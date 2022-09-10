import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import unittest
from unittest import mock

# wip
# No such file or directory: 'template.html'

# test cases:
# a user with no lists (unsubscribed from all)

# with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'TABLE_NAME': 'mock-table', 'ANNOUNCEMENTS_BUCKET': 'mock-bucket', 'WORDS_BUCKET_NAME': 'mock-words-bucket', 'WORDS_BUCKET_KEY': 'mock-words-key'}):
#   from send_daily_email.app import lambda_handler

# def mocked_get_announcement():
#   return None

# def mocked_store_words(word_list):
#   return

# def mocked_send_email(campaign_contents, email):

#   ses_success_response = {
#         "MessageId":"010001731670746b-123456-6e8c-4bd0-bf32-4238ba0e5921-000000",
#         "ResponseMetadata":{
#             "RequestId":"ab476c36-de5a-123a-a90e-6be7b103b68f",
#             "HTTPStatusCode":200,
#             "HTTPHeaders":{
#                 "x-amzn-requestid":"ab476c36-de5a-123a-a90e-6be7b103b68f",
#                 "content-type":"text/xml",
#                 "content-length":"326",
#                 "date":"Fri, 03 Jul 2020 20:48:54 GMT"
#             },
#             "RetryAttempts":0
#         }
#     }

#   return ses_success_response

# def mocked_query_all_users():

#   return [
#     {'GSI1PK': 'USER', 'Date created': '2021-06-16T23:06:48.467526', 'Character set preference': 'traditional', 'SK': 'USER#770e2827-7666-4087-9c58-17c2e862dba2', 'Email address': 'test1@gmail.com', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e862dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e862dba2', 'User alias': '小陈', 'User alias pinyin': 'xiǎo chén', 'User alias emoji': '🪃'}, 
#     {'GSI1PK': 'USER', 'Date subscribed': '2021-06-16T23:06:48.646688', 'List name': 'HSK Level 6', 'SK': 'LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Status': 'subscribed', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e862dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e862dba2#LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Character set': 'traditional'}, 
#     {'GSI1PK': 'USER', 'Date created': '2021-06-16T23:07:11.623880', 'Character set preference': 'simplified', 'SK': 'USER#ef602513-011c-481e-9825-e1e7ad39c3d3', 'Email address': 'test2@gmail.com', 'PK': 'USER#ef602513-011c-481e-9825-e1e7ad39c3d3', 'GSI1SK': 'USER#ef602513-011c-481e-9825-e1e7ad39c3d3', 'User alias': '小王', 'User alias pinyin': 'xiǎo wáng', 'User alias emoji': '🧯'}, 
#     {'GSI1PK': 'USER', 'Date subscribed': '2021-06-16T23:07:11.648212', 'List name': 'HSK Level 3', 'SK': 'LIST#1ebcad3f-f815-6b92-b3e8-acde48001122#TRADITIONAL', 'Status': 'unsubscribed', 'PK': 'USER#ef602513-011c-481e-9825-e1e7ad39c3d3', 'GSI1SK': 'USER#ef602513-011c-481e-9825-e1e7ad39c3d3#LIST#1ebcad3f-f815-6b92-b3e8-acde48001122#SIMPLIFIED', 'Character set': 'simplified'},
#     {'GSI1PK': 'USER', 'Date created': '2021-06-16T23:06:48.467526', 'Character set preference': 'traditional', 'SK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'Email address': 'test3@gmail.com', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'User alias': '小琳', 'User alias pinyin': 'xiǎo lín', 'User alias emoji': '🥷'}, 
#     {'GSI1PK': 'USER', 'Date subscribed': '2021-06-16T23:06:48.646688', 'List name': 'HSK Level 6', 'SK': 'LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Status': 'subscribed', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2#LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Character set': 'traditional'}, 
#     {'GSI1PK': 'USER', 'Date subscribed': '2021-06-16T23:06:48.646688', 'List name': 'HSK Level 2', 'SK': 'LIST#1ebcad3f-adc0-6f42-b8b1-acde48001122#TRADITIONAL', 'Status': 'unsubscribed', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2#LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Character set': 'traditional'},
#     {'GSI1PK': 'USER', 'Date subscribed': '2021-06-16T23:06:48.646688', 'List name': 'HSK Level 1', 'SK': 'LIST#1ebcad3f-5dfd-6bfe-bda4-acde48001122#TRADITIONAL', 'Status': 'subscribed', 'PK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2', 'GSI1SK': 'USER#770e2827-7666-4087-9c58-17c2e123dba2#LIST#1ebcad41-197a-6700-95a3-acde48001122#TRADITIONAL', 'Character set': 'traditional'}
#   ]

# def mocked_get_words_in_list(list_id):

#   return [
#    {
#       "list_id":"LIST#1ebcad3f-f815-6b92-b3e8-acde48001122",
#       "word_id":"WORD#1ec4a4cc-4283-6e50-b218-acde48001122",
#       "word":{
#          "Simplified":"阿姨",
#          "Pinyin":"ā yí",
#          "Definition":"maternal aunt; step-mother; childcare worker; nursemaid; woman of similar age to one's parents (term of address used by child); CL:個|个 gè",
#          "HSK Level":"3",
#          "Traditional":"阿姨",
#          "Difficulty level":"Intermediate",
#          "Audio file key":""
#       }
#    },
#    {
#       "list_id":"LIST#1ebcad3f-f815-6b92-b3e8-acde48001122",
#       "word_id":"WORD#1ec4a4cc-4284-603a-b218-acde48001122",
#       "word":{
#          "Simplified":"啊",
#          "Pinyin":"a",
#          "Definition":"modal particle ending sentence, showing affirmation, approval, or consent",
#          "HSK Level":"3",
#          "Traditional":"啊",
#          "Difficulty level":"Intermediate",
#          "Audio file key":""
#       }
#    },
#    {
#       "list_id":"LIST#1ebcad3f-f815-6b92-b3e8-acde48001122",
#       "word_id":"WORD#1ec4a4cc-4284-60e4-b218-acde48001122",
#       "word":{
#          "Simplified":"矮",
#          "Pinyin":"ǎi",
#          "Definition":"low; short (in length)",
#          "HSK Level":"3",
#          "Traditional":"矮",
#          "Difficulty level":"Intermediate",
#          "Audio file key":""
#       }
#    },
#    {
#       "list_id":"LIST#1ebcad3f-f815-6b92-b3e8-acde48001122",
#       "word_id":"WORD#1ec4a4cc-4284-6166-b218-acde48001122",
#       "word":{
#          "Simplified":"爱好",
#          "Pinyin":"ài hào",
#          "Definition":"to like; to take pleasure in; keen on; fond of; interest; hobby; appetite for; CL:個|个 gè",
#          "HSK Level":"3",
#          "Traditional":"愛好",
#          "Difficulty level":"Intermediate",
#          "Audio file key":""
#       }
#    },
#    {
#       "list_id":"LIST#1ebcad3f-f815-6b92-b3e8-acde48001122",
#       "word_id":"WORD#1ec4a4cc-4284-61d4-b218-acde48001122",
#       "word":{
#          "Simplified":"安静",
#          "Pinyin":"ān jìng",
#          "Definition":"quiet; peaceful; calm",
#          "HSK Level":"3",
#          "Traditional":"安靜",
#          "Difficulty level":"Intermediate",
#          "Audio file key":""
#       }
#    }
# ]

# class SendDailyEmailTest(unittest.TestCase):

#   @mock.patch('send_daily_email.app.get_announcement', side_effect=mocked_get_announcement)
#   @mock.patch('user_service.query_all_users', side_effect=mocked_query_all_users)
#   @mock.patch('list_word_service.get_words_in_list', side_effect=mocked_get_words_in_list)
#   @mock.patch('send_daily_email.app.store_words', side_effect=mocked_store_words)
#   @mock.patch('send_daily_email.app.send_email', side_effect=mocked_send_email)
#   def test_build(self, send_email_mock, store_words_mock, get_words_in_list_mock, query_all_users_mock, get_announcement_mock):

#     response = lambda_handler(self.scheduled_event(), "")

#     self.assertEqual(get_announcement_mock.call_count, 1)
#     self.assertEqual(store_words_mock.call_count, 1)
#     self.assertEqual(query_all_users_mock.call_count, 1)
#     self.assertEqual(get_words_in_list_mock.call_count, 6)
#     self.assertEqual(send_email_mock.call_count, 2)

#   def scheduled_event(self):
#     return {
#       "version": "0",
#       "id": "d77bcbc4-0b2b-4d45-9694-b1df99175cfb",
#       "detail-type": "Scheduled Event",
#       "source": "aws.events",
#       "account": "123456789",
#       "time": "2016-09-25T04:55:26Z",
#       "region": "us-east-1",
#       "resources": [
#         "arn:aws:events:us-east-1:123456789:rule/test-scheduled-event"
#       ],
#       "detail": {}
#     }

# if __name__ == '__main__':
#     unittest.main()