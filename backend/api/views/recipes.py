from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import RecipeReadSerializer, RecipeWriteSerializer
from api.serializers.subscriptions import RecipeMinifiedSerializer
from recipes.models import Favorite, Recipe, RecipeIngredient, ShoppingCart


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

    def _toggle_relation(self, model, request, pk, add_error, remove_error):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            _, created = model.objects.get_or_create(
                user=request.user, recipe=recipe,
            )
            if not created:
                return Response(
                    {"errors": add_error},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeMinifiedSerializer(
                recipe, context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {"errors": remove_error},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._toggle_relation(
            Favorite, request, pk,
            "Рецепт уже в избранном", "Рецепта не было в избранном",
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(
            ShoppingCart, request, pk,
            "Рецепт уже в корзине", "Рецепта не было в корзине",
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        from api.views.short_links import short_code_for
        request = self.request
        code = short_code_for(int(pk))
        link = request.build_absolute_uri(f"/s/{code}/")
        return Response({"short-link": link})

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        rows = (
            RecipeIngredient.objects
            .filter(recipe__in_carts__user=request.user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total=Sum("amount"))
            .order_by("ingredient__name")
        )
        lines = [
            "{name} ({unit}) — {total}".format(
                name=row["ingredient__name"],
                unit=row["ingredient__measurement_unit"],
                total=row["total"],
            )
            for row in rows
        ]
        content = "\n".join(lines) or "Список покупок пуст"
        response = HttpResponse(
            content, content_type="text/plain; charset=utf-8",
        )
        response["Content-Disposition"] = (
            "attachment; filename=shopping_cart.txt"
        )
        return response
