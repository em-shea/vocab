import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'BACKUPS_BUCKET_NAME': 'mock-bucket', 'TABLE_NAME': 'mock-table'}):
  from backup_dynamodb_s3.app import lambda_handler

def mocked_dynamodb_scan():
  all_contacts = [
      {
        "ListId": "1-simplified",
        "SubscriberEmail": "test@test.com",
        "CharacterSet": "simplified",
        "DateSubscribed": "3/18/20",
        "Status": "subscribed"
      },
      {
        "ListId": "3-traditional",
        "SubscriberEmail": "test@test.com",
        "CharacterSet": "traditional",
        "DateSubscribed": "3/18/20",
        "Status": "unsubscribed"
      }
    ]

  return all_contacts

def mocked_s3_put(data_rows, todays_date):
  return

class BackupDynamoDBS3Test(unittest.TestCase):

  @mock.patch('backup_dynamodb_s3.app.scan_contacts_table', side_effect=mocked_dynamodb_scan)
  @mock.patch('backup_dynamodb_s3.app.write_to_s3', side_effect=mocked_s3_put)
  def test_build(self, s3_put_mock, dynamo_scan_mock):
    
    response = lambda_handler(self.scheduled_event(), "")

    self.assertEqual(dynamo_scan_mock.call_count, 1)
    self.assertEqual(s3_put_mock.call_count, 1)

  def scheduled_event(self):
    return {
      "version": "0",
      "id": "d77bcbc4-0b2b-4d45-9694-b1df99175cfb",
      "detail-type": "Scheduled Event",
      "source": "aws.events",
      "account": "123456789",
      "time": "2016-09-25T04:55:26Z",
      "region": "us-east-1",
      "resources": [
        "arn:aws:events:us-east-1:123456789:rule/test-scheduled-event"
      ],
      "detail": {}
    }

if __name__ == '__main__':
    unittest.main()


