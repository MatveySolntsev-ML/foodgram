from rest_framework import serializers

from api.serializers.users import UserSerializer
from recipes.models import Recipe


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes = obj.recipes.all()
        limit = request.query_params.get("recipes_limit") if request else None
        if limit is not None and limit.isdigit():
            recipes = recipes[: int(limit)]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context,
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
