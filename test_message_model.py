"""User model tests."""
from app import app
import os
from sqlalchemy.exc import IntegrityError
from unittest import TestCase
from models import db, User, Message, Follows, Likes

# run these tests like:
#
#    python -m unittest test_user_model.py


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
os.environ.get('DATABASE_URL_TEST', 'postgresql:///warbler_test')


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()
        self.client = app.test_client()
        self.u1, self.u2 = self._create_users()
        self.msg1, self.msg2 = self._create_messages()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def _create_users(self):
        u1 = User.signup("test1", "email1@email.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        return u1, u2

    def _create_messages(self):
        msg1 = Message(text="test message!", user_id=self.u1.id)
        msg2 = Message(text="test2 message2!", user_id=self.u2.id)

        db.session.add_all([msg1, msg2])
        db.session.commit()

        return msg1, msg2

    def test_add_message(self):
        """Does making a message work"""

        self.assertIsNotNone(self.msg1)
        self.assertEqual(self.msg1.text, "test message!")
        self.assertIsNotNone(self.msg2)
        self.assertEqual(self.msg2.text, "test2 message2!")

    def test_like_message(self):
        """Does liking a message work as intended"""
        self.u1.likes.append(self.msg2)
        self.u2.likes.append(self.msg1)
        db.session.commit()

        likes1 = Likes.query.filter_by(message_id=self.msg1.id).first()
        likes2 = Likes.query.filter_by(message_id=self.msg2.id).first()

        self.assertIsNotNone(likes1)
        self.assertIsNotNone(likes2)

    def test_remove_like_from_msg(self):
        """Does removing a like from a message work as intended"""
        self.u1.likes.append(self.msg2)
        self.u2.likes.append(self.msg1)
        db.session.commit()

        self.u1.likes.remove(self.msg2)
        self.u2.likes.remove(self.msg1)
        db.session.commit()

        likes1 = Likes.query.filter_by(message_id=self.msg1.id).first()
        likes2 = Likes.query.filter_by(message_id=self.msg2.id).first()

        self.assertIsNone(likes1)
        self.assertIsNone(likes2)

    def test_destroy_message(self):
        """Does removing a message work as intended"""
        db.session.delete(self.msg1)
        db.session.delete(self.msg2)
        db.session.commit()

        msg1 = Message.query.get(1)
        msg2 = Message.query.get(2)

        self.assertIsNone(msg1)
        self.assertIsNone(msg2)
