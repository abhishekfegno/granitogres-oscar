import re

from django import forms
from oscar.apps.customer.utils import normalise_email
from oscar.core.compat import get_user_model
from rest_framework import serializers

from apps.users.models import UserProfile, OTP

User = get_user_model()


class MobileNumberSerializer(serializers.Serializer):

    mobile = serializers.CharField(max_length=15, required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, attrs):
        mobile_number_format = r"\d{9,12}"
        is_valid_number = re.match(mobile_number_format, attrs['mobile'])
        if not is_valid_number:
            raise serializers.ValidationError('Mobile number is not valid')
        userprofile = UserProfile.objects.filter(mobile=attrs['mobile']).last()
        if not userprofile:
            raise serializers.ValidationError(
                'Mobile number is not in our records. Please Contact Wood\'NCart')
        if userprofile.user:
            raise serializers.ValidationError(
                'This Mobile number is already Registered! Please \'Login\' or try \'Forget Password\'!')
        attrs['user_profile'] = userprofile
        return attrs


class PinSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=4, min_length=4, required=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class OtpSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, )
    code = serializers.IntegerField(required=True, max_value=999999, min_value=100000)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def validate(self, attrs):
        attrs['user_profile'] = OTP.validate(**attrs)
        if not attrs['user_profile']:
            raise serializers.ValidationError('invalid_otp')
        return attrs


class UserSerializer(serializers.ModelSerializer):
    redeem_points = serializers.SerializerMethodField()
    get_redeem_points = lambda self, instance: abs(instance.redeem_points)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'pin', 'is_active',
                  'date_joined', 'mobile', 'branch',
                  'achieved_points', 'redeem_points', 'balance_points', 'category', 'ranking',
                  'is_dealer', ]


class ConfirmUserLoginSerializer(PinSerializer, MobileNumberSerializer):

    def validate(self, attrs):
        super(MobileNumberSerializer, self).validate(attrs)
        super(PinSerializer, self).validate(attrs)
        if not attrs['user']:
            raise serializers.ValidationError('Invalid User')
        if not attrs['pin'] == attrs['user'].pin:
            raise serializers.ValidationError('Invalid PIN')
        return attrs


class RegisterSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=True)
    password2 = serializers.CharField(write_only=True)
    password1 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password2', 'password1', 'profile']

    def clean_email(self, email):
        """
        Checks for existing users with the supplied email address.
        """
        email = normalise_email(email)
        if User._default_manager.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email address already exists")
        return email

    def clean_password1(self, password1):
        password2 = self.validated_data.get('password2', '')
        if not password1:
            raise forms.ValidationError("Password field is required")
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2
