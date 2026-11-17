from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.users import AvatarSerializer


class AvatarView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
