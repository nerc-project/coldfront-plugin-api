import os
import logging

from django_scim.middleware import SCIMAuthCheckMiddleware
from mozilla_django_oidc.contrib.drf import OIDCAuthentication

logger = logging.getLogger(__name__)


class SCIMColdfrontAuthCheckMiddleware(SCIMAuthCheckMiddleware):
    def process_request(self, request):
        if not request.user or not request.user.is_authenticated:
            # Check if OIDC authentication is enabled to see if we should authenticate user using OIDC
            # PLUGIN_AUTH_OIDC implies OIDC is enabled and DRF OIDC backend is configured
            if os.getenv("PLUGIN_AUTH_OIDC") == "True":
                if user_tuple := OIDCAuthentication().authenticate(request):
                    request.user = user_tuple[0]
        return super().process_request(request)
