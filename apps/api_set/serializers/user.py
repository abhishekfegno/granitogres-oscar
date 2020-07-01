from oscar.core.compat import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = User.USERNAME_FIELD, "id", "email", "first_name", "last_name"
