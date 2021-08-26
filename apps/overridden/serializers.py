from oscar.core.compat import get_user_model
from rest_framework import serializers

UserModel = get_user_model()


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    class Meta:
        model = UserModel
        fields = ('pk', 'username', 'email', 'first_name', 'last_name', 'status', 'is_delivery_request_pending')
        read_only_fields = ( 'username', 'status', 'is_delivery_request_pending')

