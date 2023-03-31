"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase
from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Sets up the test client and creates sample data"""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testmsg = self.testuser.messages.append(
            (Message(text="this is a test")))

        db.session.commit()

    def tearDown(self):
        """Cleans up after each test case"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_and_delete_message(self):
        """Tests if a user can add and delete a message"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # check that msg = the client's msg
            msg2 = Message.query.filter_by(
                user_id=self.testuser.id).offset(1).first()
            self.assertEqual(msg2.text, "Hello")

            # delete the msg and check for proper status code
            resp = c.post(f"/messages/{msg2.id}/delete")
            self.assertEqual(resp.status_code, 302)

            # query the deleted message and check if it is deleted
            msg = Message.query.get(msg2.id)
            self.assertIsNone(msg)

    def test_following_views(self):
        """Tests if the following page renders properly"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp = c.get(f"/users/{self.testuser.id}/following")

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'<p class="small">Following</p>', resp.data)

    def test_followers_views(self):
        """Tests if the followers page renders properly"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp = c.get(f"/users/{self.testuser.id}/followers")

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'<p class="small">Followers</p>', resp.data)

    def test_logged_out_access(self):
        """Tests if a logged out user can access the following and followers pages"""
        with self.client as c:
            # mimic a logout by clearing session
            with c.session_transaction() as sess:
                sess.clear()

            # logged out user attempts to go to followers
            # sends user to home page due to not being authorized
            resp = c.get(f"/users/{self.testuser.id}/followers")
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/", resp.location)

            # logged out user attempts to go to following
            # sends user to home page due to not being authorized
            resp = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/", resp.location)

    def test_logged_out_add_delete_message(self):
        """Tests if a logged out user can add or delete a message"""

        with self.client as c:
            # mimic a logout by clearing session
            with c.session_transaction() as sess:
                sess.clear()

            count_before = Message.query.count()
            # logged out user trys to make a message
            resp = c.post("/messages/new", data={"text": "Hello"})
            count_after = Message.query.count()
            self.assertEqual(count_before, count_after)

            # Make sure it redirects and does not post
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/", resp.location)

            msg = Message.query.one()

            # delete the msg and check for proper status code
            resp = c.post(f"/messages/{msg.id}/delete")
            self.assertEqual(resp.status_code, 302)

            # Make sure it redirects and does not post
            self.assertIn("/", resp.location)

            # check to see if there's still a message
            self.assertIsNotNone(msg)

    def test_cannot_add_message_as_another_user(self):
        """Tests if a user can add a message as another user"""

        user1 = User(
            username="user1",
            email="user1@test.com",
            password="password"
        )

        user2 = User(
            username="user2",
            email="user2@test.com",
            password="password"
        )

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # log in as user1
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user1.id

        # try to add a message as user2
        with self.client.session_transaction() as sess:
            sess[CURR_USER_KEY] = user2.id
            resp = self.client.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/", resp.location)

            msg = Message.query.filter_by(
                user_id=self.testuser.id).first()

            # try to delete a message as user2
            resp = self.client.post(f"/messages/{msg.id}/delete")
            self.assertEqual(resp.status_code, 302)
            self.assertIn("/", resp.location)

            self.assertIsNotNone(msg)
