"""User model tests."""
import os
from sqlalchemy.exc import IntegrityError
from unittest import TestCase
from models import db, User, Message, Follows

# run these tests like:
#
#    python -m unittest test_user_model.py

app.testing = True
# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ.get('DATABASE_URL_TEST', 'postgresql:///warbler_test'))


# Now we can import app
from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.signup("test1", "email1@email.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        db.session.commit()

        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="2@2.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        # Does the repr method work as expected?
        self.assertEqual(
            repr(self.u1), (f"<User #{self.u1.id}: {self.u1.username}, {self.u1.email}>"))

    def test_following_and_followed_by(self):
        self.u2.following.append(self.u1)
        db.session.commit()

        # Does is_following successfully detect when users do/don't follow another user?
        # u is not following u2 = False
        self.assertFalse(self.u1.is_following(self.u2))
        # u2 is following u = 1
        self.assertEqual(self.u2.is_following(self.u1), 1)

        # Does the is_followed_by method correctly detect if a given user is followed by another user?
        # u is followed by u2 = 1
        self.assertEqual(self.u1.is_followed_by(self.u2), 1)
        # u2 is not followed by u = False
        self.assertFalse(self.u2.is_followed_by(self.u1))

    def test_signup(self):
        # Does User.create successfully create a new user given valid credentials?
        WILL = User.signup("WILL", "WILLY", "WILL@gmail.com", None)
        db.session.commit()

        self.assertIsNotNone(WILL)  # Make sure user exists
        self.assertEqual(
            repr(WILL), (f"<User #{WILL.id}: {WILL.username}, {WILL.email}>"))

        # # Try to create a new user with invalid credentials
        with self.assertRaises(IntegrityError):
            User.signup(username=self.u1.username, password="password",
                        email="email@test.com", image_url="None")
            db.session.commit()

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
