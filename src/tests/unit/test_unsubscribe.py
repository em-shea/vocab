import json
import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table', 'USER_POOL_ID': 'mock-id'}):
    from unsubscribe.app import lambda_handler

def mocked_unsubscribe_single_list(date, cognito_id, list_data):
    return

def mocked_look_up_cognito_id(event_body):
    return '123456'

def mocked_query_single_user(cognito_id):
    response = [
        {
            "Date subscribed":"2021-06-16T23:06:48.646688",
            "GSI1PK":"USER",
            "List name":"HSK Level 6",
            "SK":"LIST#1ebcad41-197a-123123#TRADITIONAL",
            "Status":"subscribed",
            "GSI1SK":"USER#770e2827-7666-123123123#LIST#1ebcad41-197a-123123#TRADITIONAL",
            "PK":"USER#770e2827-7666-123123123",
            "Character set":"traditional",
        },
        {
            "Date subscribed":"2021-06-16T23:06:48.646688",
            "GSI1PK":"USER",
            "List name":"HSK Level 2",
            "SK":"LIST#1ebcad41-197a-123123#TRADITIONAL",
            "Status":"subscribed",
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
    return response

class UnsubscribeTest(unittest.TestCase):

    @mock.patch('unsubscribe.app.unsubscribe_single_list', side_effect=mocked_unsubscribe_single_list)
    @mock.patch('unsubscribe.app.look_up_cognito_id', side_effect=mocked_look_up_cognito_id)
    @mock.patch('user_service.query_single_user', side_effect=mocked_query_single_user)
    def test_unsubscribe(self, query_single_user_mock, look_up_cognito_id_mock, unsubscribe_single_list_mock):

        event_body = {
            "cognito_id":"",
            "email":"me@testemail.com",
            "character_set_preference":"simplified",
            "list": {
                    "list_id":"123",
                    "list_name":"HSK Level 1",
                    "character_set":"simplified"
                }
        }
        response = lambda_handler(self.apig_event(json.dumps(event_body)), "")

        self.assertEqual(query_single_user_mock.call_count, 0)
        self.assertEqual(look_up_cognito_id_mock.call_count, 1)
        self.assertEqual(unsubscribe_single_list_mock.call_count, 1)
    
    @mock.patch('unsubscribe.app.unsubscribe_single_list', side_effect=mocked_unsubscribe_single_list)
    @mock.patch('unsubscribe.app.look_up_cognito_id', side_effect=mocked_look_up_cognito_id)
    @mock.patch('user_service.query_single_user', side_effect=mocked_query_single_user)
    def test_unsubscribe_all(self, query_single_user_mock, look_up_cognito_id_mock, unsubscribe_single_list_mock):

        event_body = {
            "cognito_id":"",
            "email":"me@testemail.com",
            "character_set_preference":"simplified",
            "list": ""
        }
        response = lambda_handler(self.apig_event(json.dumps(event_body)), "")

        self.assertEqual(query_single_user_mock.call_count, 1)
        self.assertEqual(look_up_cognito_id_mock.call_count, 1)
        self.assertEqual(unsubscribe_single_list_mock.call_count, 2)
    
    def apig_event(self, event_body):
        return {
            "resource":"/unsub",
            "path":"/unsub",
            "body":event_body,
            "httpMethod":"POST",
            "headers":{
                "Accept":"application/json, text/plain, */*",
                "accept-encoding":"gzip, deflate, br",
                "Accept-Language":"en-US,en;q=0.9,zh-CN;q=0.8,zh-HK;q=0.7,zh-MO;q=0.6,zh;q=0.5",
                "Authorization":"eyJraWQiOiJq1231235fOwKv46JpjurGKzvma17eqCoaw",
                "CloudFront-Forwarded-Proto":"https",
                "CloudFront-Is-Desktop-Viewer":"true",
                "CloudFront-Is-Mobile-Viewer":"false",
                "CloudFront-Is-SmartTV-Viewer":"false",
                "CloudFront-Is-Tablet-Viewer":"false",
                "CloudFront-Viewer-Country":"IE",
                "Host":"api.haohaotiantian.com",
                "origin":"http://localhost:8080",
                "Referer":"http://localhost:8080/",
                "sec-ch-ua":"\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\"",
                "sec-ch-ua-mobile":"?0",
                "sec-fetch-dest":"empty",
                "sec-fetch-mode":"cors",
                "sec-fetch-site":"cross-site",
                "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Via":"2.0 f8591238.cloudfront.net (CloudFront)",
                "X-Amz-Cf-Id":"rex4fmbUq5pvK123fj5bGvpw==",
                "X-Amzn-Trace-Id":"Root=1-60e123b7e7b70",
                "X-Forwarded-For":"123",
                "X-Forwarded-Port":"123",
                "X-Forwarded-Proto":"https"
            },
            "multiValueHeaders":{
                "Accept":[
                    "application/json, text/plain, */*"
                ],
                "accept-encoding":[
                    "gzip, deflate, br"
                ],
                "Accept-Language":[
                    "en-US,en;q=0.9,zh-CN;q=0.8,zh-HK;q=0.7,zh-MO;q=0.6,zh;q=0.5"
                ],
                "Authorization":[
                    "eyJraWQiOiJqVmhFdEN4Y123vZ25pdG123GKzvma17eqCoaw"
                ],
                "CloudFront-Forwarded-Proto":[
                    "https"
                ],
                "CloudFront-Is-Desktop-Viewer":[
                    "true"
                ],
                "CloudFront-Is-Mobile-Viewer":[
                    "false"
                ],
                "CloudFront-Is-SmartTV-Viewer":[
                    "false"
                ],
                "CloudFront-Is-Tablet-Viewer":[
                    "false"
                ],
                "CloudFront-Viewer-Country":[
                    "IE"
                ],
                "Host":[
                    "api.haohaotiantian.com"
                ],
                "origin":[
                    "http://localhost:8080"
                ],
                "Referer":[
                    "http://localhost:8080/"
                ],
                "sec-ch-ua":[
                    "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"91\", \"Chromium\";v=\"91\""
                ],
                "sec-ch-ua-mobile":[
                    "?0"
                ],
                "sec-fetch-dest":[
                    "empty"
                ],
                "sec-fetch-mode":[
                    "cors"
                ],
                "sec-fetch-site":[
                    "cross-site"
                ],
                "User-Agent":[
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
                ],
                "Via":[
                    "2.0 123.cloudfront.net (CloudFront)"
                ],
                "X-Amz-Cf-Id":[
                    "rex4fmbU123BVnGAOV9sfj5bGvpw=="
                ],
                "X-Amzn-Trace-Id":[
                    "Root=1-60e6d123b70"
                ],
                "X-Forwarded-For":[
                    "123"
                ],
                "X-Forwarded-Port":[
                    "443"
                ],
                "X-Forwarded-Proto":[
                    "https"
                ]
            },
            "queryStringParameters":"None",
            "multiValueQueryStringParameters":"None",
            "pathParameters":"None",
            "stageVariables":"None",
            "requestContext":{
                "resourceId":"123",
                "authorizer":{
                    "claims":{
                        "sub":"123123123",
                        "aud":"123123",
                        "email_verified":"true",
                        "event_id":"cc6a7b68-e1bc-417b-9344-123",
                        "token_use":"id",
                        "auth_time":"1625312024",
                        "iss":"https://cognito-idp.us-east-1.amazonaws.com/us-east-1_123",
                        "cognito:username":"123123123",
                        "exp":"Thu Jul 08 11:38:59 UTC 2021",
                        "iat":"Thu Jul 08 10:38:59 UTC 2021",
                        "email":"test@email.com"
                    }
                },
                "resourcePath":"/user_data",
                "httpMethod":"GET",
                "extendedRequestId":"CJZWoF123FT_Q=",
                "requestTime":"08/Jul/2021:10:38:59 +0000",
                "path":"/user_data",
                "accountId":"123",
                "protocol":"HTTP/1.1",
                "stage":"Prod",
                "domainPrefix":"api",
                "requestTimeEpoch":123,
                "requestId":"11875c1237fec0aab",
                "identity":{
                    "cognitoIdentityPoolId":"None",
                    "accountId":"None",
                    "cognitoIdentityId":"None",
                    "caller":"None",
                    "sourceIp":"54",
                    "principalOrgId":"None",
                    "accessKey":"None",
                    "cognitoAuthenticationType":"None",
                    "cognitoAuthenticationProvider":"None",
                    "userArn":"None",
                    "userAgent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "user":"None"
                },
                "domainName":"api.haohaotiantian.com",
                "apiId":"123"
            },
            "isBase64Encoded":False
            }

    if __name__ == '__main__':
        unittest.main()