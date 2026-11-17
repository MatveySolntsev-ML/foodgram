from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACV"
    "BMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAgg"
    "CByxOyYQAAAABJRU5ErkJggg=="
)


class UserRegistrationTests(APITestCase):
    def test_register_and_login(self):
        response = self.client.post(
            "/api/users/",
            {
                "email": "vasya@example.com",
                "username": "vasya",
                "first_name": "Вася",
                "last_name": "Иванов",
                "password": "FoodgramPass123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)

        login = self.client.post(
            "/api/auth/token/login/",
            {"email": "vasya@example.com", "password": "FoodgramPass123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("auth_token", login.data)


class CurrentUserEndpointTests(APITestCase):
    def test_me_requires_authentication(self):
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AvatarEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="vasya", email="vasya@example.com", password="Qwerty123",
            first_name="V", last_name="I",
        )
        self.client.force_authenticate(user=self.user)

    def test_set_avatar(self):
        response = self.client.put(
            "/api/users/me/avatar/", {"avatar": PIXEL}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("avatar", response.data)
        self.user.refresh_from_db()
        self.assertTrue(bool(self.user.avatar))

    def test_set_avatar_without_avatar_field_is_bad_request(self):
        response = self.client.put(
            "/api/users/me/avatar/", {}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_avatar(self):
        self.client.put(
            "/api/users/me/avatar/", {"avatar": PIXEL}, format="json",
        )
        response = self.client.delete("/api/users/me/avatar/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.avatar))


class UserDetailWriteProtectionTests(APITestCase):
    def setUp(self):
        self.victim = User.objects.create_user(
            username="victim", email="victim@example.com",
            password="VictimPass123", first_name="V", last_name="I",
        )

    def test_unauthenticated_patch_is_not_allowed(self):
        response = self.client.patch(
            f"/api/users/{self.victim.id}/",
            {"first_name": "HACKED", "email": "pwned@evil.com"},
            format="json",
        )
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.first_name, "V")
        self.assertEqual(self.victim.email, "victim@example.com")
