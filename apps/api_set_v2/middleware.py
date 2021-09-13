# import time
import re

# from django.contrib.sessions.backends.base import UpdateError
# from django.contrib.sessions.middleware import SessionMiddleware
# from django.conf import settings
# from django.core.exceptions import SuspiciousOperation
# from django.utils.cache import patch_vary_headers
# from django.utils.http import http_date
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http.response import HttpResponse
from oscarapi.middleware import HeaderSessionMiddleware
from oscarapi.utils.session import session_id_from_parsed_session_uri, get_session
from rest_framework import exceptions
from oscarapi.utils.request import get_domain
from django.utils.translation import ugettext as _
from oscarapi.utils.loading import get_api_class
HTTP_SESSION_ID_REGEX = re.compile(
    r"^SID:(?P<type>(?:ANON|AUTH)):(?P<realm>.*?):(?P<session_id>.+?)(?:[-:][0-9a-fA-F]+){0,2}$"
)

def parse_session_id(request):
    """Parse a session id from the request"""
    unparsed_session_id = request.META.get("HTTP_SESSION_ID", None)
    if unparsed_session_id is not None:
        parsed_session_id = HTTP_SESSION_ID_REGEX.match(unparsed_session_id)
        if parsed_session_id is not None:
            return parsed_session_id.groupdict()

    return None


def start_or_resume(session_id, session_type):
    if session_type == "ANON":
        return get_session(session_id, raise_on_create=False)

    return get_session(session_id, raise_on_create=True)


class CustomSessionMiddleware(SessionMiddleware):

    def process_response(self, request, response):
        response = super(CustomSessionMiddleware, self).process_response(request, response)
        if response.cookies:
            response.set_cookie(settings.SESSION_COOKIE_NAME, request.session.session_key, max_age=360)
            response.cookies[settings.SESSION_COOKIE_NAME]['secure'] = True
            response.cookies[settings.SESSION_COOKIE_NAME]['samesite'] = 'None'
        return response


class CustomHeaderSessionMiddleware(HeaderSessionMiddleware):
    """
    Implement session through headers:

    http://www.w3.org/TR/WD-session-id

    TODO:
    Implement gateway protection, with permission options for usage of
    header sessions. With that in place the api can be used for both trusted
    and non trusted clients, see README.rst.
    """

    def process_request(self, request):
        """
        Parse the session id from the 'Session-Id: ' header when using the api.
        """
        print(self.is_api_request(request))
        print(parse_session_id(request))
        if self.is_api_request(request):
            try:
                parsed_session_uri = parse_session_id(request)
                if parsed_session_uri is not None:
                    domain = get_domain(request)
                    if parsed_session_uri["realm"] != domain:
                        raise exceptions.PermissionDenied(
                            _("Can not accept cookie with realm %s on realm %s")
                            % (parsed_session_uri["realm"], domain)
                        )
                    session_id = session_id_from_parsed_session_uri(parsed_session_uri)
                    request.session = start_or_resume(
                        session_id, session_type=parsed_session_uri["type"]
                    )
                    request.parsed_session_uri = parsed_session_uri

                    # since the session id is assigned by the CLIENT, there is
                    # no point in having csrf_protection. Session id's read
                    # from cookies, still need csrf!
                    request.csrf_processing_done = True
                    return None
            except exceptions.APIException as e:
                response = HttpResponse(
                    '{"reason": "%s"}' % e.detail, content_type="application/json"
                )
                response.status_code = e.status_code
                return response

        return super(CustomSessionMiddleware, self).process_request(request)

    def process_response(self, request, response):
        """
        Add the 'Session-Id: ' header when using the api.
        """
        if (
                self.is_api_request(request)
                and getattr(request, "session", None) is not None
                and hasattr(request, "parsed_session_uri")
        ):
            session_key = request.session.session_key
            parsed_session_key = session_id_from_parsed_session_uri(
                request.parsed_session_uri
            )
            assert session_key == parsed_session_key, "%s is not equal to %s" % (
                session_key,
                parsed_session_key,
            )
            response["Session-Id"] = "SID:%(type)s:%(realm)s:%(session_id)s" % (
                request.parsed_session_uri
            )
        # import pdb;pdb.set_trace()

        return super(CustomSessionMiddleware, self).process_response(request, response)
