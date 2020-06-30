import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

# ses, dynamo, lambda clients
# input: api gateway call w email, hsk list params
# output: create dynamo user, send conf email

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

  def apig_event(self):
    {
      "body": "",
      "path": "/sample_vocab",
      "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, lzma, sdch, br",
        "Accept-Language": "en-US,en;q=0.8",
        "CloudFront-Forwarded-Proto": "https",
        "CloudFront-Is-Desktop-Viewer": "true",
        "CloudFront-Is-Mobile-Viewer": "false",
        "CloudFront-Is-SmartTV-Viewer": "false",
        "CloudFront-Is-Tablet-Viewer": "false",
        "CloudFront-Viewer-Country": "US",
        "Host": "wt6mne2s9k.execute-api.us-west-2.amazonaws.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36 OPR/39.0.2256.48",
        "Via": "1.1 fb7cca60f0ecd82ce07790c9c5eef16c.cloudfront.net (CloudFront)",
        "X-Amz-Cf-Id": "nBsWBOrSHMgnaROZJK1wGCZ9PcRcSpq_oSXZNQwQ10OTZL4cimZo3g==",
        "X-Forwarded-For": "192.168.100.1, 192.168.1.1",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https"
      },
      "multiValueHeaders": {},
      "isBase64Encoded": false,
      "multiValueQueryStringParameters": {},
      "requestContext": {
        "accountId": "123456789012",
        "resourceId": "us4z18",
        "stage": "test",
        "requestId": "41b45ea3-70b5-11e6-b7bd-69b5aaebc7d9",
        "identity": {
          "accessKey": "",
          "apiKeyId": "",
          "cognitoIdentityPoolId": "",
          "accountId": "",
          "cognitoIdentityId": "",
          "caller": "",
          "apiKey": "",
          "sourceIp": "192.168.100.1",
          "cognitoAuthenticationType": "",
          "cognitoAuthenticationProvider": "",
          "userArn": "",
          "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36 OPR/39.0.2256.48",
          "user": ""
        },
        "path": "",
        "requestTimeEpoch": 0,
        "resourcePath": "/{proxy+}",
        "httpMethod": "GET",
        "apiId": "wt6mne2s9k"
      },
      "resource": "/{proxy+}",
      "httpMethod": "GET",
      "queryStringParameters": {
        "name": "me"
      },
      "stageVariables": {
        "stageVarName": "stageVarValue"
      }
    }

if __name__ == '__main__':
    unittest.main()