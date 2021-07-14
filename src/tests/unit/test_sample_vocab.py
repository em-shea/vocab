import sys
sys.path.append('../../')
sys.path.append('../../layer')

import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'WORDS_BUCKET_NAME': 'mock-words-bucket', 'WORDS_BUCKET_KEY': 'mock-words-key'}):
  from sample_vocab.app import lambda_handler

def mocked_get_random(hsk_level):
  
  hsk_level_index = int(hsk_level) - 1

  local_vocab_lists = [
        [
          {
            "Word": "怎么样",
            "Pronunciation": "zěn me yàng",
            "Definition": "how?; how about?; how was it?; how are things?",
            "HSK Level": "1",
            "Word-Traditional": "怎麼樣"
          }
        ],
        [
          {
            "Word": "回答",
            "Pronunciation": "huí dá",
            "Definition": "to reply; to answer; the answer; CL:個|个[ge4]",
            "HSK Level": "2",
            "Word-Traditional": "回答"
          }
        ],
        [
          {
            "Word": "腿",
            "Pronunciation": "tuǐ",
            "Definition": "leg; CL:條|条[tiao2]",
            "HSK Level": "3",
            "Word-Traditional": "腿"
          }
        ],
        [
          {
            "Word": "乱",
            "Pronunciation": "luàn",
            "Definition": "in confusion or disorder; in a confused state of mind; disorder; upheaval; riot; illicit sexual relations; to throw into disorder; to mix up; indiscriminate; random; arbitrary",
            "HSK Level": "4",
            "Word-Traditional": "亂"
          }
        ],
        [
          {
            "Word": "叉子",
            "Pronunciation": "chā zi",
            "Definition": "fork; CL:把[ba3]",
            "HSK Level": "5",
            "Word-Traditional": "叉子"
          }
        ],
        [
          {
            "Word": "注视",
            "Pronunciation": "zhù shì",
            "Definition": "to watch attentively; to gaze",
            "HSK Level": "6",
            "Word-Traditional": "注視"
          }
        ],
    ]

  return local_vocab_lists[hsk_level_index]

class SampleVocabTest(unittest.TestCase):

  @mock.patch('layer.random_word_service.select_random_word', side_effect=mocked_get_random)
  def test_build(self, get_random_mock):
    
    response = lambda_handler(self.apig_event(), "")
    response_body = json.loads(response["body"])

    self.assertEqual(get_random_mock.call_count, 30)
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