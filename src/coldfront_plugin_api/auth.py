import os

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from mozilla_django_oidc.contrib.drf import OIDCAuthentication

if os.getenv("PLUGIN_AUTH_OIDC") == "True":
    AUTHENTICATION_CLASSES = [OIDCAuthentication, SessionAuthentication]
else:
    AUTHENTICATION_CLASSES = [SessionAuthentication, BasicAuthentication]
