import json

import unittest
from unittest import mock

from get_sentences.app import lambda_handler, pull_user_sentences
from set_sentence.app import update_sentence


def test_sentences_written_by_set_sentence_are_readable(dynamodb_table):
    """Round-trip regression: the read path must match the key shape the write path uses.

    get_sentences queried SK begins_with('SENTENCE') while set_sentence writes
    'DATE#<date>#SENTENCE#<id>', so this returned nothing no matter how many
    sentences a user had saved.
    """
    body = {
        "sentence_id": "sentence-1",
        "sentence": "我喜欢学中文。",
        "list_id": "123",
        "character_set": "simplified",
        "word": {"Word id": "w1", "Simplified": "中文"},
    }
    update_sentence("user-1", body, "2021-11-04")

    items = pull_user_sentences("user-1")

    assert len(items) == 1
    assert items[0]["Sentence"] == "我喜欢学中文。"
    assert items[0]["Sentence id"] == "sentence-1"


def test_quizzes_are_filtered_out_of_the_sentence_query(dynamodb_table):
    """The query reads the whole DATE# range, so quizzes must be filtered back out."""
    update_sentence("user-1", {
        "sentence_id": "sentence-1", "sentence": "我喜欢学中文。", "list_id": "123",
        "character_set": "simplified", "word": {"Word id": "w1"},
    }, "2021-11-04")
    dynamodb_table.put_item(Item={
        "PK": "USER#user-1",
        "SK": "DATE#2021-11-04#QUIZ#quiz-1",
        "Quiz id": "quiz-1",
    })

    items = pull_user_sentences("user-1")

    assert len(items) == 1
    assert items[0]["Sentence id"] == "sentence-1"


def test_other_users_sentences_are_not_returned(dynamodb_table):
    update_sentence("user-1", {
        "sentence_id": "s1", "sentence": "第一句。", "list_id": "123",
        "character_set": "simplified", "word": {"Word id": "w1"},
    }, "2021-11-04")
    update_sentence("user-2", {
        "sentence_id": "s2", "sentence": "第二句。", "list_id": "123",
        "character_set": "simplified", "word": {"Word id": "w1"},
    }, "2021-11-04")

    items = pull_user_sentences("user-1")

    assert len(items) == 1
    assert items[0]["Sentence id"] == "s1"

# Item shape matches what set_sentence actually writes: the sentence marker sits in
# the middle of the SK, and the id is stored as its own attribute.
def mocked_pull_user_sentences(cognito_id):
        example_response = [
            {
                "GSI1PK":"DATE#2021-11-04",
                "Date created":"2021-11-04",
                "Sentence":"我喜欢韩语。",
                "Sentence id":"12345-3763-6260-bf4f-6a03d2d3da0b",
                "SK":"DATE#2021-11-04#SENTENCE#12345-3763-6260-bf4f-6a03d2d3da0b",
                "GSI1SK":"SENTENCE#12345-3763-6260-bf4f-6a03d2d3da0b",
                "PK":"USER#12345-c759-48cd-97ea-3e8876eedb2d",
                "List id":"12345",
                "Character set":"simplified"
            },
            {
                "GSI1PK":"DATE#2021-11-05",
                "Date created":"2021-11-05",
                "Sentence":"我喜欢法语。",
                "Sentence id":"12345-2dd9-6886-bf4f-6a03d2d3da0b",
                "SK":"DATE#2021-11-05#SENTENCE#12345-2dd9-6886-bf4f-6a03d2d3da0b",
                "GSI1SK":"SENTENCE#12345-2dd9-6886-bf4f-6a03d2d3da0b",
                "PK":"USER#996ca9a4-c759-48cd-97ea-3e8876eedb2d",
                "List id":"5678",
                "Character set":"simplified"
            }
        ]
        return example_response

class GetSentencesTest(unittest.TestCase):

    @mock.patch('get_sentences.app.pull_user_sentences', side_effect=mocked_pull_user_sentences)
    def test_build(self, pull_user_sentences_mock):

        response = lambda_handler(self.sub_apig_event(), "")
        body = json.loads(response["body"])

        self.assertEqual(pull_user_sentences_mock.call_count, 1)
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(body["success"])

        sentences = body["data"]["sentences"]
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0]["sentence"], "我喜欢韩语。")
        self.assertEqual(sentences[0]["sentence_id"], "12345-3763-6260-bf4f-6a03d2d3da0b")
        self.assertEqual(sentences[0]["character_set"], "simplified")

    @mock.patch('get_sentences.app.pull_user_sentences', side_effect=Exception("DynamoDB unavailable"))
    def test_query_failure_returns_502(self, pull_user_sentences_mock):

        response = lambda_handler(self.sub_apig_event(), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 502)
        self.assertFalse(body["success"])


    def sub_apig_event(self):
        return {
            "resource":"/sentence",
            "path":"/sentence",
            "body":"",
            "httpMethod":"GET",
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