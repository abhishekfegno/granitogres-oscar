import re
from oscar.core.compat import get_user_model
from rest_framework import serializers

from apps.api_set import app_settings
from apps.api_set.app_settings import OTP_MAX_VALUE, OTP_MIN_VALUE
from apps.users.models import OTP

User = get_user_model()
mobile_number_format = app_settings.MOBILE_NUMBER_VALIDATOR['REGEX']


class MobileNumberSerializer(serializers.Serializer):

    mobile = serializers.CharField(max_length=15, required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, mobile):
        is_valid_number = re.match(mobile_number_format, attrs)
        if not is_valid_number:
            raise serializers.ValidationError('Mobile number is not valid')
        return mobile


class OtpSerializer(MobileNumberSerializer):
    id = serializers.IntegerField(required=True)
    code = serializers.IntegerField(required=True, max_value=OTP_MAX_VALUE, min_value=OTP_MIN_VALUE)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, attrs):
        attrs['object'] = OTP.validate(mobile_number=attrs['mobile'], id=attrs['id'], code=attrs['code'], )
        if not attrs['object']:
            raise serializers.ValidationError('OTP is not valid!')
        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'mobile', 'email',
            'first_name', 'last_name',
            'pin', 'is_active',
        ]
