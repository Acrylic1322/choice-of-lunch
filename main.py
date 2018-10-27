import csv
import io
import json
import os
import random
import sys
import urllib.request
import datetime

ENCODING = "utf-8"
LIST_FILE_NAME = "./list.json"
NUM_SUGGESTION = 3
FILE_HOLIDAY="syukujitsu_kyujitsu.csv"
WEB_HOOK_URL = os.environ["WEB_HOOK_URL"]
SLACK_USER_NAME = "お昼ごはん推薦"
SLACK_PROFILE_EMOJI = ":bento:"
SLACK_PREFIX_TEXT = "今日のお昼ご飯はこの中から選んでみては？\n"
SLACK_SUFFIX_TEXT = ""

def lambda_handler(event, context):
    if isHoliday() is False:
        response = suggest_lunch()

        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }

    return {
        "statusCode": 204,
        "body": "Not posted to slack, because today is holiday."
    }

def isHoliday():
    # Getting today and weekday
    JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
    now = datetime.datetime.now(JST)
    today = now.strftime("%Y-%m-%d")
    weekday = now.weekday()

    # On Suturday or Sunday
    if weekday >= 5:
      return True

    # Judgement whether today is holiday
    with open(FILE_HOLIDAY, "r", encoding=ENCODING) as file_holiday:
        reader = csv.reader(file_holiday)
        header = next(reader)

        for row in reader:
            if row[0] == today:
                return True

    return False

def suggest_lunch():
    # Setting stdin/out/err encoding
    # Not use in aws lambda
    # sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding=ENCODING)
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=ENCODING)
    # sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=ENCODING)

    # Loading list from file
    list = []
    with open(LIST_FILE_NAME, "r", encoding=ENCODING) as list_file:
        file_text = list_file.read()
        list = json.loads(file_text)

    # Picking items in the list randomly
    suggestions = []
    for i in range(NUM_SUGGESTION):
        index = random.randrange(len(list))
        suggestions.append(list[index])
        del list[index]

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
    request = urllib.request.Request(WEB_HOOK_URL, data=to_send_text.encode(ENCODING), method="POST")
    response_body = ""
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode(ENCODING)

    return response_body
