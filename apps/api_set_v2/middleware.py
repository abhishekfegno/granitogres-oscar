import time

from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date


class CustomSessionMiddleware(SessionMiddleware):

    # def process_response(self, request, response):
    #     super(CustomSessionMiddleware, self).process_response(request, response)
    #     if settings.SESSION_COOKIE_NAME in request.COOKIES:
    #         response.delete_cookie(
    #             settings.SESSION_COOKIE_NAME,
    #             path=settings.SESSION_COOKIE_PATH,
    #             domain=settings.SESSION_COOKIE_DOMAIN,
    #             samesite=settings.SESSION_COOKIE_SAMESITE,
    #         )
    #         patch_vary_headers(response, ('Cookie',))
    #     response.set_cookie(
    #         settings.SESSION_COOKIE_NAME,
    #         request.session.session_key,
    #         # max_age=max_age,
    #         # expires=expires,
    #         domain=settings.SESSION_COOKIE_DOMAIN,
    #         path=settings.SESSION_COOKIE_PATH,
    #         secure=settings.SESSION_COOKIE_SECURE or None,
    #         httponly=settings.SESSION_COOKIE_HTTPONLY or None,
    #         samesite='None',
    #     )
    #     return response

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            pass
        else:
            # First check if we need to delete this cookie.
            # The session should be deleted only if the session is entirely empty
            if settings.SESSION_COOKIE_NAME in request.COOKIES and empty:
                response.delete_cookie(
                    settings.SESSION_COOKIE_NAME,
                    path=settings.SESSION_COOKIE_PATH,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                )
            else:
                if accessed:
                    patch_vary_headers(response, ('Cookie',))

                if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                    if request.session.get_expire_at_browser_close():
                        max_age = None
                        expires = None
                    else:
                        max_age = request.session.get_expiry_age()
                        expires_time = time.time() + max_age
                        expires = http_date(expires_time)
                    # Save the session data and refresh the client cookie.
                    # Skip session save for 500 responses, refs #3881.
                    if response.status_code != 500:
                        try:
                            request.session.save()
                        except UpdateError:
                            raise SuspiciousOperation(
                                "The request's session was deleted before the "
                                "request completed. The user may have logged "
                                "out in a concurrent request, for example."
                            )
                        # import pdb;
                        # pdb.set_trace()

                        host = None
                        # if request.META.get('HTTP_REFERER'):
                        #     host = str(request.META['HTTP_REFERER']).split('/')[-2].split(':')[0]
                        # elif request.get_host():
                        if request.get_host():
                            host = f'{request.get_host()}'
                        print(settings.SESSION_COOKIE_DOMAIN)
                        response.set_cookie(
                            settings.SESSION_COOKIE_NAME,
                            request.session.session_key,
                            # max_age=max_age,
                            # expires=expires,
                            domain=host or settings.SESSION_COOKIE_DOMAIN,
                            path=settings.SESSION_COOKIE_PATH,
                            # secure=settings.SESSION_COOKIE_SECURE or True,
                            # httponly=settings.SESSION_COOKIE_HTTPONLY,
                            samesite=None
                        )
        if settings.SESSION_COOKIE_NAME in response.cookies:
            response.cookies[settings.SESSION_COOKIE_NAME]['samesite'] = settings.SESSION_COOKIE_SAMESITE

        # response["Access-Control-Allow-Origin"] = "http://dev.fegno.com:8080"
        response["Access-Control-Allow-Headers"] = ','.join(
            ['accept',
             'accept-encoding',
             'authorization',
             'content-type',
             'dnt',
             'mode',
             'origin',
             'user-agent',
             'x-csrftoken',
             'x-requested-with',
             ])
        response["Access-Control-Allow-Credentials"] = "true"
        # import pdb;pdb.set_trace()
        return response