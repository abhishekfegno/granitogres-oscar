from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.serializers.account import UserProfileSerializer
from apps.users.models import UserProfile


@api_view(['GET', 'POST'])
def update_profile(request, *args, **kwargs):
    serializer_class = UserProfileSerializer
    has_gst = UserProfile.get_gst(request.user)

    if request.method == 'GET':
        return Response({
            'gst_number': has_gst,
        })

    if has_gst is None and request.method == 'POST':
        serializer = serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
