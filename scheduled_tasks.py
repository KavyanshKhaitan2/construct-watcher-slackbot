from construct_sdk.utils import get_page_data
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
                        "text": f"*Project:*\n{devlog.project_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time spent:*\n{devlog.devlog_time_spent}"
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
        schedule.run_pending()
        time.sleep(0.5)

def start_scheduler():
    threading.Thread(target=_start_scheduler).start()


if __name__ == "__main__":
    start_scheduler()