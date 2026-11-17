from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.users import AvatarSerializer


class UserViewSet(DjoserUserViewSet):
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()


class AvatarView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = AvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
