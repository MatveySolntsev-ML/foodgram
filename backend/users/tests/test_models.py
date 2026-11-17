from django.db import IntegrityError
from django.test import TestCase

from users.models import Subscription, User


class UserModelTests(TestCase):
    def test_create_user_by_email(self):
        user = User.objects.create_user(
            username="vasya",
            email="vasya@example.com",
            password="Qwerty123",
            first_name="Вася",
            last_name="Иванов",
        )
        self.assertEqual(user.email, "vasya@example.com")
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="vasya", email="dup@example.com", password="x",
            first_name="V", last_name="I",
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="petya", email="dup@example.com", password="x",
                first_name="P", last_name="P",
            )


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="follower", email="f@example.com", password="x",
            first_name="F", last_name="F",
        )
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="x",
            first_name="A", last_name="A",
        )

    def test_subscribe(self):
        sub = Subscription.objects.create(user=self.user, author=self.author)
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.author, self.author)

    def test_duplicate_subscription_rejected(self):
        Subscription.objects.create(user=self.user, author=self.author)
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(user=self.user, author=self.author)
