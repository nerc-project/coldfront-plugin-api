import os

from django.test import Client


from coldfront_plugin_api.tests.functional import utils
from coldfront_plugin_api.tests.base import TestBase


class TestAuthOIDC(TestBase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.kc_client = utils.UpdatedKeycloakClient()
        # Only initialize Coldfront client if running in Github action
        if os.getenv("CI") == "true":
            self.kc_client.create_client(
                "master",
                "coldfront",
                "nomoresecret",
                ["http://foo/signup/oidc_redirect_uri"],
            )
            self.kc_client.create_user("master", "staff@email.com", "staff", "staff")
            self.kc_client.create_user("master", "user@email.com", "user", "user")

    def setUp(self):
        super().setUp()
        self.staff_user = self.new_user("staff@email.com")
        self.normal_user = self.new_user("user@email.com")

        self.staff_user.is_staff = True
        self.staff_user.save()

    def test_oidc_authenticated(self):
        # Test for both staff and normal authenticated users
        def impersonate_and_get_endpoint(
            user_to_impersonate, endpoint_url, expected_status_code
        ):
            user_token = self.kc_client.impersonate_access_token(user_to_impersonate)

            cf_client = Client()
            r = cf_client.get(
                endpoint_url,
                HTTP_AUTHORIZATION=f"Bearer {user_token}",
            )
            self.assertEqual(r.status_code, expected_status_code)

        for endpoint_url in [
            "/api/scim/v2/Users",
            "/api/scim/v2/Groups",
            "/api/allocations",
        ]:
            impersonate_and_get_endpoint(self.staff_user.username, endpoint_url, 200)
            impersonate_and_get_endpoint(self.normal_user.username, endpoint_url, 403)

    def test_oidc_unauthenticated(self):
        # Test for unauthenticated user case
        cf_client = Client()
        for endpoint_url in [
            "/api/scim/v2/Users",
            "/api/scim/v2/Groups",
            "/api/allocations",
        ]:
            r = cf_client.get(endpoint_url)
            self.assertEqual(r.status_code, 401)
