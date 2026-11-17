from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.users import AvatarView

router = DefaultRouter()

urlpatterns = [
    path("users/me/avatar/", AvatarView.as_view(), name="user-avatar"),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path("", include(router.urls)),
]
