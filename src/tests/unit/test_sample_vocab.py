import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table'}):
  from sample_vocab.app import lambda_handler

def mocked_get_words_in_list(list_id):

  test_words = {'1ebcad3f-5dfd-6bfe-bda4-acde48001122': [{'list_id': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'word_id': 'WORD#1ec4a4cc-4277-6a38-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.7134f82e-392f-43fe-86f3-7d82a1003521.mp3', 'Definition': 'to love; affection; to be fond of; to like', 'Difficulty level': 'Beginner', 'HSK Level': '1', 'Pinyin': 'ài', 'Simplified': '爱', 'Traditional': '愛'}}, {'list_id': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'word_id': 'WORD#1ec4a4cc-4277-6cea-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.465302fd-09ea-42c1-8e81-9c119a4a10e0.mp3', 'Definition': 'eight; 8', 'Difficulty level': 'Beginner', 'HSK Level': '1', 'Pinyin': 'bā', 'Simplified': '八', 'Traditional': '八'}}, {'list_id': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122', 'word_id': 'WORD#1ec4a4cc-4277-6d94-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.26e443f0-f020-4a62-954d-75da3f2575a6.mp3', 'Definition': '(informal) father; CL:個|个 gè,位 wèi', 'Difficulty level': 'Beginner', 'HSK Level': '1', 'Pinyin': 'bà ba', 'Simplified': '爸爸', 'Traditional': '爸爸'}}], '1ebcad3f-adc0-6f42-b8b1-acde48001122': [{'list_id': 'LIST#1ebcad3f-adc0-6f42-b8b1-acde48001122', 'word_id': 'WORD#1ec4a4cc-427e-61f8-b218-acde48001122', 'word': {'Simplified': '吧', 'Pinyin': 'ba', 'Definition': '(modal particle indicating polite suggestion); ...right?; ...OK?', 'HSK Level': '2', 'Traditional': '吧', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad3f-adc0-6f42-b8b1-acde48001122', 'word_id': 'WORD#1ec4a4cc-427e-6270-b218-acde48001122', 'word': {'Simplified': '白', 'Pinyin': 'bái', 'Definition': 'white; snowy; pure; bright; empty; blank; plain; clear; to make clear; in vain; gratuitous; free of charge; reactionary; anti-communist; funeral; to stare coldly; to write wrong character; to state; to explain; vernacular; spoken lines in opera; surname Bai', 'HSK Level': '2', 'Traditional': '白', 'Difficulty level': 'Beginner', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad3f-adc0-6f42-b8b1-acde48001122', 'word_id': 'WORD#1ec4a4cc-427e-6306-b218-acde48001122', 'word': {'Simplified': '百', 'Pinyin': 'bǎi', 'Definition': 'hundred; numerous; all kinds of; surname Bai', 'HSK Level': '2', 'Traditional': '百', 'Difficulty level': 'Beginner', 'Audio file key': ''}}], '1ebcad3f-f815-6b92-b3e8-acde48001122': [{'list_id': 'LIST#1ebcad3f-f815-6b92-b3e8-acde48001122', 'word_id': 'WORD#1ec4a4cc-4283-6e50-b218-acde48001122', 'word': {'Simplified': '阿姨', 'Pinyin': 'ā yí', 'Definition': "maternal aunt; step-mother; childcare worker; nursemaid; woman of similar age to one's parents (term of address used by child); CL:個|个 gè", 'HSK Level': '3', 'Traditional': '阿姨', 'Difficulty level': 'Intermediate', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad3f-f815-6b92-b3e8-acde48001122', 'word_id': 'WORD#1ec4a4cc-4284-603a-b218-acde48001122', 'word': {'Simplified': '啊', 'Pinyin': 'a', 'Definition': 'modal particle ending sentence, showing affirmation, approval, or consent', 'HSK Level': '3', 'Traditional': '啊', 'Difficulty level': 'Intermediate', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad3f-f815-6b92-b3e8-acde48001122', 'word_id': 'WORD#1ec4a4cc-4284-60e4-b218-acde48001122', 'word': {'Simplified': '矮', 'Pinyin': 'ǎi', 'Definition': 'low; short (in length)', 'HSK Level': '3', 'Traditional': '矮', 'Difficulty level': 'Intermediate', 'Audio file key': ''}}], '1ebcad40-414f-6bc8-859d-acde48001122': [{'list_id': 'LIST#1ebcad40-414f-6bc8-859d-acde48001122', 'word_id': 'WORD#1ec4a4cc-4294-67dc-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.a91ad5a1-f8aa-4107-81e3-3a76b7584a3a.mp3', 'Definition': 'romance; love (romantic); CL:個|个 gè', 'Difficulty level': 'Intermediate', 'HSK Level': '4', 'Pinyin': 'ài qíng', 'Simplified': '爱情', 'Traditional': '愛情'}}, {'list_id': 'LIST#1ebcad40-414f-6bc8-859d-acde48001122', 'word_id': 'WORD#1ec4a4cc-4294-6854-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.c983adc3-3e2c-424b-b5fb-1e3bf8f0a812.mp3', 'Definition': 'to arrange; to plan; to set up', 'Difficulty level': 'Intermediate', 'HSK Level': '4', 'Pinyin': 'ān pái', 'Simplified': '安排', 'Traditional': '安排'}}, {'list_id': 'LIST#1ebcad40-414f-6bc8-859d-acde48001122', 'word_id': 'WORD#1ec4a4cc-4294-68c2-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.c8c96005-7c6e-44cf-a547-e00884a9f679.mp3', 'Definition': 'safe; secure; safety; security', 'Difficulty level': 'Intermediate', 'HSK Level': '4', 'Pinyin': 'ān quán', 'Simplified': '安全', 'Traditional': '安全'}}], '1ebcad40-bb9e-6ece-a366-acde48001122': [{'list_id': 'LIST#1ebcad40-bb9e-6ece-a366-acde48001122', 'word_id': 'WORD#1ec4a4cc-42a7-68fa-b218-acde48001122', 'word': {'Simplified': '唉', 'Pinyin': 'āi', 'Definition': "interjection or grunt of agreement or recognition (e.g. yes, it's me!); to sigh", 'HSK Level': '5', 'Traditional': '唉', 'Difficulty level': 'Advanced', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad40-bb9e-6ece-a366-acde48001122', 'word_id': 'WORD#1ec4a4cc-42a7-6986-b218-acde48001122', 'word': {'Simplified': '爱护', 'Pinyin': 'ài hù', 'Definition': 'to cherish; to treasure; to take care of; to love and protect', 'HSK Level': '5', 'Traditional': '愛護', 'Difficulty level': 'Advanced', 'Audio file key': ''}}, {'list_id': 'LIST#1ebcad40-bb9e-6ece-a366-acde48001122', 'word_id': 'WORD#1ec4a4cc-42a7-69f4-b218-acde48001122', 'word': {'Simplified': '爱惜', 'Pinyin': 'ài xī', 'Definition': 'to cherish; to treasure; to use sparingly', 'HSK Level': '5', 'Traditional': '愛惜', 'Difficulty level': 'Advanced', 'Audio file key': ''}}], '1ebcad41-197a-6700-95a3-acde48001122': [{'list_id': 'LIST#1ebcad41-197a-6700-95a3-acde48001122', 'word_id': 'WORD#1ec4a4cc-42d4-62ec-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.d282f001-c0d9-4527-93c3-f7d0107ac1b3.mp3', 'Definition': 'hey; ow; ouch; interjection of pain or surprise', 'Difficulty level': 'Advanced', 'HSK Level': '6', 'Pinyin': 'āi yō', 'Simplified': '哎哟', 'Traditional': '哎喲'}}, {'list_id': 'LIST#1ebcad41-197a-6700-95a3-acde48001122', 'word_id': 'WORD#1ec4a4cc-42d4-6378-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.214cc658-5172-4774-8b6d-984ca2f4ac5c.mp3', 'Definition': 'to suffer from; to endure; to tide over (a difficult period); to delay', 'Difficulty level': 'Advanced', 'HSK Level': '6', 'Pinyin': 'ái', 'Simplified': '挨', 'Traditional': '挨'}}, {'list_id': 'LIST#1ebcad41-197a-6700-95a3-acde48001122', 'word_id': 'WORD#1ec4a4cc-42d4-63fa-b218-acde48001122', 'word': {'Audio file key': 'https://s3.us-east-1.amazonaws.com/vocab-audio-staging/audio/.8e48d401-8d03-4bab-b741-1b8efe8bad35.mp3', 'Definition': 'cancer', 'Difficulty level': 'Advanced', 'HSK Level': '6', 'Pinyin': 'ái zhèng', 'Simplified': '癌症', 'Traditional': '癌症'}}]}

  return test_words[list_id]

class SampleVocabTest(unittest.TestCase):

  @mock.patch('list_word_service.get_words_in_list', side_effect=mocked_get_words_in_list)
  def test_build(self, get_words_mock):
    
    response = lambda_handler(self.apig_event(), "")
    response_body = json.loads(response["body"])

    self.assertEqual(get_words_mock.call_count, 6)
    self.assertEqual(response["statusCode"], 200)
    self.assertIn("headers", response)
    self.assertIn("body", response)
    self.assertEqual(len(response_body), 6)

  def apig_event(self):
    return {
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
        "name": "me"
      },
      "stageVariables": {
        "stageVarName": "stageVarValue"
      }
    }

if __name__ == '__main__':
    unittest.main()