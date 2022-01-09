import json
import sys
sys.path.append('../../')

import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table'}):
    from set_user_data.app import lambda_handler

class SetUserDataTest(unittest.TestCase):

    # @mock.patch('set_user_data.app.create_user', side_effect=mocked_create_user)
    # @mock.patch('set_user_data.app.create_subscription', side_effect=mocked_create_subscription)
    def test_build(self):

        apig_event_body =  {
            'user_alias': '小王 📙',
            'user_alias_pinyin': 'xiǎo wáng',
            'character_set_preference': 'traditional'
        }
        response = lambda_handler(self.sub_apig_event(json.dumps(apig_event_body)), "")

        # self.assertEqual(create_user_mock.call_count, 1)
        # self.assertEqual(create_sub_mock.call_count, 1)
    
    def sub_apig_event(self, event_body):
        return {
            "resource":"/set_subs",
            "path":"/set_subs",
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