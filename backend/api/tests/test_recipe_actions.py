from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class RecipeActionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eater", email="e@example.com", password="x",
            first_name="E", last_name="E",
        )
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="x",
            cooking_time=10, image="r.jpg",
        )
        self.client.force_authenticate(user=self.user)

    def test_favorite_add_and_remove(self):
        url = f"/api/recipes/{self.recipe.id}/favorite/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_shopping_cart_add_and_remove(self):
        url = f"/api/recipes/{self.recipe.id}/shopping_cart/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_link(self):
        response = self.client.get(f"/api/recipes/{self.recipe.id}/get-link/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("short-link", response.data)

    def test_download_shopping_cart_aggregates_amounts(self):
        salt = Ingredient.objects.create(name="соль", measurement_unit="г")
        other_recipe = Recipe.objects.create(
            author=self.author, name="Борщ", text="x",
            cooking_time=20, image="r2.jpg",
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe, ingredient=salt, amount=5,
        )
        RecipeIngredient.objects.create(
            recipe=other_recipe, ingredient=salt, amount=3,
        )
        self.client.post(f"/api/recipes/{self.recipe.id}/shopping_cart/")
        self.client.post(f"/api/recipes/{other_recipe.id}/shopping_cart/")

        response = self.client.get("/api/recipes/download_shopping_cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode("utf-8")
        self.assertIn("соль", content)
        self.assertIn("8", content)
