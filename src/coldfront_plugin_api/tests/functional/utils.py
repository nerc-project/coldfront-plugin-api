import urllib
import requests

from onboarding_tools.keycloak import KeycloakClient
from onboarding_tools import settings


class UpdatedKeycloakClient(KeycloakClient):
    @staticmethod
    def construct_url(realm, path):
        return f"{settings.KEYCLOAK_URL}/admin/realms/{realm}/{path}"

    @property
    def url_base(self):
        return f"{settings.KEYCLOAK_URL}/admin/realms"

    @staticmethod
    def auth_endpoint(realm):
        return f"{settings.KEYCLOAK_URL}/realms/{realm}/protocol/openid-connect/auth"

    @staticmethod
    def token_endpoint(realm):
        return f"{settings.KEYCLOAK_URL}/realms/{realm}/protocol/openid-connect/token"

    def impersonate_access_token(self, user):
        user_session = requests.session()
        user_session.cookies.update(self.impersonate(user).cookies)
        params = {
            "response_mode": "fragment",
            "response_type": "token",
            "client_id": settings.OIDC_CLIENT_ID,
            "client_secret": settings.OIDC_CLIENT_SECRET,
            "redirect_uri": f"{settings.HORIZON_URL}/signup/oidc_redirect_uri",
            "scope": "openid profile email",
        }
        response = user_session.get(
            self.auth_endpoint("master"), params=params, allow_redirects=False
        )
        redirect = response.headers["Location"]
        token = urllib.parse.parse_qs(redirect)["access_token"][0]
        return token
