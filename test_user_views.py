"""User model tests."""

from app import app, do_login, CURR_USER_KEY
from sqlalchemy.exc import IntegrityError
from unittest import TestCase
from models import db, User, Message, Follows


db.create_all()


class UserViewsTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        """Sets up the test client and creates sample data"""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                     email="test2@test.com",
                                     password="testuser",
                                     image_url=None)

        self.testuser.following.append(self.testuser2)

        self.testmsg = self.testuser.messages.append(
            (Message(text="this is a test")))

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_logout(self):
        """Test login with valid credentials."""

        # Make a POST request to the login route with valid credentials
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/logout")
            self.assertEqual(resp.status_code, 302)
            self.assertIn(
                b'<a href="/login">/login</a>', resp.data)

    def test_users_view(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                b'<button class="btn btn-outline-primary btn-sm">Follow</button>', resp.data)

    def test_users_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.testuser.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                f'<a href="/users/{self.testuser.id}">@{self.testuser.username}</a>'.encode(),
                resp.data
            )

    def test_stop_following(self):
        """Test that a user can stop following another user."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/stop-following/{self.testuser2.id}")
            self.assertEqual(resp.status_code, 302)

            user = User.query.get(self.testuser.id)
            self.assertNotIn(self.testuser2, user.following)

            followed_user = User.query.get(self.testuser2.id)
            self.assertNotIn(self.testuser, followed_user.followers)

    def test_edit_profile(self):
        """Test that a user can edit their profile."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser2.id

            resp = c.post("/users/profile", data={
                'username': 'testuser2',
                'email': 'test2@test.com',
                'image_url': '',
                'header_image_url': '',
                'bio': '',
                'password': 'testuser'
            })

            self.assertEqual(resp.status_code, 200)

            user = User.query.get(self.testuser2.id)
            self.assertEqual(user.username, 'testuser2')
            self.assertEqual(user.email, 'test2@test.com')
