import json

import unittest
from unittest import mock

from boto3.dynamodb.conditions import Key

from set_user_data.app import lambda_handler, update_user_data, NothingToUpdate


def _user_item(uid='u1', **overrides):
    item = {
        'PK': f'USER#{uid}', 'SK': f'USER#{uid}',
        'GSI1PK': 'USER', 'GSI1SK': f'USER#{uid}',
        'Email address': f'{uid}@test.com',
        'Character set preference': 'simplified',
        'Date created': '2026-01-01T00:00:00',
        'User alias': 'Not set', 'User alias pinyin': 'Not set',
        'User alias emoji': 'Not set',
    }
    item.update(overrides)
    return item


def _read(table, uid='u1'):
    return table.query(KeyConditionExpression=Key('PK').eq(f'USER#{uid}'))['Items'][0]


def test_updates_only_the_fields_supplied(dynamodb_table):
    """The preferences switch sends language and character set alone.

    This used to require all four profile fields and raised KeyError otherwise,
    so it could only be called by the full profile form.
    """
    dynamodb_table.put_item(Item=_user_item())

    update_user_data('u1', {'character_set_preference': 'traditional',
                            'language_preference': 'cn'})

    item = _read(dynamodb_table)
    assert item['Character set preference'] == 'traditional'
    assert item['Language preference'] == 'cn'
    # Untouched fields are left alone rather than blanked.
    assert item['User alias'] == 'Not set'
    assert item['Email address'] == 'u1@test.com'


def test_updates_the_full_profile(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item())

    update_user_data('u1', {
        'user_alias': '小王 📙', 'user_alias_pinyin': 'xiǎo wáng',
        'user_alias_emoji': '📙', 'character_set_preference': 'traditional',
    })

    item = _read(dynamodb_table)
    assert item['User alias'] == '小王 📙'
    assert item['User alias emoji'] == '📙'
    assert item['Character set preference'] == 'traditional'


def test_unknown_fields_are_ignored(dynamodb_table):
    """A caller must not be able to write arbitrary attributes onto a user."""
    dynamodb_table.put_item(Item=_user_item())

    update_user_data('u1', {'language_preference': 'cn', 'Email address': 'attacker@x.com',
                            'GSI1PK': 'nonsense'})

    item = _read(dynamodb_table)
    assert item['Language preference'] == 'cn'
    assert item['Email address'] == 'u1@test.com'
    assert item['GSI1PK'] == 'USER'


def test_invalid_preference_values_are_ignored(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item())

    update_user_data('u1', {'language_preference': 'fr',
                            'character_set_preference': 'traditional'})

    item = _read(dynamodb_table)
    assert 'Language preference' not in item
    assert item['Character set preference'] == 'traditional'


def test_no_recognised_fields_raises(dynamodb_table):
    dynamodb_table.put_item(Item=_user_item())

    try:
        update_user_data('u1', {'nothing': 'useful'})
    except NothingToUpdate:
        pass
    else:
        raise AssertionError('expected NothingToUpdate')


class SetUserDataTest(unittest.TestCase):

    @mock.patch('set_user_data.app.update_user_data', side_effect=NothingToUpdate())
    def test_request_with_no_known_fields_returns_400(self, update_mock):
        response = lambda_handler(self.sub_apig_event(json.dumps({'nope': 1})), "")

        self.assertEqual(response["statusCode"], 400)
        self.assertFalse(json.loads(response["body"])["success"])

    @mock.patch('set_user_data.app.update_user_data')
    def test_build(self, update_user_data_mock):

        apig_event_body =  {
            'user_alias': '小王 📙',
            'user_alias_pinyin': 'xiǎo wáng',
            'user_alias_emoji': '📙',
            'character_set_preference': 'traditional'
        }
        response = lambda_handler(self.sub_apig_event(json.dumps(apig_event_body)), "")

        self.assertEqual(update_user_data_mock.call_count, 1)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), {"success": True})
        # Handler forwards the cognito sub and the parsed request body to the writer.
        called_id, called_body = update_user_data_mock.call_args.args
        self.assertEqual(called_id, "123123123")
        self.assertEqual(called_body["user_alias"], "小王 📙")
        self.assertEqual(called_body["character_set_preference"], "traditional")

    @mock.patch('set_user_data.app.update_user_data', side_effect=Exception("dynamo down"))
    def test_update_failure_returns_502(self, update_user_data_mock):

        apig_event_body = {
            'user_alias': 'x', 'user_alias_pinyin': 'y',
            'user_alias_emoji': 'z', 'character_set_preference': 'simplified'
        }
        response = lambda_handler(self.sub_apig_event(json.dumps(apig_event_body)), "")

        self.assertEqual(response["statusCode"], 502)
        self.assertEqual(json.loads(response["body"]), {"success": False})


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