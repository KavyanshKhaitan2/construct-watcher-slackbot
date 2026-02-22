from construct_sdk.utils import get_page_data
from construct_sdk.get_user_data import get_user_data
from send_messages import send_slack_message
from models import Devlogs
import dotenv
import os
import schedule
import threading
import time
dotenv.load_dotenv()

@schedule.every(5).seconds.do
def reload_devlogs():
    data, r = get_page_data('https://construct.hackclub.com/dashboard/explore')
    data['devlogs'] = reversed(data['devlogs'])
    for entry in data['devlogs']:
        devlog = Devlogs.get_or_none(devlog_id=entry['devlog']['id'])
        if devlog is not None:
            continue
        devlog = Devlogs.create(
            user_id=entry['user']['id'],
            user_name=entry['user']['name'],
            
            project_id=entry['project']['id'],
            project_name=entry['project']['name'],
            
            devlog_id=entry['devlog']['id'],
            devlog_description=entry['devlog']['description'],
            devlog_image="https://construct.hackclub-assets.com/"+entry['devlog']['image'],
            devlog_time_spent=entry['devlog']['timeSpent'],
            devlog_created=entry['devlog']['createdAt']
        )
        user_data = get_user_data(devlog.user_id)
        slack_id = user_data['requestedUser']['slackId']
        
        
        send_slack_message(os.environ.get('DEFAULT_CHANNEL'), text=None, blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"New devlog has been created in *<https://construct.hackclub.com/dashboard/projects/{devlog.project_id}|{devlog.project_name}>*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*User:*\n<https://construct.hackclub.com/dashboard/users/{devlog.user_id}|{devlog.user_name}>\n<@{slack_id}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Project:*\n<https://construct.hackclub.com/dashboard/projects/{devlog.project_id}|{devlog.project_name}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time spent:*\n{devlog.devlog_time_spent} minutes"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created:*\n{devlog.devlog_created}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description*:\n{devlog.devlog_description}"
                },
                "accessory": {
                    "type": "image",
                    "image_url": f"{devlog.devlog_image}",
                    "alt_text": "Devlog image."
                }
            }
        ])
        
def _start_scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception:
            ...
        
        time.sleep(0.5)

def start_scheduler():
    try:
        threading.Thread(target=_start_scheduler).start()
        # send_slack_message(os.environ.get('DEFAULT_CHANNEL'), "yo, im up again.")
    except Exception:
        ...


if __name__ == "__main__":
    start_scheduler()