from django.conf import settings
from oscarapi.basket.operations import get_basket
from oscarapi.serializers.basket import BasketSerializer
from oscarapi.serializers.login import UserSerializer
from oscarapi.views.login import LoginView as CoreLoginView
from oscarapi.utils.session import login_and_upgrade_session
from oscarapi.views.login import LoginSerializer
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from oscarapi.basket import operations
from oscar.core.loading import get_model


class LoginView(CoreLoginView):
    """
    Api for logging in users.

    DELETE:
    Log the user out by destroying the session.
    Anonymous users will have their cart destroyed as well, because there is
    no way to reach it anymore

    POST(username, password):
    1. The user will be authenticated. The next steps will only be
       performed is login is successful. Logging in logged in users results in
       405.
    2. The anonymous cart will be merged with the private cart associated with
       that authenticated user.
    3. A new session will be started, this session identifies the authenticated
       user for the duration of the session, without further need for
       authentication.
    4. The new, merged cart will be associated with this session.
    5. The anonymous session will be terminated.
    6. A response will be issued containing the new session id as a header
       (only when the request contained the session header as well).

    GET (enabled in DEBUG mode only):
    Get the details of the logged in user.
    If more details are needed, use the ``OSCARAPI_USER_FIELDS`` setting to change
    the fields the ``UserSerializer`` will render.
    """
    serializer_class = LoginSerializer

    def get(self, request, format=None):
        ctxt = {'context': {'request': request}}
        if request.user.is_authenticated:
            user_serializer_data = UserSerializer(request.user, many=False).data
            return Response({
                'user': user_serializer_data,
                'basket': BasketSerializer(operations.get_basket(request), **ctxt).data,
            })
        return Response({
            'user': None,
            'basket': None
        }, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        ser = self.serializer_class(data=request.data)
        ctxt = {'context': {'request': request}}

        if ser.is_valid():
            anonymous_basket = operations.get_anonymous_basket(request)
            user = ser.instance
            # refuse to login logged in users, to avoid attaching sessions to
            # multiple users at the same time.
            if request.user.is_authenticated:
                return Response(
                    {"detail": "Session is in use, log out first"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )
            request.user = user
            login_and_upgrade_session(request, user)

            # merge anonymous basket with authenticated basket.
            basket = get_basket(request)

            return Response({
                'user': UserSerializer(instance=user, **ctxt).data,
                'basket': BasketSerializer(instance=basket, **ctxt).data,
            })

        return Response(ser.errors, status=status.HTTP_401_UNAUTHORIZED)

