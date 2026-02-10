import os
import random
import datetime
import json
import traceback
import dotenv
from slack_bolt import App
from slack_bolt.context.say.say import Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
import time

from construct_sdk.utils import get_page_data
from construct_sdk.get_user_data import get_user_data, get_user_data_from_slack_id

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
    channel_list = f.read().split('\n')


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


@app.command("/construct-time")
def construct_time(ack, say: Say, command):
    ack()
    print("acked request for time")
    slack_user_id = command["user_id"]
    res = say(f"<@{slack_user_id}> ran:\n/construct_time")
    thread_ts = res["ts"]
    say = Say(
        client=say.client,
        channel=say.channel,
        thread_ts=thread_ts,
        metadata=say.metadata,
        build_metadata=say.build_metadata,
    )
    try:
        say(f"{slack_user_id}")
        print(f"{command}")
        message = res
        print(f"[INFO] Received command: {message}")
        print(type(message))
        user_data = get_user_data_from_slack_id(slack_user_id)
        say(f"Please wait, fetching all your projects! _(estimated time: {1.5 * len(user_data['projects'])}s)_")
        start = time.time()
        projects = []
        for project in user_data["projects"]:
            project_data, r = get_page_data(
                f"https://construct.hackclub.com/dashboard/projects/{project['id']}"
            )
            projects.append(project_data[2]["data"])

        dur = round(time.time() - start, 2)
        say(
            f"_fetched *{len(projects)}* projects in *{dur}* seconds, an avg. of *{round(dur/len(projects), 2)}* seconds per project._"
        )

        table_rows = [
            [  # Top header ("Project name", "Time spent", " ")
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "Project name",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "Time spent",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": " ",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
            ],
        ]
        total_time = 0
        total_redeemable_time = 0
        for project in projects:
            project_name = project["project"]["name"]
            project_time_spent = int(project["project"]["timeSpent"])
            total_time += project_time_spent
            if project_time_spent > 120:
                total_redeemable_time += project_time_spent
            hours = project_time_spent // 60
            mins = project_time_spent % 60
            table_rows.append(
                [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": project_name}],
                            }
                        ],
                    },
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": f"{hours}h {mins}m"}],
                            }
                        ],
                    },
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {"type": "text", "text": "⏲️" if hours < 2 else " "}
                                ],
                            }
                        ],
                    },
                ],
            )
        
        hours = total_time // 60
        mins = total_time % 60
        total_time_formatted = f"{hours}h {mins}m"
        
        hours = total_redeemable_time // 60
        mins = total_redeemable_time % 60
        daily_reedemable_time_formatted = f"{hours}h {mins}m"
        
        table_rows += [
            [
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "Total",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": total_time_formatted,
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": " ",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
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
                                    "text": "Redeemable",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": daily_reedemable_time_formatted,
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_section",
                            "elements": [
                                {
                                    "type": "text",
                                    "text": "⏲️",
                                    "style": {"bold": True},
                                }
                            ],
                        }
                    ],
                },
            ],
        ]
        GOAL = 42 * 60
        deadline = datetime.date(2026, 3, 7)
        time_left = deadline - datetime.date.today()
        days_left = time_left.days
        
        total_time = (GOAL - total_time) / days_left
        total_redeemable_time = (GOAL - total_redeemable_time) / days_left
        
        hours = int(total_time // 60)
        mins = int(total_time % 60)
        daily_time_formatted = f"{hours}h {mins}m"
        
        hours = int(total_redeemable_time // 60)
        mins = int(total_redeemable_time % 60)
        daily_reedemable_time_formatted = f"{hours}h {mins}m"
        
        blocks = [{"type": "table", "rows": table_rows}, {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"Deadline in *{days_left}* days ({deadline})\nGOAL: {GOAL/60} hours\nDo *{daily_time_formatted}* every day to reach GOAL.\nDo *{daily_reedemable_time_formatted}* every day to reach GOAL. *(calculated using redeemable time)*",
			}
		}]
        say(blocks=blocks)
    except Exception as _:
        traceback_text = traceback.format_exc()
        say(
            "_Construct Watcher tried finding you in the shelves, but tripped._",
        )
        say("Uh oh! You landed on an error.")
        say(f"{traceback_text}")
        print(traceback_text)
        say(
            f"cc <@U0A7776A2MT>. <@{command['user_id']}> found a bug in me! :bug:",
        )


@app.command("/construct-user-info")
def construct_user_info(ack, say: Say, command):
    # Acknowledge command request
    ack()
    print("acked request for user-info.")
    slack_id = command["text"].split("|")[0].removeprefix("<@")
    display_name = command["text"].split("|")[1].removesuffix(">")
    res = say(f"<@{command['user_id']}> ran:\n/construct-user-info {display_name}")
    thread_ts = res["ts"]
    say = Say(
        client=say.client,
        channel=say.channel,
        thread_ts=thread_ts,
        metadata=say.metadata,
        build_metadata=say.build_metadata,
    )
    print(command["text"])
    message = res

    try:
        if message["channel"] not in channel_list:
            say(
                ":no-no: Please only use this bot in #construct-watcher-stats!\n\n",
            )
            return
        slack_id = slack_id
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
            )
            return
        data = get_user_data(found["id"])
        found = data["requestedUser"]
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
                                                "style": {"bold": True},
                                            }
                                        ],
                                    }
                                ],
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
                                                "style": {"bold": True},
                                            }
                                        ],
                                    }
                                ],
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
                                                "style": {"bold": True},
                                            }
                                        ],
                                    }
                                ],
                            },
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
                                                "text": (
                                                    "Yes"
                                                    if found["isPrinter"] == "true"
                                                    else "No"
                                                ),
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "type": "rich_text",
                                "elements": [
                                    {
                                        "type": "rich_text_section",
                                        "elements": [
                                            {
                                                "type": "text",
                                                "text": (
                                                    (
                                                        "T1 Review"
                                                        if found["hasT1Review"]
                                                        == "true"
                                                        else ""
                                                    )
                                                    + (
                                                        "\nT2 Review"
                                                        if found["hasT2Review"]
                                                        == "true"
                                                        else ""
                                                    )
                                                )
                                                or "No",
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "type": "rich_text",
                                "elements": [
                                    {
                                        "type": "rich_text_section",
                                        "elements": [
                                            {
                                                "type": "text",
                                                "text": (
                                                    "Yes"
                                                    if found["hasAdmin"] == "true"
                                                    else "No"
                                                ),
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    ],
                },
            ],
        )

        print(message)
    except Exception as _:
        traceback_text = traceback.format_exc()
        say(
            "_Construct Watcher tried finding you in the shelves, but tripped._",
        )
        say("Uh oh! You landed on an error.")
        say(f"{traceback_text}")
        say(
            f"cc <@U0A7776A2MT>. <@{command['user_id']}> found a bug in me! :bug:",
        )


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
