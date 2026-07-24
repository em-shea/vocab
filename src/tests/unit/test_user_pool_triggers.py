"""Tests for the four Cognito custom-auth trigger lambdas (passwordless OTP flow)."""
import unittest
from unittest import mock

from create_auth_challenge.app import lambda_handler as create_auth_challenge
from define_auth_challenge.app import lambda_handler as define_auth_challenge
from pre_sign_up.app import lambda_handler as pre_sign_up
from verify_auth_challenge_response.app import lambda_handler as verify_auth_challenge


class PreSignUpTest(unittest.TestCase):
    def test_auto_confirms_user(self):
        event = pre_sign_up({"response": {}}, "")
        self.assertTrue(event["response"]["autoConfirmUser"])


class DefineAuthChallengeTest(unittest.TestCase):
    def _run(self, request):
        return define_auth_challenge({"request": request, "response": {}}, "")

    def test_user_not_found_fails_auth(self):
        response = self._run({"userNotFound": True})["response"]
        self.assertFalse(response["issueTokens"])
        self.assertTrue(response["failAuthentication"])

    def test_no_session_issues_custom_challenge(self):
        response = self._run({"session": []})["response"]
        self.assertFalse(response["issueTokens"])
        self.assertFalse(response["failAuthentication"])
        self.assertEqual(response["challengeName"], "CUSTOM_CHALLENGE")

    def test_correct_code_issues_tokens(self):
        response = self._run({"session": [
            {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": True},
        ]})["response"]
        self.assertTrue(response["issueTokens"])
        self.assertFalse(response["failAuthentication"])

    def test_wrong_code_under_three_attempts_reissues_challenge(self):
        response = self._run({"session": [
            {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": False},
        ]})["response"]
        self.assertFalse(response["issueTokens"])
        self.assertFalse(response["failAuthentication"])
        self.assertEqual(response["challengeName"], "CUSTOM_CHALLENGE")

    def test_three_failed_attempts_fails_auth(self):
        response = self._run({"session": [
            {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": False},
            {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": False},
            {"challengeName": "CUSTOM_CHALLENGE", "challengeResult": False},
        ]})["response"]
        self.assertFalse(response["issueTokens"])
        self.assertTrue(response["failAuthentication"])


class CreateAuthChallengeTest(unittest.TestCase):

    @mock.patch('create_auth_challenge.app.send_notification_email')
    def test_first_attempt_generates_and_emails_code(self, send_mock):
        event = create_auth_challenge({
            "userName": "user1",
            "request": {"session": [], "userAttributes": {"email": "e@test.com"}},
            "response": {},
        }, "")
        response = event["response"]

        self.assertEqual(send_mock.call_count, 1)
        answer = response["privateChallengeParameters"]["answer"]
        self.assertTrue(answer)
        # The code the user must supply is echoed into the challenge metadata.
        self.assertEqual(response["challengeMetadata"], answer)

    @mock.patch('create_auth_challenge.app.send_notification_email')
    def test_repeat_attempt_reuses_existing_code(self, send_mock):
        event = create_auth_challenge({
            "userName": "user1",
            "request": {
                "session": [{"challengeMetadata": "CODE123"}],
                "userAttributes": {"email": "e@test.com"},
            },
            "response": {},
        }, "")

        # No new email on retry; the original code is reused.
        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(event["response"]["privateChallengeParameters"]["answer"], "CODE123")


class VerifyAuthChallengeResponseTest(unittest.TestCase):

    def _event(self, challenge_answer):
        return {
            "userPoolId": "us-east-1_testpool",
            "userName": "user1",
            "request": {
                "privateChallengeParameters": {"answer": "EXPECTED"},
                "challengeAnswer": challenge_answer,
                "session": [],
            },
            "response": {},
        }

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_correct_answer_marks_email_verified(self, cognito_mock):
        event = verify_auth_challenge(self._event("EXPECTED"), "")

        self.assertTrue(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 1)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_incorrect_answer_is_rejected(self, cognito_mock):
        event = verify_auth_challenge(self._event("WRONG"), "")

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)


if __name__ == '__main__':
    unittest.main()
