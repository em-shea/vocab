import sys
sys.path.append('../../')

import os
import json
import unittest
from unittest import mock
from io import BytesIO

# done

from layer import vocab_random_word

print('starting test')

def mocked_get_s3_file():

  csv_file = "example_words_list.csv"
  with open(csv_file) as fh:
    contents = fh.read()

  return contents

class VocabRandomWordTest(unittest.TestCase):

  @mock.patch('layer.vocab_random_word.get_s3_file', side_effect=mocked_get_s3_file)
  def test_build(self, s3_get_file_mock):
    
    hsk_level = 2

    response = vocab_random_word.select_random_word(hsk_level)

    self.assertEqual(s3_get_file_mock.call_count, 1)
    self.assertEqual(response['HSK Level'], "2")
  
  @mock.patch('layer.vocab_random_word.get_s3_file', side_effect=mocked_get_s3_file)
  def test_input_fail(self, s3_get_file_mock):
    
    hsk_level = "invalid hsk_level format"

    response = vocab_random_word.select_random_word(hsk_level)
    print("response: ", response)

    self.assertEqual(s3_get_file_mock.call_count, 0)
    self.assertEqual(response, "Invalid HSK level. HSK level should be a string representing an integer between 1 and 6.")

if __name__ == '__main__':
    unittest.main()


