import rest_auth.views
from django.contrib.auth import get_user_model
from oscar.core.loading import get_model
from oscarapi.basket import operations
from oscarapi.utils.session import login_and_upgrade_session
from rest_framework import permissions, authentication
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
# REGISTRATION URLS
from rest_framework.views import APIView
from rest_framework import status

from apps.api_set.serializers.auth import MobileNumberSerializer, OTP, OtpSerializer, UserSerializer
from apps.api_set.serializers.basket import WncBasketSerializer

AWAITING_LENGTH = 8
User = get_user_model()


class SendOTP(APIView):
    """
    This API is used to send otp.
    on getting a mobile number, first it is checked across a User Records, Send an otp if found.
    Else Return response as mobile number not registered.

    Mobile number must be starting with "+91" Without spaces in it.

    When Request is forwarded from Delivery App, 'is_delivery_boy_request': true  must be added with it.

    """

    permission_classes = [permissions.AllowAny, ]
    serializer_class = MobileNumberSerializer

    def post(self, request):
        out = {'id': None, 'otp_send': False, 'error': None}
        mns = self.serializer_class(data=request.data, context={'request': request})
        if not mns.is_valid():
            out['error'] = mns.errors
            return Response(out, status=400)
        else:
            otp = OTP.generate(mns.validated_data['mobile'], )
            status = otp.send_message()       # FOR LOCAL DEVELOPMENT.
            # status = False
            out['id'] = otp.id
            out['mobile_number'] = otp.mobile_number
            out['otp_send'] = status
            out['otp'] = otp.code
            out['user'] = bool(otp.user)
            out['user_name'] = (bool(otp.user) and otp.user.get_short_name()) or None
        return Response(out)


@api_view(['POST'])
def resend_otp(request):
    """
    POST
    {
        "id": 2,
        "mobile_number": "9497572863"
    }

    RESPONSE :
    {
        "resend": true,
        "message": "SMS Sent!"
    }
    """
    otp_obj = OTP.objects.filter(id=request.data['id'], mobile_number=request.data['mobile_number'], is_active=True).first()
    if otp_obj:
        status = otp_obj.send_message()
        if status is None:
            return Response({'resend': False, 'message': 'Reached Maximum Retries!'}, status=400)
        elif status is True:
            return Response({'resend': True, 'message': 'SMS Sent!'}, status=200)
        return Response({'resend': False, 'message': 'Couldn\'t Send Message. Please Contact Admin!'}, status=400)
    return Response({'resend': False, 'message': 'Invalid Attempt'}, status=400)


class LoginWithOTP(APIView):
    """
    This API Permits Login.
    """
    permission_classes = [permissions.AllowAny, ]
    serializer_class = OtpSerializer

    def post(self, request, *args, **kwargs):
        out = {'error': None, 'user': None, 'basket': None, 'cart_item_count': 0, 'new_user': None}

        # Validating Data
        otp_serializer = self.serializer_class(data=request.data, context={'request': request})
        if not otp_serializer.is_valid():
            out['error'] = otp_serializer.errors
            return Response(out, status=400)

        # Generating User or Respond with error
        otp_object = otp_serializer.validated_data['object']
        out['new_user'] = False
        if not otp_object.user:  # signup
            try:
                otp_object.generate_user()
                out['new_user'] = True #new user flag
            except Exception as e:
                out['error'] = {
                    'non_field_errors': [str(e)]
                }
                return Response(out, status=400)

        # Create User and Merge Baskets
        user = otp_object.user
        out['user'] = UserSerializer(instance=otp_object.user, context={'request': request}).data
        anonymous_basket = operations.get_anonymous_basket(request)
        request.user = user
        request.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login_and_upgrade_session(request._request, user)
        # merge anonymous basket with authenticated basket.
        basket = operations.get_user_basket(user)
        if anonymous_basket is not None:
            basket.merge(anonymous_basket)

        operations.store_basket_in_session(basket, request.session)
        out['basket'] = WncBasketSerializer(instance=basket, context={'request': request}).data
        out["cart_item_count"] = basket.lines.all().count()
        return Response(out, status=200)


class LoginWithOTPForDeliveryBoy(LoginWithOTP):
    def post(self, request, *args, **kwargs):
        out = {'error': None, 'user': None, 'basket': None, 'cart_item_count': 0}

        # Validating Data
        otp_serializer = self.serializer_class(data=request.data, context={'request': request})
        if not otp_serializer.is_valid():
            out['error'] = otp_serializer.errors
            return Response(out, status=400)

        # Generating User or Respond with error
        otp_object = otp_serializer.validated_data['object']
        if not otp_object.user:  # signup
            try:
                otp_object.generate_user()
            except Exception as e:
                out['error'] = {
                    'non_field_errors': [str(e)]
                }
                return Response(out, status=400)

        # Create User and Merge Baskets
        user = otp_object.user
        out['user'] = UserSerializer(instance=otp_object.user, context={'request': request}).data

        request.user = user
        request.user.backend = 'django.contrib.auth.backends.ModelBackend'
        login_and_upgrade_session(request._request, user)
        # merge anonymous basket with authenticated basket.
        basket = operations.get_user_basket(user)
        return Response(out, status=200)


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return self.get_queryset()
        else:
            data = {"detail": "Authentication credentials were not provided"}
            return Response(data, status.HTTP_401_UNAUTHORIZED)

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        """
        Adding this method since it is sometimes called when using
        django-rest-swagger
        https://github.com/Tivix/django-rest-auth/issues/275
        """
        return get_user_model().objects.none()

