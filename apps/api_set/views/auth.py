from django.db.models import Max, Min, F
from oscar.core.loading import get_model
from rest_framework import permissions, authentication, serializers
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
# REGISTRATION URLS
from rest_framework.views import APIView

from apps.api_set.serializers.auth import MobileNumberSerializer, OTP, OtpSerializer, PinSerializer, \
    ConfirmUserLoginSerializer, RegisterSerializer

AWAITING_LENGTH = 8

UserProfile = get_model('users', 'UserProfile')


class SendOTP(APIView):

    permission_classes = [permissions.AllowAny, ]
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication ]
    serializer_class = MobileNumberSerializer

    def post(self, request):
        """
        This API is used For First Time Login.
        on getting a mobile number, first it is checked across a User Records, Send an otp if found.
        Else Return response as mobile number not registered.

        Mobile number must be starting with "+91" Without spaces in it.
        """
        out = {
            'id': None,
            'otp': None,
            'otp_send': False,
            'user_pin': None,
            'error': None,
        }
        mns = self.serializer_class(data=self.request.data, context={'request': request})
        if not mns.is_valid():
            out['error'] = mns.errors
        else:
            user_profile = mns.validated_data['user_profile']
            otp = OTP.generate(user_profile)
            status = otp.send_message()
            out['id'] = otp.id
            out['otp'] = str(otp.code)
            out['otp_send'] = status
            out['user_pin'] = False
        return Response(out)


class VerifyOTP(APIView):
    """
        This API is used Verifying the OTP. API Expects `otp`  and `otp_id` with
    """
    permission_classes = [permissions.AllowAny, ]
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    serializer_class = OtpSerializer

    def post(self, request):
        out = {'error': None, 'user': None, }
        otp = self.serializer_class(data=request.data, context={'request': request})
        if not otp.is_valid():
            out['error'] = otp.errors
        else:
            # get_homepage_data(request, otp.validated_data['user'], out)     # `out` as pass by reference
            user_profile = otp.validated_data['user_profile']
            out['user_profile'] = {
                "id": user_profile.id,
                "pincode": user_profile.pincode,
                "email": user_profile.email,
                "mobile": user_profile.mobile,
                "name": user_profile.name,
                "gst_number": user_profile.gst_number,
            }
        return Response(out)


class UserRegister(APIView):
    """ This API is used for Registering User.
    """
    permission_classes = [permissions.AllowAny, ]
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    serializer_class = RegisterSerializer

    def post(self, request):
        out = {'error': None, 'user': None, }
        otp = self.serializer_class(data=request.data, context={'request': request})
        if not otp.is_valid():
            out['error'] = otp.errors
        return Response(out)


