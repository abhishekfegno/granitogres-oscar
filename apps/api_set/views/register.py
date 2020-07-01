from oscar.core.compat import get_user_model
from oscarapi.serializers.login import UserSerializer
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.serializers.user import UserRegisterSerializer

User = get_user_model()


@api_view(['POST'])
def register_view(request):
    serialized = UserRegisterSerializer(data=request.data)

    if serialized.is_valid():
        User.objects.create_user(
            request.data['email'],
            request.data['username'],
            request.data['password'],
            request.data['first_name'],
            request.data['last_name'],
            is_active=True
        )
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)

