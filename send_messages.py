import os
import random

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    raise Exception("Error: SLACK_BOT_TOKEN not found.")

client = WebClient(SLACK_BOT_TOKEN)

def send_slack_message(channel, text):
    try:
        # Call the chat.postMessage method using the WebClient
        response = client.chat_postMessage(
            channel=channel,
            text=text
        )
        print(f"Message sent: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

if __name__ == "__main__":
    # Example usage
    message_text = "Hello world from my Python bot! :tada-dino:"
    send_slack_message("#kavyansh-bot-playground", message_text)
