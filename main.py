import csv
import json
import os
import random
import urllib.request
import datetime

ENCODING = "utf-8"
FILE_NAME_LIST = "./list.json"
FILE_NAME_HOLIDAY = "./syukujitsu_kyujitsu.csv"
NUM_SUGGESTION = 3
SLACK_WEB_HOOK_URL = os.environ["WEB_HOOK_URL"]
SLACK_USER_NAME = "お昼ごはん推薦"
SLACK_PROFILE_EMOJI = ":bento:"
SLACK_PREFIX_TEXT = "今日のお昼ご飯はこの中から選んでみては？\n"
SLACK_SUFFIX_TEXT = ""


def lambda_handler(event, context):
    """
    This function will be called at first like main().
    """
    if is_today_holiday():
        return {
            "statusCode": 204,
            "body": "Not posted to slack, because today is holiday."
        }

    response = suggest_lunch()

    return {
        "statusCode": 200,
        "body": json.dumps(response)
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


def suggest_lunch():
    """
    Choice lunch store randomly.
    Then, Post slack it.
    """
    # Setting stdin/out/err encoding
    # Not use in aws lambda
    # sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding=ENCODING)
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=ENCODING)
    # sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=ENCODING)

    # Loading list from file
    with open(FILE_NAME_LIST, "r", encoding=ENCODING) as list_file:
        file_text = list_file.read()
        store_list = json.loads(file_text)

    # Picking items in the list randomly
    suggestions = []
    for i in range(NUM_SUGGESTION):
        index = random.randrange(len(store_list))
        suggestions.append(store_list[index])
        del store_list[index]

    # Creating message
    message = SLACK_PREFIX_TEXT
    for i, item in enumerate(suggestions):
        index = str(i + 1)
        message += index + ". " + item + "\n"
    message += SLACK_SUFFIX_TEXT

    # Posting to slack
    to_send_data = {
        "username": SLACK_USER_NAME,
        "icon_emoji": SLACK_PROFILE_EMOJI,
        "text": message,
    }
    to_send_text = "payload=" + json.dumps(to_send_data)
    request = urllib.request.Request(
        SLACK_WEB_HOOK_URL, data=to_send_text.encode(ENCODING), method="POST")
    response_body = ""
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode(ENCODING)

    return response_body
