import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

# done

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'SUB_TOPIC_ARN': 'mock-topic'}):
  from cw_logs_notifications.app import lambda_handler

def mocked_sns_publish(message):
  return

def mocked_decode_decompress_log_data(event):
  log_json = {
      "messageType": "DATA_MESSAGE",
      "owner": "123456789012",
      "logGroup": "/aws/lambda/mock-function-name",
      "logStream": "2019/03/13/[$LATEST]94fa867e5374431291a7fc14e2f56ae7",
      "subscriptionFilters": [
          "LambdaStream_cloudwatchlogs"
      ],
      "logEvents": [
        {
          "id": "34622316099697884706540976068822859012661220141643892546",
          "timestamp": 1552518348220,
          "message": "REPORT RequestId: 6234bffe-149a-b642-81ff-2e8e376d8aff\tDuration: 46.84 ms\tBilled Duration: 100 ms \tMemory Size: 192 MB\tMax Memory Used: 72 MB\t\n"
        }
      ]
    }

  return log_json

class CWLogsNotificationsTest(unittest.TestCase):

  @mock.patch('cw_logs_notifications.app.publish_to_sns', side_effect=mocked_sns_publish)
  @mock.patch('cw_logs_notifications.app.decode_and_decompress_log', side_effect=mocked_decode_decompress_log_data)
  def test_build(self, sns_publish_mock, decode_logs_mock):
    
    response = lambda_handler(self.cw_logs_event(), "")

    self.assertEqual(sns_publish_mock.call_count, 1)
    self.assertEqual(decode_logs_mock.call_count, 1)

  def cw_logs_event(self):
    return {
      "awslogs": {
        "data": "H4sIAIOmuFwAA8tJLVGvUqjKLFAoycgsBgAzQsm5DgAAAA=="
      }
    }

if __name__ == '__main__':
    unittest.main()


