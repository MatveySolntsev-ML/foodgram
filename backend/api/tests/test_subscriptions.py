from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class SubscriptionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="follower", email="f@example.com", password="x",
            first_name="F", last_name="F",
        )
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="x",
            first_name="A", last_name="A",
        )
        self.client.force_authenticate(user=self.user)

    def test_subscribe(self):
        response = self.client.post(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], self.author.id)
        self.assertTrue(response.data["is_subscribed"])

    def test_cannot_subscribe_twice(self):
        self.client.post(f"/api/users/{self.author.id}/subscribe/")
        response = self.client.post(f"/api/users/{self.author.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_subscribe_to_self(self):
        response = self.client.post(f"/api/users/{self.user.id}/subscribe/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe(self):
        url = f"/api/users/{self.author.id}/subscribe/"
        self.client.post(url)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unsubscribe_when_not_subscribed_404(self):
        url = f"/api/users/{self.author.id}/subscribe/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_subscriptions(self):
        self.client.post(f"/api/users/{self.author.id}/subscribe/")
        response = self.client.get("/api/users/subscriptions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.author.id)
