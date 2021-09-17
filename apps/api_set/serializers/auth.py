import re
from oscar.core.compat import get_user_model
from rest_framework import serializers

from apps.api_set import app_settings
from apps.api_set.app_settings import OTP_MAX_VALUE, OTP_MIN_VALUE
from apps.users.models import OTP

User = get_user_model()
# mobile_number_format = app_settings.MOBILE_NUMBER_VALIDATOR['REGEX']


class MobileNumberSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        max_length=app_settings.MOBILE_NUMBER_VALIDATOR['LENGTH'],
        min_length=app_settings.MOBILE_NUMBER_VALIDATOR['LENGTH'],
        required=True
    )

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate_mobile(self, mobile):
        """
        As per change, Delivery boy should not be able to register, but must be added from Backend by Admin!
        """
        is_delivery_boy_request = self.context['request'].data.get('is_delivery_boy_request', False)
        mobile_number_format = r'^\d{10}$'
        is_valid_number = re.match(mobile_number_format, mobile)
        if not is_valid_number:
            raise serializers.ValidationError('Mobile number is not valid')
        if is_delivery_boy_request:
            user = User.objects.filter(username=mobile).first()
            if not user:
                raise serializers.ValidationError('Mobile number is not valid')
            if user.is_delivery_boy is not True:
                raise serializers.ValidationError('This user is not permitted to continue!')
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
            'image', 'image',
            'is_active', 'is_delivery_boy',
        ]
