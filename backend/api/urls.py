from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.ingredients import IngredientViewSet
from api.views.recipes import RecipeViewSet
from api.views.subscriptions import list_subscriptions, manage_subscription
from api.views.users import AvatarView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("users/me/avatar/", AvatarView.as_view(), name="user-avatar"),
    path("users/subscriptions/", list_subscriptions, name="subscriptions"),
    path("users/<int:id>/subscribe/", manage_subscription, name="subscribe"),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
