from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient


class IngredientTests(APITestCase):
    def setUp(self):
        Ingredient.objects.create(name="соль", measurement_unit="г")
        Ingredient.objects.create(name="сахар", measurement_unit="г")
        Ingredient.objects.create(name="солянка", measurement_unit="шт")

    def test_list_ingredients(self):
        response = self.client.get("/api/ingredients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_by_name_prefix_case_insensitive(self):
        response = self.client.get("/api/ingredients/", {"name": "СОЛ"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {item["name"] for item in response.data}
        self.assertEqual(names, {"соль", "солянка"})
