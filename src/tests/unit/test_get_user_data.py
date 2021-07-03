import sys
sys.path.append('../../')

import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'DYNAMODB_TABLE_NAME': 'mock-table'}):
    from get_user_data.app import lambda_handler

def mocked_get_user_data(cognito_user_id):
  return  [
        {
            "Date subscribed":"2021-06-16T23:06:48.646688",
            "GSI1PK":"USER",
            "List name":"HSK Level 6",
            "SK":"LIST#1ebcad41-197a-123123",
            "Status":"SUBSCRIBED",
            "GSI1SK":"USER#770e2827-7666-123123123#LIST#1ebcad41-197a-123123#TRADITIONAL",
            "PK":"USER#770e2827-7666-123123123",
            "Character set":"traditional"
        },
        {
            "GSI1PK":"USER",
            "Date created":"2021-06-16T23:06:48.467526",
            "Character set preference":"traditional",
            "SK":"USER#770e2827-7666-123123123",
            "Email address":"test@email.com",
            "GSI1SK":"USER#770e2827-7666-123123123",
            "PK":"USER#770e2827-7666-123123123"
        }
    ]

class GetUserDataTest(unittest.TestCase):

  @mock.patch('get_user_data.app.get_user_data', side_effect=mocked_get_user_data)
  def test_build(self, get_user_data_mock):
    
    response = lambda_handler(self.apig_event(), "")

    self.assertEqual(get_user_data_mock.call_count, 1)

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
            "Via": "2.0 83ec53fe631231239a0dc49.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "IzAVYoTv123123gWRZWs79mFBjvWaSJQw==",
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
            "2.0 83ec51231230dc49.cloudfront.net (CloudFront)"
            ],
            "X-Amz-Cf-Id": [
            "IzAVYoTvttI123123123ZWs79mFBjvWaSJQw=="
            ],
            "X-Amzn-Trace-Id": [
            "Root=1-12367cca34e3"
            ],
            "X-Forwarded-For": [
            "81.98.52.111, 70.132.38.79"
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