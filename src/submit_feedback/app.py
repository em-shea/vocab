"""POST /feedback {"message": "..."}: a signed-in user sends feedback.

The message is emailed to nihao@haohaotiantian.com with Reply-To set to the
user's address, so Emily can answer by replying. Reads the user's own item to
get their email and name; writes nothing to DynamoDB.
"""
import os
import json
import html

import boto3

import api_response
import user_service
from email_message import send_html_email

MAX_LENGTH = 2000
INBOX = 'nihao@haohaotiantian.com'
SENDER = 'Haohaotiantian feedback <vocab@haohaotiantian.com>'

ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])


def lambda_handler(event, context):
    cognito_id = event['requestContext']['authorizer']['claims']['sub']
    try:
        body = json.loads(event.get('body') or '{}')
    except ValueError:
        return api_response.response(400, "Body must be JSON.")
    message = body.get('message')
    if not isinstance(message, str) or not message.strip():
        return api_response.response(400, "'message' is required.")
    message = message.strip()
    if len(message) > MAX_LENGTH:
        return api_response.response(400, f"'message' must be {MAX_LENGTH} characters or fewer.")
    page = body.get('page') if isinstance(body.get('page'), str) else ''

    try:
        user = user_service.get_single_user(cognito_id)
    except Exception as e:
        print(f"Error: failed to look up user {cognito_id}")
        print(e)
        return api_response.response(404, "User not found.")

    try:
        send_html_email(ses_client, SENDER, INBOX, subject(user), email_html(user, message, page[:200]),
                        reply_to=user.email_address)
    except Exception as e:
        print(f"Error: failed to send feedback from {cognito_id}")
        print(e)
        return api_response.response(502, "Failed to send feedback.")
    return api_response.response(200, "Feedback sent.")


def _name(user):
    alias = getattr(user, 'user_alias', None)
    return alias if alias not in (None, '', 'Not set') else None


def subject(user):
    name = _name(user)
    return f"Feedback from {name} ({user.email_address})" if name else f"Feedback from {user.email_address}"


def email_html(user, message, page):
    lines = [f'<p style="white-space: pre-wrap; font-family: Arial, sans-serif; font-size: 15px;">{html.escape(message)}</p>',
             '<hr>',
             f'<p style="font-family: Arial, sans-serif; font-size: 13px; color: #5F6276;">From {html.escape(user.email_address)}'
             + (f' ({html.escape(_name(user))})' if _name(user) else '') + '</p>']
    if page:
        lines.append(f'<p style="font-family: Arial, sans-serif; font-size: 13px; color: #5F6276;">Sent from {html.escape(page)}</p>')
    lines.append('<p style="font-family: Arial, sans-serif; font-size: 13px; color: #5F6276;">Reply to this email to answer them.</p>')
    return ''.join(lines)
