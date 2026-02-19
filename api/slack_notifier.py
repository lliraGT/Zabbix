# api/slack_notifier.py
# Slack notification module with environment variables
import sys
import os
# Agregar directorio padre al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from datetime import datetime
from config import Config

# Slack Webhook URL from environment
SLACK_WEBHOOK_URL = Config.SLACK_WEBHOOK_URL

def get_severity_color(severity):
    """Return color code based on severity"""
    colors = {
        'Critical': '#FF0000',  # Red
        'Medium': '#FFA500',    # Orange
        'Minor': '#FFFF00',     # Yellow
        'Clear': '#00FF00'      # Green
    }
    return colors.get(severity, '#808080')  # Default gray

def get_severity_emoji(severity):
    """Return emoji based on severity"""
    emojis = {
        'Critical': '🔴',
        'Medium': '🟠',
        'Minor': '🟡',
        'Clear': '🟢'
    }
    return emojis.get(severity, '⚪')

def send_slack_notification(event_id, hostname, visible_name, problem_name, severity, timestamp, group_name):
    """
    Send formatted notification to Slack using Block Kit

    Parameters:
    - event_id: Zabbix event ID
    - hostname: Technical hostname
    - visible_name: Human-readable host name
    - problem_name: Description of the problem
    - severity: Severity level (Critical, Medium, Minor, Clear)
    - timestamp: When the problem occurred
    - group_name: Host group name
    """

    try:
        color = get_severity_color(severity)
        emoji = get_severity_emoji(severity)

        # Format timestamp
        if isinstance(timestamp, str):
            timestamp_str = timestamp
        else:
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Prepare the message payload with Block Kit
        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} Zabbix Alert - {severity}",
                                "emoji": True
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Problem:\n{problem_name}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"Severity:\n{severity}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Host:\n{hostname}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"Visible Name:\n{visible_name}"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Group:\n{group_name}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"Timestamp:\n{timestamp_str}"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Event ID: {event_id} | Zabbix Monitor"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # Send POST request to Slack webhook
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            print(f"[{datetime.now()}] Slack notification sent successfully for event {event_id}")
            return True
        else:
            print(f"[{datetime.now()}] Failed to send Slack notification. Status: {response.status_code}, Response: {response.text}")
            return False

    except Exception as e:
        print(f"[{datetime.now()}] Error sending Slack notification: {str(e)}")
        return False

def send_simple_slack_message(message):
    """
    Send a simple text message to Slack

    Parameters:
    - message: Text message to send
    """
    try:
        payload = {
            "text": message
        }

        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        return response.status_code == 200

    except Exception as e:
        print(f"[{datetime.now()}] Error sending simple Slack message: {str(e)}")
        return False

# Test function
if __name__ == "__main__":
    # Test with sample data
    send_slack_notification(
        event_id="12345",
        hostname="test-server-01",
        visible_name="Test Server 01",
        problem_name="High CPU usage detected",
        severity="Critical",
        timestamp=datetime.now(),
        group_name="Production Servers"
    )
