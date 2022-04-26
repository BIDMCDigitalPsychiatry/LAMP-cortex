""" Module with functions for pushing slack / email notifications """
import os
import json
import logging
from pprint import pformat
import requests

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def _get_push_keys(push_api_key, push_gateway):
    """ Get the push api keys. If None, they should be retrieved from
        the corresponding environment variable.
    """
    if push_api_key is None:
        if not 'PUSH_API_KEY' in os.environ:
            raise Exception("You must configure `PUSH_API_KEY` or pass "
                          + "it as a parameter to send notifications")
        push_api_key = os.getenv('PUSH_API_KEY')
    if push_gateway is None:
        if not 'PUSH_GATEWAY' in os.environ:
            raise Exception("You must configure `PUSH_GATEWAY` or pass "
                          + "it as a parameter to send notifications")
        push_gateway = os.getenv('PUSH_GATEWAY')
    return push_api_key, push_gateway

def push_email(email, content, push_api_key=None, push_gateway=None,
               support_email=None, debug_mode=0):
    """ Helper function to send custom push notifications to emails to addresses.

        Args:
            email (str): the email to push the message to
                ex: "someemail@gmail.com"
            content (str): the content of the message.
                Subject and body should be split by a new line.
                ex: "email subject\nemail text"
            push_api_key (str): the API key, will be pulled from the environment variable if None.
            push_gateway (str): the gateway, will be pulled from the environment variable if None.
            support_email (str): the email to send from. This email will also be cc'd.
            debug_mode (boolean, default: False): if set, emails / notifications
                will be logged and not sent.
    """
    push_api_key, push_gateway = _get_push_keys(push_api_key, push_gateway)
    if support_email is None:
        if not 'SUPPORT_EMAIL' in os.environ:
            raise Exception("You must configure `SUPPORT_EMAIL` or pass "
                          + "it as a parameter to send notifications")
        support_email = os.getenv('SUPPORT_EMAIL')
    push_body = {
        'api_key': push_api_key,
        'device_token': 'mailto:' + email,
        'payload': {
            'from': support_email,
            'cc': support_email,
            'subject': content.split('\n', 1)[0],
            'body': content.split('\n', 1)[1]
        }
    }
    if debug_mode:
        log.debug(pformat(push_body))
    else:
        response = requests.post(f"https://{push_gateway}/push", headers={
            'Content-Type': 'application/json'
        }, json=push_body).json()
        log.debug(pformat(response))
    log.info("Sent email to %s with content %s.", email, content)

def send_push_notification(device, content, push_api_key=None, push_gateway=None,
                           expiry=86400000, debug_mode=0):
    """ Helper function to send custom push notifications to devices.

        Args:
            device (str): the device to push the message to
                "{'apns' if 'iOS' else 'gcm'}:{device['device_token']}"
                    The device information can be found using LAMP.analytics. Please see
                    the docs for more information.
            content (str): the content of the message.
                for email: subject and body should be split by a new line.
                    ex: "email subject\nemail text"
            push_api_key (str): the API key, will be pulled from the environment variable if None.
            push_gateway (str): the gateway, will be pulled from the environment variable if None.
            expiry (int, unit: ms, default: 8640000, or ms in a day): the amount
                of time before the notification expires (for device)
            debug_mode (boolean, default: False): if set, emails / notifications
                will be logged and not sent.
    """
    push_api_key, push_gateway = _get_push_keys(push_api_key, push_gateway)
    push_body = {
        'api_key': push_api_key,
        'device_token': device,
        'payload': {
            "aps": {"content-available": 1} if content is None else {
                "alert": content, # 'Hello World!'
                "badge": 0,
                "sound": "default",
                "mutable-content": 1,
                "content-available": 1
            },
            "notificationId": content,
            "expiry": expiry,
            #"page": None, # 'https://dashboard.lamp.digital/'
            "actions": []
        }
    }
    if debug_mode:
        log.debug(pformat(push_body))
    else:
        requests.post(f"https://{push_gateway}/push", headers={
            'Content-Type': 'application/json'
        }, json=push_body).json()
    log.info("Sent push notification to %s with content %s.", device, content)

def slack(message, slack_webhook=None):
    """ A function for sending slack messages.

        Args:
            message (str): the text of the slack message
            slack_webhook (str, default: None): the slack webhook url. If set to None,
                will try to use the environment variable 'LAMP_SLACK_WEBHOOK'
                to send slack messages.
    """
    if slack_webhook is None:
        if not 'LAMP_SLACK_WEBHOOK' in os.environ:
            raise Exception("You must configure `LAMP_SLACK_WEBHOOK` or pass "
                          + "it as a parameter to send slack messages")
        slack_webhook = os.getenv('LAMP_SLACK_WEBHOOK')
    data = {'text': message}
    requests.post(slack_webhook,
                  data=json.dumps(data),
                  headers={'Content-Type': 'application/json'})
