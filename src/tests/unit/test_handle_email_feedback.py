import json
from unittest import mock

from email import message_from_bytes

from handle_email_feedback import app
from email_message import build_raw_email


def _sns_event(notification):
    return {"Records": [{"Sns": {"Message": json.dumps(notification)}}]}


def _bounce(bounce_type, address="Bad@Example.com"):
    return {
        "notificationType": "Bounce",
        "bounce": {"bounceType": bounce_type, "bouncedRecipients": [{"emailAddress": address}]},
    }


def _seed_user(table, uid="abc"):
    table.put_item(Item={
        "PK": f"USER#{uid}", "SK": f"USER#{uid}", "GSI1PK": "USER", "GSI1SK": f"USER#{uid}",
        "Email address": "bad@example.com", "Character set preference": "simplified",
        "Date created": "2021-01-01T00:00:00", "User alias": "Not set",
        "User alias pinyin": "Not set", "User alias emoji": "Not set",
    })
    for list_id, status in [("111", "subscribed"), ("222", "subscribed"), ("333", "unsubscribed")]:
        table.put_item(Item={
            "PK": f"USER#{uid}", "SK": f"LIST#{list_id}#SIMPLIFIED", "GSI1PK": "USER",
            "GSI1SK": f"USER#{uid}#LIST#{list_id}#SIMPLIFIED", "List name": "HSK Level 1",
            "Status": status, "Character set": "simplified",
            "Date subscribed": "2021-01-02T00:00:00",
        })


def _statuses(table, uid="abc"):
    items = table.scan()["Items"]
    return {i["SK"]: i["Status"] for i in items if i["SK"].startswith("LIST#")}


# --- which addresses get unsubscribed -------------------------------------------

def test_permanent_bounce_is_unsubscribed_and_lowercased():
    assert app.addresses_to_unsubscribe(_bounce("Permanent")) == ["bad@example.com"]


def test_transient_bounce_is_ignored():
    assert app.addresses_to_unsubscribe(_bounce("Transient")) == []


def test_complaint_is_unsubscribed():
    notification = {
        "notificationType": "Complaint",
        "complaint": {"complainedRecipients": [{"emailAddress": "a@b.com"}]},
    }
    assert app.addresses_to_unsubscribe(notification) == ["a@b.com"]


def test_event_publishing_format_is_understood():
    notification = {"eventType": "Bounce", "bounce": _bounce("Permanent")["bounce"]}
    assert app.addresses_to_unsubscribe(notification) == ["bad@example.com"]


def test_delivery_notification_is_ignored():
    assert app.addresses_to_unsubscribe({"notificationType": "Delivery"}) == []


# --- end to end against moto DynamoDB -------------------------------------------

def test_hard_bounce_unsubscribes_every_active_list(dynamodb_table):
    _seed_user(dynamodb_table)
    with mock.patch.object(app.cognito_client, "admin_get_user", return_value={"Username": "abc"}):
        app.lambda_handler(_sns_event(_bounce("Permanent")), None)

    assert _statuses(dynamodb_table) == {
        "LIST#111#SIMPLIFIED": "unsubscribed",
        "LIST#222#SIMPLIFIED": "unsubscribed",
        "LIST#333#SIMPLIFIED": "unsubscribed",
    }


def test_soft_bounce_changes_nothing(dynamodb_table):
    _seed_user(dynamodb_table)
    with mock.patch.object(app.cognito_client, "admin_get_user") as lookup:
        app.lambda_handler(_sns_event(_bounce("Transient")), None)
    lookup.assert_not_called()
    assert _statuses(dynamodb_table)["LIST#111#SIMPLIFIED"] == "subscribed"


def test_unknown_address_is_skipped_quietly(dynamodb_table, capsys):
    not_found = app.cognito_client.exceptions.UserNotFoundException(
        {"Error": {"Code": "UserNotFoundException", "Message": "nope"}}, "AdminGetUser")
    with mock.patch.object(app.cognito_client, "admin_get_user", side_effect=not_found):
        app.lambda_handler(_sns_event(_bounce("Permanent")), None)
    # No 'Error' in the log, so no alarm email.
    assert "Error" not in capsys.readouterr().out


# --- outgoing headers -----------------------------------------------------------

def test_emails_carry_auto_reply_suppression_headers():
    raw = build_raw_email("Haohaotiantian <vocab@haohaotiantian.com>", "a@b.com",
                          "Daily vocab word", "<p>你好</p>", bulk=True)
    message = message_from_bytes(raw)
    assert message["Auto-Submitted"] == "auto-generated"
    assert message["X-Auto-Response-Suppress"] == "All"
    assert message["Precedence"] == "bulk"
    assert "你好" in message.get_payload(decode=True).decode("utf-8")


def test_sign_in_emails_are_not_marked_bulk():
    raw = build_raw_email("signin@haohaotiantian.com", "a@b.com", "Sign in", "<p>x</p>")
    message = message_from_bytes(raw)
    assert message["Precedence"] is None
    assert message["Auto-Submitted"] == "auto-generated"
