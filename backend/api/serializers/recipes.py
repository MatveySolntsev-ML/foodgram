from django.db import transaction
from rest_framework import serializers

from api.fields import Base64ImageField
from api.serializers.users import UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients", many=True, read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id", "author", "ingredients", "is_favorited",
            "is_in_shopping_cart", "name", "image", "text", "cooking_time",
        )

    def _user(self):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user
        return None

    def get_is_favorited(self, obj):
        user = self._user()
        return bool(user) and obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self._user()
        return bool(user) and obj.in_carts.filter(user=user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "image", "name", "text", "cooking_time")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент")
        ids = [item["id"].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться",
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data,
        )
        self._set_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._set_ingredients(instance, ingredients)
        return instance

    def _set_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe, ingredient=item["id"], amount=item["amount"],
            )
            for item in ingredients
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
