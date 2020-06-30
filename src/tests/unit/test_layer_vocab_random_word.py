import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock

with mock.patch.dict('os.environ', {'AWS_REGION': 'us-east-1', 'WORDS_BUCKET_NAME': 'mock-bucket-name', 'WORDS_BUCKET_KEY': 'mock-bucket-key'}):
  from layer.vocab_random_word import select_random_word

def mocked_get_s3_file():
  
  # get contents from example_words_list.py

  return csv_file

class VocabRandomWordTest(unittest.TestCase):

  @mock.patch('backup_dynamo_s3.app.write_to_s3', side_effect=mocked_get_s3_file)
  def test_build(self, s3_get_file_mock):
    
    response = lambda_handler(self.scheduled_event(), "")

    self.assertEqual(s3_get_file_mock.call_count, 1)

  def scheduled_event(self):
    {
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


