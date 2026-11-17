from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination
from api.serializers.subscriptions import UserWithRecipesSerializer
from users.models import Subscription, User


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_subscriptions(request):
    authors = User.objects.filter(subscribers__user=request.user)
    paginator = LimitPageNumberPagination()
    page = paginator.paginate_queryset(authors, request)
    serializer = UserWithRecipesSerializer(
        page, many=True, context={"request": request},
    )
    return paginator.get_paginated_response(serializer.data)


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def manage_subscription(request, id):
    author = get_object_or_404(User, id=id)

    if request.method == "POST":
        if author == request.user:
            return Response(
                {"errors": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author,
        )
        if not created:
            return Response(
                {"errors": "Вы уже подписаны на этого пользователя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserWithRecipesSerializer(
            author, context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    deleted, _ = Subscription.objects.filter(
        user=request.user, author=author,
    ).delete()
    if not deleted:
        return Response(
            {"errors": "Вы не были подписаны на этого пользователя"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)
