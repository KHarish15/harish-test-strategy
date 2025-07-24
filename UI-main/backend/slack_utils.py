import os
import requests

def send_slack_message(text):
    """
    Send a message to Slack using the webhook URL from environment variables.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL not set in environment variables.")
    payload = {"text": text}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to send Slack message: {response.status_code} {response.text}")
    return response.text 