import os
import random
import datetime
import json
import traceback
import dotenv
from slack_bolt import App
from slack_bolt.context.say.say import Say
from slack_bolt.adapter.socket_mode import SocketModeHandler

from construct_sdk.get_dashboard_projects import get_projects
from construct_sdk.get_user_data import get_user_data

# This sample slack application uses SocketMode
# For the companion getting started setup guide,
# see: https://docs.slack.dev/tools/bolt-python/getting-started

token = os.environ.get("SLACK_BOT_TOKEN")
if token is None:
    dotenv.load_dotenv()
    token = os.environ.get("SLACK_BOT_TOKEN")

# Initializes your app with your bot token
app = App(token=token)
# app.client.chat_postMessage(channel="#kavyansh", text="Back online!")

with open("allowed_channels.txt") as f:
    channel_list = f.readlines()


# Listens to incoming messages that contain "hello"
@app.message("!hello")
def message_hello(message, say: Say):
    # say() sends a message to the channel where the event was triggered
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click Me"},
                    "action_id": "button_click",
                },
            }
        ],
        text=f"Hey there <@{message['user']}>!",
        thread_ts=message["ts"],
    )
    say("Oh, and btw, heres the message i received:", thread_ts=message["ts"])
    say(text=str(message), thread_ts=message["ts"])

    global channel_list
    with open("allowed_channels.txt") as f:
        channel_list = f.readlines()

    say(
        text=f"Also, these are the channels I am allowed to reply in:\n{channel_list}",
        thread_ts=message["ts"],
    )


# @app.message("goodbye")
# def message_goodbye(say: Say):
#     responses = ["Adios", "Au revoir", "Farewell"]
#     parting = random.choice(responses)
#     say(f"{parting}!")


# @app.action("button_click")
# def action_button_click(body, ack, say: Say):
#     # Acknowledge the action
#     ack()
#     say(f"<@{body['user']['id']}> clicked the button")


GOAL = 42  # hours


@app.message("!time")
def time_to_do(message, say: Say):
    print(f"[INFO] Received command: {message}")
    print(type(message))
    if message["user"] != "U0A7776A2MT":
        say("You are not allowed to do this!", thread_ts=message["ts"])
        print("Incorrect user!")
        return
    say("Please wait...", thread_ts=message["ts"])
    projects = get_projects()
    total_time = 0
    total_total_time = 0
    message_to_send = ""
    say("Done! Here is what I found:", thread_ts=message["ts"])
    for project in projects:
        minutes = project["minutes"]
        formatted_time = f"{int(minutes/60)}h {int(minutes%60)}m"
        message_to_send += f"- *{project['name']}*: {formatted_time}" + (
            " :tw_timer_clock: _cant redeem time below 2h_\n" if minutes < 120 else "\n"
        )
        total_total_time += minutes
        if minutes < 120:
            print("cant calculate", project)
        if minutes > 120:
            total_time += minutes
    say(message_to_send, thread_ts=message["ts"])
    formatted_time = f"{int(total_time/60)}h {int(total_time%60)}m"
    formatted_total_time = f"{int(total_total_time/60)}h {int(total_total_time%60)}m"
    say(f"*Total time*: {formatted_total_time}", thread_ts=message["ts"])
    say(f"*Total redeemable time*: {formatted_time}", thread_ts=message["ts"])

    deadline = datetime.date(2026, 3, 7)
    time_left = deadline - datetime.date.today()
    days_left = time_left.days
    say(
        f"{days_left} days left to {deadline} // Goal: {GOAL} hours",
        thread_ts=message["ts"],
    )
    redeemable_daily_time = (GOAL - total_time / 60) / days_left * 60
    total_daily_time = (GOAL - total_total_time / 60) / days_left * 60
    formatted_redeemable_daily_time = (
        f"{int(redeemable_daily_time/60)}h {int(redeemable_daily_time%60)}m"
    )
    formatted_total_daily_time = (
        f"{int(total_daily_time/60)}h {int(total_daily_time%60)}m"
    )

    say(
        f"Do {formatted_redeemable_daily_time} hours daily to reach goal. (only redeemable time)",
        thread_ts=message["ts"],
    )
    say(
        f"Do {formatted_total_daily_time} hours daily to reach goal. (total time)",
        thread_ts=message["ts"],
    )


@app.message("!construct_user")
def construct_user(message, say: Say):
    try:
        if message["channel"] not in channel_list:
            say(
                ":no-no: Please only use this bot in #construct-watcher-stats!\n\n",
                thread_ts=message["ts"],
            )
            return
        text: str = message["text"]
        text = text.removeprefix("!construct_user").strip()
        if not text:
            say(
                "Find anyone on construct using their slack mention.\n\nUsage:\n> !construct_user @mention",
                thread_ts=message["ts"],
            )
            return
        slack_id = text.removeprefix("<@").removesuffix(">")
        say(slack_id, thread_ts=message["ts"])
        with open("all_users_data.json") as f:
            data = json.load(f)

        found = None
        for row in data:
            if row["slackId"] == slack_id:
                found = row
        if not found:
            say(
                "Couldnt find anyone :sad-pf:\n\n_I can help you find anyone's construct account via their slack mention!_",
                thread_ts=message["ts"],
            )
            return
        data = get_user_data(found["id"])
        found = data['requestedUser']
        total_time = 0
        devlog_count = 0
        for devlog in data["devlogs"]:
            total_time += devlog["timeSpent"]
            devlog_count += 1

        formatted_time = f"{int(total_time/60)}h {int(total_time%60)}m"

        embed_text = (
            f"*{found['name']}*\n"
            f"*Slack ID:* {found['slackId']}\n"
            f"<https://construct.hackclub.com/dashboard/users/{found['id']}|*Construct User ID*: {found['id']}>\n"
            # f"Is printer? {found['isPrinter']}\n"
            # f"T1 reviewer? {found['hasT1Review']}\n"
            # f"T2 reviewer? {found['hasT2Review']}\n"
            # f"Admin? {found['hasAdmin']}\n"
            f"*Market score:* {found['shopScore']}\n"
            f"*Total time logged:* {formatted_time}\n"
            f"*Number of devlogs:* {devlog_count}\n"
        )

        say(
            embed_text,
            [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": embed_text},
                    "accessory": {
                        "type": "image",
                        "image_url": found["profilePicture"],
                        "alt_text": "A Construct user's profile picture",
                    },
                },
    {
                "type": "table",
                "rows": [
                    [
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Printer?",
                                            "style": {
                                                "bold": True
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Reviewer?",
                                            "style": {
                                                "bold": True
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Admin?",
                                            "style": {
                                                "bold": True
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ],
                    [
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Yes" if found['isPrinter'] == 'true' else "No"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": (("T1 Review" if found['hasT1Review'] == 'true' else '') + ("\nT2 Review" if found['hasT2Review'] == 'true' else '')) or "No"
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [
                                        {
                                            "type": "text",
                                            "text": "Yes" if found['hasAdmin'] == 'true' else "No"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                ]
            }
            ],
            thread_ts=message["ts"],
        )

        print(message)
    except Exception as _:
        traceback_text = traceback.format_exc()
        say("_Construct Watcher tried finding you in the shelves, but tripped._", thread_ts=message["ts"])
        say("Uh oh! You landed on an error.", thread_ts=message["ts"])
        say(f"{traceback_text}", thread_ts=message["ts"])
        say(f"cc <@U0A7776A2MT>. <@{message['user']}> found a bug in me! :bug:", thread_ts=message["ts"])
        


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
