"""Tests for the four Cognito custom-auth trigger lambdas (passwordless OTP flow)."""
import os
import time
import unittest
from unittest import mock

import jwt

from create_auth_challenge.app import lambda_handler as create_auth_challenge
from define_auth_challenge.app import lambda_handler as define_auth_challenge
from pre_sign_up.app import lambda_handler as pre_sign_up
from verify_auth_challenge_response.app import lambda_handler as verify_auth_challenge

# Set by conftest.py before the handlers import.
OTP_SECRET = os.environ['OTP_SECRET_KEY']


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
        # Security: the secret code must NOT leak via publicChallengeParameters,
        # which are returned to the unauthenticated client.
        self.assertNotIn("answer", response["publicChallengeParameters"])
        self.assertNotIn(answer, response["publicChallengeParameters"].values())

    @mock.patch('create_auth_challenge.app.send_notification_email')
    def test_code_carries_an_expiry_and_binds_the_username(self, send_mock):
        event = create_auth_challenge({
            "userName": "user1",
            "request": {"session": [], "userAttributes": {"email": "e@test.com"}},
            "response": {},
        }, "")
        answer = event["response"]["privateChallengeParameters"]["answer"]

        claims = jwt.decode(answer, OTP_SECRET, algorithms=["HS256"])
        self.assertEqual(claims["u"], "user1")
        # Regression: the payload used to be a bare {'u': username} with no exp,
        # so a user's code never changed and never expired.
        self.assertIn("exp", claims)
        self.assertEqual(claims["exp"] - claims["iat"], 600)

    @mock.patch('create_auth_challenge.app.send_notification_email')
    def test_each_sign_in_generates_a_different_code(self, send_mock):
        def _new_code():
            event = create_auth_challenge({
                "userName": "user1",
                "request": {"session": [], "userAttributes": {"email": "e@test.com"}},
                "response": {},
            }, "")
            return event["response"]["privateChallengeParameters"]["answer"]

        # The nonce is what stops one intercepted code working forever.
        self.assertNotEqual(_new_code(), _new_code())

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

    def _code(self, username="user1", ttl=600, key=None):
        issued_at = int(time.time())
        return jwt.encode(
            {"u": username, "iat": issued_at, "exp": issued_at + ttl, "jti": "nonce"},
            key or OTP_SECRET,
            algorithm="HS256",
        )

    def _event(self, challenge_answer, expected_answer=None, user_name="user1"):
        return {
            "userPoolId": "us-east-1_testpool",
            "userName": user_name,
            "request": {
                "privateChallengeParameters": {
                    "answer": expected_answer if expected_answer is not None else challenge_answer
                },
                "challengeAnswer": challenge_answer,
                "session": [],
            },
            "response": {},
        }

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_correct_answer_marks_email_verified(self, cognito_mock):
        event = verify_auth_challenge(self._event(self._code()), "")

        self.assertTrue(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 1)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_incorrect_answer_is_rejected(self, cognito_mock):
        event = verify_auth_challenge(
            self._event("WRONG", expected_answer=self._code()), ""
        )

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_expired_code_is_rejected(self, cognito_mock):
        # Matches the challenge exactly, so a plain string compare would accept it.
        # Only decoding the token catches that it has expired.
        expired = self._code(ttl=-1)

        event = verify_auth_challenge(self._event(expired), "")

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_code_issued_for_another_user_is_rejected(self, cognito_mock):
        other_users_code = self._code(username="user2")

        event = verify_auth_challenge(
            self._event(other_users_code, user_name="user1"), ""
        )

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_code_signed_with_the_wrong_key_is_rejected(self, cognito_mock):
        forged = self._code(key="not-the-real-secret")

        event = verify_auth_challenge(self._event(forged), "")

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)

    @mock.patch('verify_auth_challenge_response.app.cognito_client')
    def test_empty_answer_is_rejected(self, cognito_mock):
        event = verify_auth_challenge(self._event("", expected_answer=""), "")

        self.assertFalse(event["response"]["answerCorrect"])
        self.assertEqual(cognito_mock.admin_update_user_attributes.call_count, 0)


if __name__ == '__main__':
    unittest.main()
