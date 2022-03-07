import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table'}):
    from get_user_data.app import lambda_handler

def mocked_query_single_user(cognito_user_id):
  return  [
        {
            "Date subscribed":"2021-06-16T23:06:48.646688",
            "GSI1PK":"USER",
            "List name":"HSK Level 6",
            "SK":"LIST#1ebcad41-197a-123123#TRADITIONAL",
            "Status":"SUBSCRIBED",
            "GSI1SK":"USER#770e2827-7666-123123123#LIST#1ebcad41-197a-123123#TRADITIONAL",
            "PK":"USER#770e2827-7666-123123123",
            "Character set":"traditional",
        },
        {
            "Date subscribed":"2021-06-16T23:06:48.646688",
            "GSI1PK":"USER",
            "List name":"HSK Level 2",
            "SK":"LIST#1ebcad41-197a-123123#SIMPLIFIED",
            "Status":"UNSUBSCRIBED",
            "GSI1SK":"USER#770e2827-7666-123123123#LIST#1ebcad41-197a-123123#TRADITIONAL",
            "PK":"USER#770e2827-7666-123123123",
            "Character set":"simplified",
        },
        {
            "GSI1PK":"USER",
            "Date created":"2021-06-16T23:06:48.467526",
            "Character set preference":"traditional",
            "SK":"USER#770e2827-7666-123123123",
            "Email address":"test@email.com",
            "GSI1SK":"USER#770e2827-7666-123123123",
            "PK":"USER#770e2827-7666-123123123",
            "User alias": "Not set",
            "User alias pinyin": "Not set",
            "User alias emoji": "Not set"
        }
    ]

class GetUserDataTest(unittest.TestCase):

  @mock.patch('user_service.query_single_user', side_effect=mocked_query_single_user)
  def test_build(self, query_single_user_mock):
    
    response = lambda_handler(self.apig_event(), "")

    self.assertEqual(query_single_user_mock.call_count, 1)

  def apig_event(self):
    return {
        "resource": "/user_data",
        "path": "/user_data",
        "httpMethod": "GET",
        "headers": {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-HK;q=0.7,zh-MO;q=0.6,zh;q=0.5",
            "Authorization": "123123123",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "GB",
            "Host": "api.haohaotiantian.com",
            "origin": "http://localhost:8080",
            "Referer": "http://localhost:8080/",
            "sec-ch-ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Via": "2.0 123.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "Iz123BjvWaSJQw==",
            "X-Amzn-Trace-Id": "Roo12312348867cca34e3",
            "X-Forwarded-For": "81.123",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https"
        },
        "multiValueHeaders": {
            "Accept": [
            "application/json, text/plain, */*"
            ],
            "Accept-Encoding": [
            "gzip, deflate, br"
            ],
            "Accept-Language": [
            "en-US,en;q=0.9,zh-CN;q=0.8,zh-HK;q=0.7,zh-MO;q=0.6,zh;q=0.5"
            ],
            "Authorization": [
            "123123123"
            ],
            "CloudFront-Forwarded-Proto": [
            "https"
            ],
            "CloudFront-Is-Desktop-Viewer": [
            "true"
            ],
            "CloudFront-Is-Mobile-Viewer": [
            "false"
            ],
            "CloudFront-Is-SmartTV-Viewer": [
            "false"
            ],
            "CloudFront-Is-Tablet-Viewer": [
            "false"
            ],
            "CloudFront-Viewer-Country": [
            "GB"
            ],
            "Host": [
            "api.haohaotiantian.com"
            ],
            "origin": [
            "http://localhost:8080"
            ],
            "Referer": [
            "http://localhost:8080/"
            ],
            "sec-ch-ua": [
            "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\""
            ],
            "sec-ch-ua-mobile": [
            "?0"
            ],
            "sec-fetch-dest": [
            "empty"
            ],
            "sec-fetch-mode": [
            "cors"
            ],
            "sec-fetch-site": [
            "cross-site"
            ],
            "User-Agent": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            ],
            "Via": [
            "2.0 123.cloudfront.net (CloudFront)"
            ],
            "X-Amz-Cf-Id": [
            "IzAVY123WaSJQw=="
            ],
            "X-Amzn-Trace-Id": [
            "Root=1-12367cca34e3"
            ],
            "X-Forwarded-For": [
            "123"
            ],
            "X-Forwarded-Port": [
            "443"
            ],
            "X-Forwarded-Proto": [
            "https"
            ]
        },
        "queryStringParameters": "None",
        "multiValueQueryStringParameters": "None",
        "pathParameters": "None",
        "stageVariables": "None",
        "requestContext": {
            "resourceId": "vylypt",
            "authorizer": {
            "claims": {
                "sub": "770123132862dba2",
                "aud": "mi4ig1231236mgodd",
                "email_verified": "true",
                "event_id": "cc6a1231239878f86be",
                "token_use": "id",
                "auth_time": "123",
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_123123",
                "cognito:username": "770e2123123862dba2",
                "exp": "Sat Jul 03 12:33:44 UTC 2021",
                "iat": "Sat Jul 03 11:33:44 UTC 2021",
                "email": "test@email.com"
            }
            },
            "resourcePath": "/user_data",
            "httpMethod": "GET",
            "extendedRequestId": "B5JkUG123FeWw=",
            "requestTime": "03/Jul/2021:12:20:43 +0000",
            "path": "/user_data",
            "accountId": "132123",
            "protocol": "HTTP/1.1",
            "stage": "Prod",
            "domainPrefix": "api",
            "requestTimeEpoch": 123123,
            "requestId": "91d7123123f4a3764",
            "identity": {
            "cognitoIdentityPoolId": "None",
            "accountId": "None",
            "cognitoIdentityId": "None",
            "caller": "None",
            "sourceIp": "81.123",
            "principalOrgId": "None",
            "accessKey": "None",
            "cognitoAuthenticationType": "None",
            "cognitoAuthenticationProvider": "None",
            "userArn": "None",
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "user": "None"
            },
            "domainName": "api.haohaotiantian.com",
            "apiId": "123"
        },
        "body": "None",
        "isBase64Encoded": False
    }