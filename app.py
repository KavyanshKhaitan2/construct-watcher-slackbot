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
import models
import asyncio
import scheduled_tasks

from construct_sdk.utils import get_page_data
from construct_sdk.get_user_data import get_user_data, get_user_data_from_slack_id

# This sample slack application uses SocketMode
# For the companion getting started setup guide,
# see: https://docs.slack.dev/tools/bolt-python/getting-started
TOKEN = os.environ.get("SLACK_BOT_TOKEN")
dotenv.load_dotenv()
DEBUG = os.environ.get("DEBUG", "false").lower() in ["true", "1", "on"]

if DEBUG:
    print("---> DEBUG is on!")

if TOKEN is None:
    TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# Initializes your app with your bot token
app = App(token=TOKEN)
# app.client.chat_postMessage(channel="#kavyansh", text="Back online!")

with open("allowed_channels.txt") as f:
    channel_list = f.read().split("\n")


def command(command):
    if DEBUG:
        return app.command("/dev-" + command)
    return app.command("/" + command)


# Listens to incoming messages that contain "hello"
@app.message("!hello")
def message_hello(message, say: Say):
    # say() sends a message to the channel where the event was triggered
    app.client.reactions_add(
        channel=message["channel"], name="+1", timestamp=message["ts"]
    )
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
        channel_list = f.read().split("\n")

    say(
        text=f"Also, these are the channels I am allowed to reply in:\n{channel_list}",
        thread_ts=message["ts"],
    )


def get_clay_time(slack_id):
    user_data = get_user_data_from_slack_id(slack_id)
    if user_data is None:
        return None
    print(user_data)
    total_time = 0
    total_redeemable_time = 0
    total_clay_time = user_data["requestedUser"]["clay"] * 60

    projects = []
    for project in user_data["projects"]:
        project_data, r = get_page_data(
            f"https://construct.hackclub.com/dashboard/projects/{project['id']}"
        )
        projects.append(project_data[2]["data"])

        project_time_spent = int(project["project"]["timeSpent"])
        total_time += project_time_spent
        if project_time_spent >= 120:
            total_redeemable_time += project_time_spent
        if project_time_spent >= 120 and project["project"]["status"] != "finalized":
            total_clay_time += project_time_spent

    return total_clay_time / 60


@command("construct-time")
def construct_time(ack, say: Say, command):
    ack()
    print("acked request for time")
    slack_user_id = command["user_id"]
    res = say(f"<@{slack_user_id}> ran:\n/construct-time {command['text']}")
    thread_ts = res["ts"]
    say = Say(
        client=say.client,
        channel=say.channel,
        thread_ts=thread_ts,
        metadata=say.metadata,
        build_metadata=say.build_metadata,
    )
    try:
        message = res
        if message["channel"] not in channel_list:
            say(
                ":no-no: Please only use this bot in #construct-watcher-stats!\n\n",
            )
            return
        say(f"{slack_user_id}")
        print(f"{command}")
        print(type(message))
        start = time.time()
        user_data = get_user_data_from_slack_id(slack_user_id)
        if user_data is None:
            say(
                "Didnt find you in my db! If you think this is a mistake, please DM @kavyansh.tech"
            )
            return
        print(user_data)
        config, _ = models.UserConfigs.get_or_create(
            user_id=user_data["requestedUser"]["id"]
        )
        text = command["text"]
        if text:
            try:
                val = int(text)
                if val <= 0:
                    say(":no-no: Why do you want your goal to be negative tho?")
                    return
            except ValueError:
                say(
                    "Sorry, but the inputted clay goal value is invalid! Please try again with a valid integer."
                )
                return
            config.goal = val
            config.save()
        say(
            f"Please wait, fetching all your projects! _(estimated time: {round((time.time()-start) * len(user_data['projects']), 2)}s)_"
        )
        start = time.time()
        projects = []
        for project in user_data["projects"]:
            project_data, r = get_page_data(
                f"https://construct.hackclub.com/dashboard/projects/{project['id']}"
            )
            projects.append(project_data[2]["data"])

        dur = round(time.time() - start, 2)
        say(
            f"_fetched *{len(projects)}* projects in *{dur}* seconds{f", an avg. of *{round(dur/len(projects), 2)}* seconds per project" if len(projects) > 0 else ""}._"
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
        total_clay_time = user_data["requestedUser"]["clay"] * 60
        for project in projects:
            max_length = 20

            project_name: str = project["project"]["name"]
            if len(project_name) > max_length + 3:
                project_name = project_name[:max_length] + "..."
            project_time_spent = int(project["project"]["timeSpent"])
            total_time += project_time_spent
            if project_time_spent >= 120:
                total_redeemable_time += project_time_spent
            hours = project_time_spent // 60
            mins = project_time_spent % 60
            if project["project"]["status"] == "finalized":
                last_col_text = "✅ Finalized"
            elif project["project"]["status"] == "printed":
                total_clay_time += project_time_spent
                last_col_text = "🖨️ Printed"
            elif project["project"]["status"] == "printing":
                total_clay_time += project_time_spent
                last_col_text = "⏱️ Printing"
            elif project["project"]["status"] == "submitted":
                total_clay_time += project_time_spent
                last_col_text = "🔃 Submitted"
            elif project["project"]["status"] == "rejected":
                last_col_text = "❌ Rejected"
            elif hours >= 2:
                total_clay_time += project_time_spent
                last_col_text = "👍 Redeemable"
            else:
                last_col_text = "🚧 Building"
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
                                "elements": [
                                    {"type": "text", "text": f"{hours}h {mins}m"}
                                ],
                            }
                        ],
                    },
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [{"type": "text", "text": last_col_text}],
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

        hours = int(total_clay_time // 60)
        mins = round(total_clay_time % 60)
        total_clay_time_formatted = f"{hours}h {mins}m"

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
                                    "text": "Clay time",
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
                                    "text": total_clay_time_formatted,
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
        goal = config.goal * 60
        deadline = datetime.date(2026, 3, 7)
        time_left = deadline - datetime.date.today()
        days_left = time_left.days

        total_time_for_calc = (goal - total_time) / days_left
        total_clay_time_for_calc = (goal - total_clay_time) / days_left

        if total_time_for_calc > 0:
            hours = int(total_time_for_calc // 60)
            mins = int(total_time_for_calc % 60)
            daily_time_formatted = f"{hours}h {mins}m"
        else:
            daily_time_formatted = "0m (goal reached :yay:)"

        if total_clay_time_for_calc > 0:
            hours = int(total_clay_time_for_calc // 60)
            mins = int(total_clay_time_for_calc % 60)
            daily_clay_time_formatted = f"{hours}h {mins}m"
        else:
            daily_clay_time_formatted = "0m (goal reached :yay:)"

        blocks = [
            {"type": "table", "rows": table_rows},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Deadline in *{days_left}* days ({deadline})\nGOAL: {goal/60} hours\nDo *{daily_time_formatted}* every day to reach GOAL.\nDo *{daily_clay_time_formatted}* every day to reach GOAL. *(calculated using clay time)*",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Open Printer Shop :3d-printer-icon: ",
                            "emoji": True,
                        },
                        "value": "show",
                        "action_id": "printer-shop",
                    }
                ],
            },
        ]
        say(blocks=blocks, text="Your construct report has been generated.")
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


@app.action("printer-shop")
def printer_shop(ack, action, say, respond):
    ack()
    respond(":discord_loader:")
    print(action)
    return
    get_clay_time()
    respond(
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "This is a header block",
                    "emoji": True,
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
                                            "text": "Printer/addon",
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
                                            "text": "Cost",
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
                                            "text": "Time reqd.",
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
                                    "elements": [{"type": "text", "text": "Datum 1"}],
                                }
                            ],
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [{"type": "text", "text": "Datum 2"}],
                                }
                            ],
                        },
                        {
                            "type": "rich_text",
                            "elements": [
                                {
                                    "type": "rich_text_section",
                                    "elements": [{"type": "text", "text": "Datum 2"}],
                                }
                            ],
                        },
                    ],
                ],
            },
            {"type": "divider"},
        ]
    )


@command("construct-user-info")
def construct_user_info(ack, say: Say, command):
    # Acknowledge command request
    ack()
    print("acked request for user-info.")
    slack_id = command["text"].split("|")[0].removeprefix("<@")
    if slack_id:
        display_name = command["text"].split("|")[1].removesuffix(">")
    else:
        slack_id = command["user_id"]
        display_name = command["user_name"]

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
            f"*Balance:* *{round(found['clay'], 2)}* clay, *{found['brick']}* bricks.\n"
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
    scheduled_tasks.start_scheduler()
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
