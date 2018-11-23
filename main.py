import csv
import json
import os
import urllib.request
import urllib.parse
import datetime
import hmac
import hashlib

from dynamo_db import DynamoDB
from data_operation_error import DataOperationError

ENCODING = "utf-8"
FILE_NAME_LIST = "./list.json"
FILE_NAME_HOLIDAY = "./syukujitsu_kyujitsu.csv"
NUM_SUGGESTION = 3
COMMAND_ADD = "/lunch-add"
COMMAND_DEL = "/lunch-del"
COMMAND_GET_LIST = "/lunch-list"
COMMAND_GET_SUGGESTION = "/lunch-suggestion"
SLACK_WEB_HOOK_URL = os.environ["SLACK_WEB_HOOK_URL"]
SLACK_SECRET = os.environ["SLACK_SECRET"]
SLACK_USER_NAME = "お昼ごはん推薦"
SLACK_PROFILE_EMOJI = ":bento:"
SLACK_PREFIX_TEXT = "今日のお昼ご飯はこの中から選んでみては？\n"
SLACK_SUFFIX_TEXT = ""


def lambda_handler(event, context):
    """
    This function will be called at first like main().
    """
    if "detail-type" in event and event["detail-type"] == "Scheduled Event":
        # Called by Timer.
        return post_suggestion_to_webhook()
    elif "httpMethod" in event:
        if not is_request_from_slack(event):
            return {
                "statusCode": 400,
                "body": "Not allowd to receive request from you"
            }

        # Called by API gateway
        if event["httpMethod"] == "POST":
            params = convert_tuple_params_to_dict(urllib.parse.parse_qsl(event["body"]))
            print(params)
            if params["command"] == COMMAND_ADD:
                if "text" not in params:
                    return {
                        "statusCode": 200,
                        "body": "お店の名前がありませんよ！"
                    }
                return add_eating_place(params["text"])
            elif params["command"] == COMMAND_DEL:
                if "text" not in params:
                    return {
                        "statusCode": 200,
                        "body": "お店の名前がありませんよ！"
                    }
                return del_eating_place(params["text"])
            elif params["command"] == COMMAND_GET_LIST:
                return get_list_of_eating_place()
            elif params["command"] == COMMAND_GET_SUGGESTION:
                return get_suggestion()
            else:
                return {
                    "statusCode": 400,
                    "body": "Not allowed your command"
                }
        else:
            return {
                "statusCode": 405,
                "body": "Not allowed your method"
            }
    else:
        return {
            "statusCode": 400,
            "body": "Not allowed your action"
        }


def is_request_from_slack(event):
    """
    If the request was from slack, return true.
    It check signature in http header and SLACK_SECRET
    """
    try:
        timestamp = event["headers"]["X-Slack-Request-Timestamp"]
        signature = event["headers"]["X-Slack-Signature"]
        body = event["body"]
    except KeyError:
        return False

    # Check replay attack
    now = int(datetime.datetime.now().timestamp())
    if abs(now - int(timestamp)) > 60 * 5:
        return False

    basestring = "v0:" + timestamp + ":" + body
    created_signature = hmac.new(SLACK_SECRET.encode("ascii"),
                                 basestring.encode("ascii"),
                                 hashlib.sha256).hexdigest()
    created_signature = "v0=" + created_signature

    if created_signature == signature:
        return True
    return False


def convert_tuple_params_to_dict(params_urllib_result):
    """
    Convert tuple that has two items to dict
    Return: dict
    """

    params_dict = {}
    for item in params_urllib_result:
        params_dict[item[0]] = item[1]
    return params_dict


def add_eating_place(place_name):
    """
    Return: response of AWS Lambda
    """

    data_store = DynamoDB()
    if not place_name:
        return {
            "statusCode": 200,
            "body": "お店の名前がありませんよ！"
        }

    try:
        if not data_store.is_place_exists(place_name):
            data_store.add_eating_place(place_name)
            return {
                "statusCode": 200,
                "body": "%sをお店リストに追加しました！" % (place_name)
            }
        else:
            return {
                "statusCode": 200,
                "body": "%sはすでに登録されていますよ！" % (place_name)
            }
    except DataOperationError:
        return {
            "statusCode": 200,
            "body": "すみません、サーバでなんらかの問題が起きているようです"
        }


def del_eating_place(place_name):
    """
    Return: response of AWS Lambda
    """

    data_store = DynamoDB()
    if not place_name:
        return {
            "statusCode": 200,
            "body": "お店の名前がありませんよ！"
        }

    try:
        if data_store.is_place_exists(place_name):
            data_store.del_eating_place(place_name)
            return {
                "statusCode": 200,
                "body": "%sをお店リストから削除しました" % (place_name)
            }
        else:
            return {
                "statusCode": 200,
                "body": "%sはお店リストにないようです" % (place_name)
            }
    except DataOperationError:
        return {
            "statusCode": 200,
            "body": "すみません、サーバでなんらかの問題が起きているようです"
        }


def get_list_of_eating_place():
    """
    Return: response of AWS Lambda
    """

    data_store = DynamoDB()
    try:
        eating_places = data_store.get_list_of_eating_place()
        if not eating_places:
            return {
                "statusCode": 200,
                "body": "今登録されているお店はないようです"
            }

        return_text = "今登録されているお店一覧です！\n"
        for item in eating_places:
            return_text += "* " + item + "\n"

        return {
            "statusCode": 200,
            "body": return_text
        }
    except DataOperationError:
        return {
            "statusCode": 200,
            "body": "すみません、サーバでなんらかの問題が起きているようです"
        }


def get_suggestion():
    """
    Return: response of AWS Lambda
    """

    data_store = DynamoDB()
    try:
        places = data_store.get_suggestion()
        return_text = SLACK_PREFIX_TEXT
        for i, item in enumerate(places):
            return_text += str(i+1) + ". " + item + "\n"
        return {
            "statusCode": 200,
            "body": return_text
        }

    except DataOperationError:
        return {
            "statusCode": 200,
            "body": "すみません、サーバでなんらかの問題が起きているようです"
        }


def post_suggestion_to_webhook():
    """
    Return: response of AWS Lambda
    """
    if is_today_holiday():
        return {
            "statusCode": 200,
            "body": "Not posted to slack, because today is holiday."
        }

    data_store = DynamoDB()
    suggestions = data_store.get_suggestion()

    # Creating message
    message = SLACK_PREFIX_TEXT
    for i, item in enumerate(suggestions):
        index = str(i + 1)
        message += index + ". " + item + "\n"
    message += SLACK_SUFFIX_TEXT

    # Posting to slack
    to_send_data = {
        "text": message
    }
    to_send_text = "payload=" + json.dumps(to_send_data)
    request = urllib.request.Request(
        SLACK_WEB_HOOK_URL, data=to_send_text.encode(ENCODING), method="POST")
    response_body = ""
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode(ENCODING)

    return {
        "statusCode": 200,
        "body": json.dumps(response_body)
    }


def is_today_holiday():
    """
    if today is holiday, return True.
    """
    # Getting today and weekday
    jst = datetime.timezone(datetime.timedelta(hours=+9), "JST")
    now = datetime.datetime.now(jst)
    today = now.strftime("%Y-%m-%d")
    weekday = now.weekday()

    # On Suturday or Sunday
    if weekday >= 5:
        return True

    # Judgement whether today is holiday
    with open(FILE_NAME_HOLIDAY, "r", encoding=ENCODING) as file_holiday:
        reader = csv.reader(file_holiday)
        # Skip header
        next(reader)

        for row in reader:
            if row[0] == today:
                return True

    return False
