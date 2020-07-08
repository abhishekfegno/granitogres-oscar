from rest_framework import serializers
from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = (
            "user",
            "gst_number",
            "pincode",
        )

    def __init__(self, instance=None, **kwargs):
        instance = self.context['request'].user._profile
        super(UserProfileSerializer, self).__init__(instance=instance, **kwargs)


