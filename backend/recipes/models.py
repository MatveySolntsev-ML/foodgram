from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=128)
    measurement_unit = models.CharField("Единица измерения", max_length=64)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient",
            ),
        ]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField("Название", max_length=256)
    image = models.ImageField("Картинка", upload_to="recipes/images/")
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (мин)", validators=[MinValueValidator(1)],
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", related_name="recipes",
    )
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        "Количество", validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
        ]
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite",
            ),
        ]
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="in_carts",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart_item",
            ),
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.recipe} в корзине {self.user}"
