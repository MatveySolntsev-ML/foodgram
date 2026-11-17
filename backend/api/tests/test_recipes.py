from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe
from users.models import User

PIXEL = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACV"
    "BMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAgg"
    "CByxOyYQAAAABJRU5ErkJggg=="
)


class RecipeCRUDTests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.other = User.objects.create_user(
            username="guest", email="guest@example.com", password="x",
            first_name="G", last_name="G",
        )
        self.ingredient = Ingredient.objects.create(
            name="соль", measurement_unit="г",
        )

    def test_create_recipe(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 5}],
                "image": PIXEL,
                "name": "Суп",
                "text": "Варить 30 минут",
                "cooking_time": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(response.data["ingredients"][0]["amount"], 5)

    def test_create_requires_auth(self):
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 5}],
                "image": PIXEL, "name": "Суп", "text": "x", "cooking_time": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_rejects_empty_ingredients(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [], "image": PIXEL, "name": "Суп",
                "text": "x", "cooking_time": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_duplicate_ingredients(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.post(
            "/api/recipes/",
            {
                "ingredients": [
                    {"id": self.ingredient.id, "amount": 5},
                    {"id": self.ingredient.id, "amount": 3},
                ],
                "image": PIXEL, "name": "Суп", "text": "x", "cooking_time": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_recipes_paginated(self):
        Recipe.objects.create(
            author=self.author, name="Суп", text="x",
            cooking_time=10, image="r.jpg",
        )
        response = self.client.get("/api/recipes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_update_only_by_author(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x",
            cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            f"/api/recipes/{recipe.id}/",
            {
                "ingredients": [{"id": self.ingredient.id, "amount": 1}],
                "image": PIXEL, "name": "Новый суп", "text": "x",
                "cooking_time": 5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_only_by_author(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x",
            cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/api/recipes/{recipe.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
