import sys
sys.path.append('../../')
sys.path.append('../../layer/python')

import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'DYNAMODB_TABLE_NAME': 'mock-table'}):
    import user_service

def mocked_pull_user_data(user_id):

  return [
    {
        "Date subscribed":"2021-06-16T23:07:11.648212",
        "GSI1PK":"USER",
        "List name":"HSK Level 3",
        "SK":"LIST#123",
        "Status":"SUBSCRIBED",
        "GSI1SK":"USER#123#LIST#123#SIMPLIFIED",
        "PK":"USER#123",
        "Character set":"simplified"
    },
    {
        "Date subscribed":"2021-07-04T18:46:41.371527",
        "GSI1PK":"USER",
        "List name":"HSK Level 6",
        "SK":"LIST#234",
        "Status":"SUBSCRIBED",
        "GSI1SK":"USER#123#LIST#234#SIMPLIFIED",
        "PK":"USER#123",
        "Character set":"simplified"
    },
    {
        "GSI1PK":"USER",
        "Date created":"2021-06-16T23:07:11.623880",
        "Character set preference":"simplified",
        "SK":"USER#123",
        "Email address":"test@mail.com",
        "User alias":"Not set",
        "User alias pinyin":"Not set",
        "GSI1SK":"USER#123",
        "PK":"USER#123"
    }
  ]

class UserServiceTest(unittest.TestCase):

  @mock.patch('user_service.pull_user_data', side_effect=mocked_pull_user_data)
  def test_build(self, pull_user_data_mock):

    cognito_id = "1234"
    response = user_service.get_user_data(cognito_id)
    print(response)

    self.assertEqual(pull_user_data_mock.call_count, 1)

if __name__ == '__main__':
    unittest.main()


