import json
import unittest
from unittest import mock

from set_quiz_results.app import lambda_handler


def _event(body):
    return {
        "resource": "/quizzes",
        "httpMethod": "POST",
        "requestContext": {"authorizer": {"claims": {"sub": "user-123"}}},
        "body": body,
    }


QUIZ_BODY = {
    "quiz_data": [{"was_answer_correct": True}],
    "list_id": "123",
    "character_set": "simplified",
    "question_quantity": 10,
    "correct_answers": 8,
}


class SetQuizResultsTest(unittest.TestCase):

    @mock.patch('set_quiz_results.app.put_quiz_result')
    def test_build(self, put_quiz_result_mock):
        response = lambda_handler(_event(json.dumps(QUIZ_BODY)), "")
        body = json.loads(response["body"])

        self.assertEqual(put_quiz_result_mock.call_count, 1)
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(body["success"])
        # The handler generates a quiz_id and forwards the cognito sub + body to the writer.
        called_id, called_body, _date = put_quiz_result_mock.call_args.args
        self.assertEqual(called_id, "user-123")
        self.assertNotEqual(called_body["quiz_id"], "")

    @mock.patch('set_quiz_results.app.put_quiz_result', side_effect=Exception("dynamo down"))
    def test_put_failure_returns_502(self, put_quiz_result_mock):
        response = lambda_handler(_event(json.dumps(QUIZ_BODY)), "")
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 502)
        self.assertFalse(body["success"])


if __name__ == '__main__':
    unittest.main()
