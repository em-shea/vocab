import sys
sys.path.append('../../')
sys.path.append('../../layer')

import os
import json
import unittest
from unittest import mock

# wip
# No such file or directory: 'template.html'

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table', 'CONTACT_TABLE_NAME': 'mock-contact-table'}):
  from send_daily_email.app import lambda_handler

def mocked_store_words(word_list):
  return

def mocked_send_email(campaign_contents, email):

  ses_success_response = {
        "MessageId":"010001731670746b-123456-6e8c-4bd0-bf32-4238ba0e5921-000000",
        "ResponseMetadata":{
            "RequestId":"ab476c36-de5a-123a-a90e-6be7b103b68f",
            "HTTPStatusCode":200,
            "HTTPHeaders":{
                "x-amzn-requestid":"ab476c36-de5a-123a-a90e-6be7b103b68f",
                "content-type":"text/xml",
                "content-length":"326",
                "date":"Fri, 03 Jul 2020 20:48:54 GMT"
            },
            "RetryAttempts":0
        }
    }

  return ses_success_response

def mocked_scan_contacts():

  all_contacts = [
    {'Date': '2020-01-13', 'CharacterSet': 'simplified', 'Status': 'subscribed', 'SubscriberEmail': 'user@example.com', 'ListId': '1'},
    {'Date': '2020-01-13', 'CharacterSet': 'simplified', 'Status': 'unsubscribed', 'SubscriberEmail': 'user@example.com', 'ListId': '6'},
    {'Date': '2020-01-13', 'CharacterSet': 'traditional', 'Status': 'subscribed', 'SubscriberEmail': 'user@example.com', 'ListId': '4'},
    {'Date': '2020-01-13', 'CharacterSet': 'traditional', 'Status': 'unsubscribed', 'SubscriberEmail': 'user@example.com', 'ListId': '3'}
  ]

  return all_contacts

def mocked_get_random(hsk_level):
  
  hsk_level_index = int(hsk_level) - 1

  local_vocab_lists = [
      {
        "Word": "怎么样",
        "Pronunciation": "zěn me yàng",
        "Definition": "how?; how about?; how was it?; how are things?",
        "HSK Level": "1",
        "Word-Traditional": "怎麼樣"
      },
      {
        "Word": "回答",
        "Pronunciation": "huí dá",
        "Definition": "to reply; to answer; the answer; CL:個|个[ge4]",
        "HSK Level": "2",
        "Word-Traditional": "回答"
      },
      {
        "Word": "腿",
        "Pronunciation": "tuǐ",
        "Definition": "leg; CL:條|条[tiao2]",
        "HSK Level": "3",
        "Word-Traditional": "腿"
      },
      {
        "Word": "乱",
        "Pronunciation": "luàn",
        "Definition": "in confusion or disorder; in a confused state of mind; disorder; upheaval; riot; illicit sexual relations; to throw into disorder; to mix up; indiscriminate; random; arbitrary",
        "HSK Level": "4",
        "Word-Traditional": "亂"
      },
      {
        "Word": "叉子",
        "Pronunciation": "chā zi",
        "Definition": "fork; CL:把[ba3]",
        "HSK Level": "5",
        "Word-Traditional": "叉子"
      },
      {
        "Word": "注视",
        "Pronunciation": "zhù shì",
        "Definition": "to watch attentively; to gaze",
        "HSK Level": "6",
        "Word-Traditional": "注視"
      }
    ]

  return local_vocab_lists[hsk_level_index]

class SendDailyEmailTest(unittest.TestCase):

  @mock.patch('send_daily_email.app.scan_contacts_table', side_effect=mocked_scan_contacts)
  @mock.patch('send_daily_email.app.select_random_word', side_effect=mocked_get_random)
  @mock.patch('send_daily_email.app.send_email', side_effect=mocked_send_email)
  def test_build(self, send_email_mock, get_random_mock, scan_contacts_mock):

    response = lambda_handler(self.scheduled_event(), "")

    self.assertEqual(scan_contacts_mock.call_count, 1)
    self.assertEqual(get_random_mock.call_count, 6)
    self.assertEqual(send_email_mock.call_count, 2)

  def scheduled_event(self):
    return {
      "version": "0",
      "id": "d77bcbc4-0b2b-4d45-9694-b1df99175cfb",
      "detail-type": "Scheduled Event",
      "source": "aws.events",
      "account": "123456789",
      "time": "2016-09-25T04:55:26Z",
      "region": "us-east-1",
      "resources": [
        "arn:aws:events:us-east-1:123456789:rule/test-scheduled-event"
      ],
      "detail": {}
    }

if __name__ == '__main__':
    unittest.main()