import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import os
import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table-name'}):
  from get_review_words.app import lambda_handler

def get_words_with_params_mock(list_id, from_date, todays_date):

  return {
    "1ebcad3f-5dfd-6bfe-bda4-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}]
  }

def get_words_no_params_mock(todays_date):

  return {
    "1ebcad3f-5dfd-6bfe-bda4-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}],
    "1ebcad3f-adc0-6f42-b8b1-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}],
    "1ebcad3f-f815-6b92-b3e8-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}],
    "1ebcad40-414f-6bc8-859d-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}],
    "1ebcad40-bb9e-6ece-a366-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}],
    "1ebcad41-197a-6700-95a3-acde48001122": [{'SK': 'DATESENT#2020-10-10', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '多少', 'Pinyin': 'duō shǎo', 'Definition': 'number; amount; somewhat', 'HSK Level': '1', 'Traditional': '多少', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-11', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '怎么', 'Pinyin': 'zěn me', 'Definition': 'how?; what?; why?', 'HSK Level': '1', 'Traditional': '怎麼', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'SK': 'DATESENT#2020-10-12', 'PK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'Word': {'Simplified': '吗', 'Pinyin': 'ma', 'Definition': '(question tag)', 'HSK Level': '1', 'Traditional': '嗎', 'Difficulty level': 'Beginner', 'Audio file key': ''}}]
  }

class GetReviewWordsTest(unittest.TestCase):

  @mock.patch('get_review_words.app.pull_words_with_params', side_effect=get_words_with_params_mock)
  @mock.patch('get_review_words.app.pull_words_no_params', side_effect=get_words_no_params_mock)
  def test_build(self, no_params_mock, params_mock):

    params = {'list_id':'1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'date_range': '10'}

    response = lambda_handler(self.review_apig_event(params), "")

    self.assertEqual(params_mock.call_count, 1)
  
  @mock.patch('get_review_words.app.pull_words_with_params', side_effect=get_words_with_params_mock)
  @mock.patch('get_review_words.app.pull_words_no_params', side_effect=get_words_no_params_mock)
  def test_no_params(self, no_params_mock, params_mock):

    params = None

    response = lambda_handler(self.review_apig_event(params), "")

    self.assertEqual(no_params_mock.call_count, 1)

  def review_apig_event(self, params):
    return {
      "body": json.dumps(params),
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
      "queryStringParameters": params,
      "stageVariables": {
        "stageVarName": "stageVarValue"
      }
    }

if __name__ == '__main__':
    unittest.main()