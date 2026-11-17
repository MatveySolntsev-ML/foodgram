import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

ALLOWED_IMAGE_EXTENSIONS = {
    "jpeg": "jpg",
    "jpg": "jpg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
}


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, imgstr = data.split(";base64,")
            claimed_ext = header.split("/")[-1].lower()
            ext = ALLOWED_IMAGE_EXTENSIONS.get(claimed_ext)
            if ext is None:
                raise serializers.ValidationError(
                    "Неподдерживаемый формат изображения.",
                )
            data = ContentFile(
                base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}",
            )
        return super().to_internal_value(data)
