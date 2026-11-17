from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
)
from users.models import User


class RecipeModelTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="chef", email="chef@example.com", password="x",
            first_name="C", last_name="C",
        )
        self.ingredient = Ingredient.objects.create(
            name="соль", measurement_unit="г",
        )

    def test_create_recipe_with_ingredient(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=30,
        )
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=self.ingredient, amount=5,
        )
        self.assertEqual(recipe.recipe_ingredients.count(), 1)

    def test_cooking_time_must_be_positive(self):
        recipe = Recipe(
            author=self.author, name="Суп", text="Варить", cooking_time=0,
        )
        with self.assertRaises(ValidationError):
            recipe.full_clean()

    def test_favorite_unique_together(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=10,
        )
        Favorite.objects.create(user=self.author, recipe=recipe)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.author, recipe=recipe)

    def test_shopping_cart_unique_together(self):
        recipe = Recipe.objects.create(
            author=self.author, name="Суп", text="Варить", cooking_time=10,
        )
        ShoppingCart.objects.create(user=self.author, recipe=recipe)
        with self.assertRaises(IntegrityError):
            ShoppingCart.objects.create(user=self.author, recipe=recipe)


class IngredientOrderingTests(TestCase):
    def test_default_ordering_is_case_insensitive(self):
        # A capitalized name should not sort before a lowercase name
        # that is alphabetically earlier (matches case-insensitive
        # collation, e.g. PostgreSQL's default `lower()` behavior).
        Ingredient.objects.create(name="Zebra", measurement_unit="г")
        Ingredient.objects.create(name="apple", measurement_unit="г")
        names = list(Ingredient.objects.values_list("name", flat=True))
        self.assertEqual(names, ["apple", "Zebra"])
