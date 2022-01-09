import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table-name'}):
  from get_review_words.app import lambda_handler

def get_words_with_params_mock(list_id, from_date, todays_date):

  return {
    "HSKLevel1": [{"Word": {"Definition": "(negative prefix for verbs); have not; not", "HSK Level": "1", "Word": "\u6ca1", "Word-Traditional": "\u6c92", "Pronunciation": "m\u00e9i"}, "Date": "2020-07-09", "ListId": "HSKLevel1"}, {"Word": {"Definition": "hello (interj., esp. on telephone); hey; to feed (sb or some animal)", "HSK Level": "1", "Word": "\u5582", "Word-Traditional": "\u9935", "Pronunciation": "w\u00e8i"}, "Date": "2020-07-10", "ListId": "HSKLevel1"}, {"Word": {"Definition": "to speak; to say; to talk; to gossip; to tell stories; talk; word", "HSK Level": "1", "Word": "\u8bf4\u8bdd", "Word-Traditional": "\u8aaa\u8a71", "Pronunciation": "shu\u014d hu\u00e0"}, "Date": "2020-07-11", "ListId": "HSKLevel1"}, {"Word": {"Definition": "sun; day; date, day of the month; abbr. for \u65e5\u672c|\u65e5\u672c Japan", "HSK Level": "1", "Word": "\u65e5", "Word-Traditional": "\u65e5", "Pronunciation": "r\u00ec"}, "Date": "2020-07-12", "ListId": "HSKLevel1"}, {"Word": {"Definition": "to know; to recognize; to be familiar with; acquainted with sth; knowledge; understanding; awareness; cognition", "HSK Level": "1", "Word": "\u8ba4\u8bc6", "Word-Traditional": "\u8a8d\u8b58", "Pronunciation": "r\u00e8n shi"}, "Date": "2020-07-13", "ListId": "HSKLevel1"}, {"Word": {"Definition": "dog; CL:\u96bb|\u53ea[zhi1],\u689d|\u6761[tiao2]", "HSK Level": "1", "Word": "\u72d7", "Word-Traditional": "\u72d7", "Pronunciation": "g\u01d2u"}, "Date": "2020-07-14", "ListId": "HSKLevel1"}, {"Word": {"Definition": "thing; stuff; person; CL:\u500b|\u4e2a[ge4],\u4ef6[jian4]", "HSK Level": "1", "Word": "\u4e1c\u897f", "Word-Traditional": "\u6771\u897f", "Pronunciation": "d\u014dng xi"}, "Date": "2020-07-15", "ListId": "HSKLevel1"}]
  }

def get_words_no_params_mock(todays_date):

  return {
    "HSKLevel1": [{"Word": {"Definition": "(negative prefix for verbs); have not; not", "HSK Level": "1", "Word": "\u6ca1", "Word-Traditional": "\u6c92", "Pronunciation": "m\u00e9i"}, "Date": "2020-07-09", "ListId": "HSKLevel1"}, {"Word": {"Definition": "hello (interj., esp. on telephone); hey; to feed (sb or some animal)", "HSK Level": "1", "Word": "\u5582", "Word-Traditional": "\u9935", "Pronunciation": "w\u00e8i"}, "Date": "2020-07-10", "ListId": "HSKLevel1"}, {"Word": {"Definition": "to speak; to say; to talk; to gossip; to tell stories; talk; word", "HSK Level": "1", "Word": "\u8bf4\u8bdd", "Word-Traditional": "\u8aaa\u8a71", "Pronunciation": "shu\u014d hu\u00e0"}, "Date": "2020-07-11", "ListId": "HSKLevel1"}, {"Word": {"Definition": "sun; day; date, day of the month; abbr. for \u65e5\u672c|\u65e5\u672c Japan", "HSK Level": "1", "Word": "\u65e5", "Word-Traditional": "\u65e5", "Pronunciation": "r\u00ec"}, "Date": "2020-07-12", "ListId": "HSKLevel1"}, {"Word": {"Definition": "to know; to recognize; to be familiar with; acquainted with sth; knowledge; understanding; awareness; cognition", "HSK Level": "1", "Word": "\u8ba4\u8bc6", "Word-Traditional": "\u8a8d\u8b58", "Pronunciation": "r\u00e8n shi"}, "Date": "2020-07-13", "ListId": "HSKLevel1"}, {"Word": {"Definition": "dog; CL:\u96bb|\u53ea[zhi1],\u689d|\u6761[tiao2]", "HSK Level": "1", "Word": "\u72d7", "Word-Traditional": "\u72d7", "Pronunciation": "g\u01d2u"}, "Date": "2020-07-14", "ListId": "HSKLevel1"}, {"Word": {"Definition": "thing; stuff; person; CL:\u500b|\u4e2a[ge4],\u4ef6[jian4]", "HSK Level": "1", "Word": "\u4e1c\u897f", "Word-Traditional": "\u6771\u897f", "Pronunciation": "d\u014dng xi"}, "Date": "2020-07-15", "ListId": "HSKLevel1"}],
    "HSKLevel2": [{"Word": {"Definition": "in the evening; CL:\u500b|\u4e2a[ge4]", "HSK Level": "2", "Word": "\u665a\u4e0a", "Word-Traditional": "\u665a\u4e0a", "Pronunciation": "w\u01cen shang"}, "Date": "2020-07-09", "ListId": "HSKLevel2"}, {"Word": {"Definition": "bus; CL:\u8f1b|\u8f86[liang4],\u73ed[ban1]", "HSK Level": "2", "Word": "\u516c\u5171\u6c7d\u8f66", "Word-Traditional": "\u516c\u5171\u6c7d\u8eca", "Pronunciation": "g\u014dng g\u00f2ng q\u00ec ch\u0113"}, "Date": "2020-07-10", "ListId": "HSKLevel2"}, {"Word": {"Definition": "rapid; quick; speed; rate; soon; almost; to make haste; clever; sharp (of knives or wits); forthright; plain-spoken; gratified; pleased; pleasant", "HSK Level": "2", "Word": "\u5feb", "Word-Traditional": "\u5feb", "Pronunciation": "ku\u00e0i"}, "Date": "2020-07-11", "ListId": "HSKLevel2"}, {"Word": {"Definition": "to try to find; to look for; to call on sb; to find; to seek; to return; to give change", "HSK Level": "2", "Word": "\u627e", "Word-Traditional": "\u627e", "Pronunciation": "zh\u01ceo"}, "Date": "2020-07-12", "ListId": "HSKLevel2"}, {"Word": {"Definition": "family name; surname; name; CL:\u500b|\u4e2a[ge4]", "HSK Level": "2", "Word": "\u59d3", "Word-Traditional": "\u59d3", "Pronunciation": "x\u00ecng"}, "Date": "2020-07-13", "ListId": "HSKLevel2"}, {"Word": {"Definition": "newspaper; newsprint; CL:\u4efd[fen4],\u671f[qi1],\u5f35|\u5f20[zhang1]", "HSK Level": "2", "Word": "\u62a5\u7eb8", "Word-Traditional": "\u5831\u7d19", "Pronunciation": "b\u00e0o zh\u01d0"}, "Date": "2020-07-14", "ListId": "HSKLevel2"}, {"Word": {"Definition": "to wash; to bathe", "HSK Level": "2", "Word": "\u6d17", "Word-Traditional": "\u6d17", "Pronunciation": "x\u01d0"}, "Date": "2020-07-15", "ListId": "HSKLevel2"}],
    "HSKLevel3": [{"Word": {"Definition": "(lead) pencil; CL:\u652f[zhi1],\u679d[zhi1],\u687f|\u6746[gan3]", "HSK Level": "3", "Word": "\u94c5\u7b14", "Word-Traditional": "\u925b\u7b46", "Pronunciation": "qi\u0101n b\u01d0"}, "Date": "2020-07-09", "ListId": "HSKLevel3"}, {"Word": {"Definition": "important; significant; major", "HSK Level": "3", "Word": "\u91cd\u8981", "Word-Traditional": "\u91cd\u8981", "Pronunciation": "zh\u00f2ng y\u00e0o"}, "Date": "2020-07-10", "ListId": "HSKLevel3"}, {"Word": {"Definition": "mouth; classifier for things with mouths (people, domestic animals, cannons, wells etc)", "HSK Level": "3", "Word": "\u53e3", "Word-Traditional": "\u53e3", "Pronunciation": "k\u01d2u"}, "Date": "2020-07-11", "ListId": "HSKLevel3"}, {"Word": {"Definition": "to find; to discover", "HSK Level": "3", "Word": "\u53d1\u73b0", "Word-Traditional": "\u767c\u73fe", "Pronunciation": "f\u0101 xi\u00e0n"}, "Date": "2020-07-12", "ListId": "HSKLevel3"}, {"Word": {"Definition": "to hold; to contain; to grasp; to take hold of; a handle; particle marking the following noun as a direct object; classifier for objects with handle", "HSK Level": "3", "Word": "\u628a", "Word-Traditional": "\u628a", "Pronunciation": "b\u01ce"}, "Date": "2020-07-13", "ListId": "HSKLevel3"}, {"Word": {"Definition": "country; nation; state; CL:\u500b|\u4e2a[ge4]", "HSK Level": "3", "Word": "\u56fd\u5bb6", "Word-Traditional": "\u570b\u5bb6", "Pronunciation": "gu\u00f3 ji\u0101"}, "Date": "2020-07-14", "ListId": "HSKLevel3"}, {"Word": {"Definition": "invoke; pray to; wish; to express good wishes; surname Zhu", "HSK Level": "3", "Word": "\u795d", "Word-Traditional": "\u795d", "Pronunciation": "zh\u00f9"}, "Date": "2020-07-15", "ListId": "HSKLevel3"}],
    "HSKLevel4": [{"Word": {"Definition": "friendly; amicable", "HSK Level": "4", "Word": "\u53cb\u597d", "Word-Traditional": "\u53cb\u597d", "Pronunciation": "y\u01d2u h\u01ceo"}, "Date": "2020-07-09", "ListId": "HSKLevel4"}, {"Word": {"Definition": "to reach; to be enough", "HSK Level": "4", "Word": "\u591f", "Word-Traditional": "\u5920", "Pronunciation": "g\u00f2u"}, "Date": "2020-07-10", "ListId": "HSKLevel4"}, {"Word": {"Definition": "grammar", "HSK Level": "4", "Word": "\u8bed\u6cd5", "Word-Traditional": "\u8a9e\u6cd5", "Pronunciation": "y\u01d4 f\u01ce"}, "Date": "2020-07-11", "ListId": "HSKLevel4"}, {"Word": {"Definition": "belly; abdomen; stomach; CL:\u500b|\u4e2a[ge4]", "HSK Level": "4", "Word": "\u809a\u5b50", "Word-Traditional": "\u809a\u5b50", "Pronunciation": "d\u00f9 zi"}, "Date": "2020-07-12", "ListId": "HSKLevel4"}, {"Word": {"Definition": "success; to succeed; CL:\u6b21[ci4],\u500b|\u4e2a[ge4]", "HSK Level": "4", "Word": "\u6210\u529f", "Word-Traditional": "\u6210\u529f", "Pronunciation": "ch\u00e9ng g\u014dng"}, "Date": "2020-07-13", "ListId": "HSKLevel4"}, {"Word": {"Definition": "to quarrel; to make a noise; noisy; to disturb by making a noise", "HSK Level": "4", "Word": "\u5435", "Word-Traditional": "\u5435", "Pronunciation": "ch\u01ceo"}, "Date": "2020-07-14", "ListId": "HSKLevel4"}, {"Word": {"Definition": "to chat; to gossip", "HSK Level": "4", "Word": "\u804a\u5929", "Word-Traditional": "\u804a\u5929", "Pronunciation": "li\u00e1o ti\u0101n"}, "Date": "2020-07-15", "ListId": "HSKLevel4"}],
    "HSKLevel5": [{"Word": {"Definition": "business; profession; CL:\u500b|\u4e2a[ge4]", "HSK Level": "5", "Word": "\u4e1a\u52a1", "Word-Traditional": "\u696d\u52d9", "Pronunciation": "y\u00e8 w\u00f9"}, "Date": "2020-07-09", "ListId": "HSKLevel5"}, {"Word": {"Definition": "dormitory; dorm room; living quarters; hostel; CL:\u9593|\u95f4[jian1]", "HSK Level": "5", "Word": "\u5bbf\u820d", "Word-Traditional": "\u5bbf\u820d", "Pronunciation": "s\u00f9 sh\u00e8"}, "Date": "2020-07-10", "ListId": "HSKLevel5"}, {"Word": {"Definition": "boss; keeper", "HSK Level": "5", "Word": "\u8001\u677f", "Word-Traditional": "\u8001\u95c6", "Pronunciation": "l\u01ceo b\u01cen"}, "Date": "2020-07-11", "ListId": "HSKLevel5"}, {"Word": {"Definition": "ashamed", "HSK Level": "5", "Word": "\u60ed\u6127", "Word-Traditional": "\u615a\u6127", "Pronunciation": "c\u00e1n ku\u00ec"}, "Date": "2020-07-12", "ListId": "HSKLevel5"}, {"Word": {"Definition": "daily; everyday", "HSK Level": "5", "Word": "\u65e5\u5e38", "Word-Traditional": "\u65e5\u5e38", "Pronunciation": "r\u00ec ch\u00e1ng"}, "Date": "2020-07-13", "ListId": "HSKLevel5"}, {"Word": {"Definition": "president (of a country); CL:\u500b|\u4e2a[ge4],\u4f4d[wei4],\u540d[ming2],\u5c46|\u5c4a[jie4]", "HSK Level": "5", "Word": "\u603b\u7edf", "Word-Traditional": "\u7e3d\u7d71", "Pronunciation": "z\u01d2ng t\u01d2ng"}, "Date": "2020-07-14", "ListId": "HSKLevel5"}, {"Word": {"Definition": "weak; feeble; young; inferior; (following a decimal or fraction) slightly less than", "HSK Level": "5", "Word": "\u5f31", "Word-Traditional": "\u5f31", "Pronunciation": "ru\u00f2"}, "Date": "2020-07-15", "ListId": "HSKLevel5"}],
    "HSKLevel6": [{"Word": {"Definition": "former; original", "HSK Level": "6", "Word": "\u539f\u5148", "Word-Traditional": "\u539f\u5148", "Pronunciation": "yu\u00e1n xi\u0101n"}, "Date": "2020-07-09", "ListId": "HSKLevel6"}, {"Word": {"Definition": "pool; pond", "HSK Level": "6", "Word": "\u6c60\u5858", "Word-Traditional": "\u6c60\u5858", "Pronunciation": "ch\u00ed t\u00e1ng"}, "Date": "2020-07-10", "ListId": "HSKLevel6"}, {"Word": {"Definition": "to clasp; to cup the hands; to hold up with both hands; to offer (esp. in cupped hands); to praise; to flatter", "HSK Level": "6", "Word": "\u6367", "Word-Traditional": "\u6367", "Pronunciation": "p\u011bng"}, "Date": "2020-07-11", "ListId": "HSKLevel6"}, {"Word": {"Definition": "exchanging conventional greetings; to talk about the weather", "HSK Level": "6", "Word": "\u5bd2\u6684", "Word-Traditional": "\u5bd2\u6684", "Pronunciation": "h\u00e1n xu\u0101n"}, "Date": "2020-07-12", "ListId": "HSKLevel6"}, {"Word": {"Definition": "college entrance exam; abbr. for \u666e\u901a\u9ad8\u7b49\u5b78\u6821\u62db\u751f\u5168\u570b\u7d71\u4e00\u8003\u8a66|\u666e\u901a\u9ad8\u7b49\u5b66\u6821\u62db\u751f\u5168\u56fd\u7edf\u4e00\u8003\u8bd5[pu3 tong1 gao1 deng3 xue2 xiao4 zhao1 sheng1 quan2 guo2 tong3 yi1 kao3 shi4]", "HSK Level": "6", "Word": "\u9ad8\u8003", "Word-Traditional": "\u9ad8\u8003", "Pronunciation": "g\u0101o k\u01ceo"}, "Date": "2020-07-13", "ListId": "HSKLevel6"}, {"Word": {"Definition": "kneel", "HSK Level": "6", "Word": "\u8dea", "Word-Traditional": "\u8dea", "Pronunciation": "gu\u00ec"}, "Date": "2020-07-14", "ListId": "HSKLevel6"}, {"Word": {"Definition": "to guide; to lead; to conduct; introduction", "HSK Level": "6", "Word": "\u5f15\u5bfc", "Word-Traditional": "\u5f15\u5c0e", "Pronunciation": "y\u01d0n d\u01ceo"}, "Date": "2020-07-15", "ListId": "HSKLevel6"}]
  }

class WordHistoryTest(unittest.TestCase):

  @mock.patch('get_review_words.app.pull_words_with_params', side_effect=get_words_with_params_mock)
  @mock.patch('get_review_words.app.pull_words_no_params', side_effect=get_words_no_params_mock)
  def test_build(self, no_params_mock, params_mock):

    params = {'list':'HSKLevel1', 'date_range': '10'}

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