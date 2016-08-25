from ..rest_framework.serializers import UserCreatedSerializer


def jwt_response_payload_handler(token, user=None, request=None):
    return UserCreatedSerializer(user).data
