"""Auth tests - hashing/JWT."""
# pylint: disable=missing-class-docstring
import unittest
from datetime import timedelta, datetime

from auth import hashing
from auth.jwt import JwtTokenUtils
from models.user import UserView, UserCapability
from tests.utils import TestTimeProvider


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.token_utils = JwtTokenUtils(
            secret_key="testing secret key",
            access_token_expiry=timedelta(minutes=60),
        )

    def test_passwords(self):
        """Ensure password hashing and verification is working"""
        pwd = "test password..."
        hashed = hashing.hash_password(pwd)
        is_same = hashing.verify_password(pwd, hashed)
        self.assertTrue(is_same)
        self.assertNotEqual(hashed, pwd)

    def test_token_encodes_user(self):
        """Token encodes username correctly"""
        username = "test user name"
        user = UserView(
            username=username,
            capabilities=[UserCapability.SERVER_MANAGEMENT],
        )

        token = self.token_utils.create_access_token(user)

        username_from_token = self.token_utils.get_user(token)

        self.assertEqual(user, username_from_token)

    def test_token_duration(self):
        """Ensures token duration is validated"""
        expiry_time = timedelta(minutes=10)
        time_provider = TestTimeProvider(datetime.now() - timedelta(minutes=15))
        token_utils = JwtTokenUtils(
            secret_key="testing secret key",
            access_token_expiry=expiry_time,
            time_provider=time_provider
        )
        name = "test user"
        user = UserView(
            username=name,
            capabilities=[]
        )

        # token1 is 5 minutes expired when checked
        token1 = token_utils.create_access_token(user)

        # note: implementation of get_user always checks expiration against
        #   current datetime, not against time provider one.
        user_from_token1 = token_utils.get_user(token1)
        self.assertEqual(None, user_from_token1)

        time_provider.pass_time(timedelta(minutes=10))

        # token2 still has 5 minutes of lifetime
        token2 = token_utils.create_access_token(user)
        user_from_token2 = token_utils.get_user(token2)
        self.assertEqual(user, user_from_token2)
        self.assertEqual(None, user_from_token1)
