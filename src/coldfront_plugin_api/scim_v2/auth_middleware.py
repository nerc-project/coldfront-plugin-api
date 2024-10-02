import os
import logging

from django_scim.middleware import SCIMAuthCheckMiddleware
from mozilla_django_oidc.contrib.drf import OIDCAuthentication

logger = logging.getLogger(__name__)


class SCIMColdfrontAuthCheckMiddleware(SCIMAuthCheckMiddleware):
    def process_request(self, request):
        if not request.user or not request.user.is_authenticated:
            # django-scim2 does not use by default the DRF backend of mozilla-django-oidc,
            # and therefore does not support authentication with bearer tokens, only
            # session cookies. We manually call `authenticate()` on the DRF backend if
            # the user is not already authenticated, and if OIDC authentication is enabled.
            if os.getenv("PLUGIN_AUTH_OIDC") == "True":
                if user_tuple := OIDCAuthentication().authenticate(request):
                    request.user = user_tuple[0]
        return super().process_request(request)
