from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings


class CustomSessionMiddleware(SessionMiddleware):

    def process_response(self, request, response):
        super(CustomSessionMiddleware, self).process_response(request, response)
        response.set_cookie(
            settings.SESSION_COOKIE_NAME,
            request.session.session_key,
            # max_age=max_age,
            # expires=expires,
            domain=settings.SESSION_COOKIE_DOMAIN,
            path=settings.SESSION_COOKIE_PATH,
            secure=settings.SESSION_COOKIE_SECURE or None,
            httponly=settings.SESSION_COOKIE_HTTPONLY or None,
            samesite=None,
        )
        return response