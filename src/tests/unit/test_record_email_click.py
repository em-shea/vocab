import os
import sys
import json
from unittest import mock

os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('CLICKS_TABLE', 'VocabEmailClicks-test')


def load():
    import importlib.util
    path = os.path.join(os.path.dirname(__file__), '../../record_email_click/app.py')
    spec = importlib.util.spec_from_file_location('record_email_click_app', path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch('boto3.resource'):
        spec.loader.exec_module(module)
    return module


CLICK = {
    'eventType': 'Click',
    'mail': {'messageId': 'abc123', 'destination': ['Reader@Example.com'],
             'tags': {'campaign': ['new-features']}},
    'click': {'timestamp': '2026-11-27T13:05:00.000Z', 'link': 'https://staging.haohaotiantian.com/profile?from=email',
              'linkTags': {'link': ['announcement']}},
}


def test_click_item_reads_recipient_campaign_and_link():
    app = load()
    assert app.click_item(CLICK) == {
        'Email': 'reader@example.com',
        'ClickedAt': '2026-11-27T13:05:00.000Z#abc123',
        'Campaign': 'new-features',
        'Link': 'announcement',
        'Url': 'https://staging.haohaotiantian.com/profile?from=email',
    }


def test_other_events_are_ignored():
    app = load()
    assert app.click_item({**CLICK, 'eventType': 'Open'}) is None


def test_handler_only_puts_items():
    app = load()
    app.table = mock.Mock()
    app.lambda_handler({'Records': [{'Sns': {'Message': json.dumps(CLICK)}}]}, None)
    app.table.put_item.assert_called_once()
    assert app.table.method_calls == [mock.call.put_item(Item=app.click_item(CLICK))]
