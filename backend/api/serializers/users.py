from djoser.serializers import (
    UserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers

from api.fields import Base64ImageField
from users.models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name", "password",
        )


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name",
            "is_subscribed", "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.subscriptions.filter(author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)
