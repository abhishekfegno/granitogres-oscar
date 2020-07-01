from oscar.core.loading import get_model, get_class
from oscarapi.utils.loading import get_api_classes
from rest_framework import serializers

from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin
from apps.users.models import GSTNumber, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserProfile
        fields = (
            "user",
            "gst_number",
            "pincode",
        )

