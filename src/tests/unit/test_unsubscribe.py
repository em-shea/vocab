import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

# wip

# dynamo clients
# input: api gateway call w email, hsk list params
# output: create dynamo user, send conf email

# test cases: if list = all, if list = 1-simplified; if subscribed email found, if not found

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table-name'}):
  from unsubscribe.app import lambda_handler

def mocked_get_dynamo_contacts(contact_keys):

  subscriber_list = []

  return subscriber_list

def mocked_unsubscribe_user(subscriber_list):

  return

class UnsubscribeTest(unittest.TestCase):

  @mock.patch('unsubscribe.app.get_dynamo_contacts', side_effect=mocked_get_dynamo_contacts)
  @mock.patch('unsubscribe.app.unsubscribe_user', side_effect=mocked_unsubscribe_user)
  def test_build(self, get_dynamo_contacts_mock, unsubscribe_user_mock):

    unsub_list = "4-traditional"

    response = lambda_handler(self.unsub_apig_event(unsub_list), "")

    self.assertEqual(get_dynamo_contacts_mock.call_count, 1)
    self.assertEqual(unsubscribe_user_mock.call_count, 1)
  
  def unsub_apig_event(self, unsub_list):
    event_body = json.dumps({'email':'user@example.com', 'list':unsub_list})
    return {
      "body": event_body,
      "path": "/sub",
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
      "isBase64Encoded": False,
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
        "email":"user@example.com",
        "list":unsub_list
      },
      "stageVariables": {
        "stageVarName": "stageVarValue"
      }
    }

if __name__ == '__main__':
    unittest.main()