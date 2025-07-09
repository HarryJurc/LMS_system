from rest_framework.serializers import ValidationError
from urllib.parse import urlparse


class YouTubeValidator:
    def __init__(self, field):
        self.field = field

    def __call__(self, attrs):
        value = attrs.get(self.field)
        if value:
            from urllib.parse import urlparse
            parsed_url = urlparse(value)
            if 'youtube.com' not in parsed_url.netloc and 'youtu.be' not in parsed_url.netloc:
                raise ValidationError({self.field: "Разрешены только ссылки на YouTube."})