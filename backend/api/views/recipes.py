from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import RecipeReadSerializer, RecipeWriteSerializer
from recipes.models import Recipe


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient",
    )
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = LimitPageNumberPagination

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        user = self.request.user

        if params.get("author"):
            queryset = queryset.filter(author_id=params["author"])
        if user.is_authenticated and params.get("is_favorited") == "1":
            queryset = queryset.filter(favorited_by__user=user)
        if user.is_authenticated and params.get("is_in_shopping_cart") == "1":
            queryset = queryset.filter(in_carts__user=user)
        return queryset
