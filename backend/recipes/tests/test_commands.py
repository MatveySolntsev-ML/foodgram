from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from recipes.models import Ingredient

FIXTURE = Path(__file__).parent / "fixtures" / "ingredients_sample.json"


class LoadIngredientsTests(TestCase):
    def test_loads_ingredients_from_json(self):
        call_command("load_ingredients", path=str(FIXTURE))
        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertTrue(Ingredient.objects.filter(name="соль").exists())

    def test_is_idempotent(self):
        call_command("load_ingredients", path=str(FIXTURE))
        call_command("load_ingredients", path=str(FIXTURE))
        self.assertEqual(Ingredient.objects.count(), 2)
