from unittest import mock
import uuid

from coldfront.core.resource import models as resource_models
from coldfront.core.user.models import User
from coldfront_plugin_api.tests import base
from rest_framework.test import APIClient

from coldfront_plugin_api.tests.unit import fakes


class TestUsers(base.TestBase):
    def setUp(self) -> None:
        self.maxDiff = None
        super().setUp()
        self.resource = resource_models.Resource.objects.all().first()

    @property
    def admin_client(self):
        client = APIClient()
        client.login(username="admin", password="test1234")
        return client

    @property
    def logged_in_user_client(self):
        client = APIClient()
        client.login(username="cgray", password="test1234")
        return client

    def test_create_list_detail_user(self):
        username = uuid.uuid4().hex
        first_name = uuid.uuid4().hex
        last_name = uuid.uuid4().hex
        email = f"{uuid.uuid4().hex}@example.com"
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": username,
            "name": {
                "givenName": first_name,
                "familyName": last_name,
            },
            "emails": [
                {
                    "value": email,
                    "type": "work",
                    "primary": True,
                }
            ],
        }
        r = self.admin_client.post("/api/scim/v2/Users", data=payload, format="json")
        self.assertEqual(r.status_code, 201)

        user_dict = r.json()
        self.assertEqual(user_dict["userName"], username)
        self.assertEqual(user_dict["name"]["givenName"], first_name)
        self.assertEqual(user_dict["name"]["familyName"], last_name)
        self.assertEqual(user_dict["emails"][0]["value"], email)

        r = self.admin_client.get("/api/scim/v2/Users?count=100")
        self.assertIn(user_dict, r.json()["Resources"])

        r = self.admin_client.get(f"/api/scim/v2/Users/{username}")
        self.assertEqual(r.json(), user_dict)

    @mock.patch("coldfront.core.user.utils.CombinedUserSearch", fakes.FakeUserSearch)
    def test_create_user_minimal_fetched(self):
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "fake-user-1",
        }
        r = self.admin_client.post("/api/scim/v2/Users", data=payload, format="json")
        self.assertEqual(r.status_code, 201)

        user_dict = r.json()
        self.assertEqual(user_dict["userName"], "fake-user-1")
        self.assertEqual(user_dict["name"]["givenName"], "fake")
        self.assertEqual(user_dict["name"]["familyName"], "user 1")
        self.assertEqual(user_dict["emails"][0]["value"], "fake_user_1@example.com")

    def test_reseponse_404(self):
        fake_username = "9999"
        self.assertFalse(User.objects.filter(username=fake_username).exists())

        r = self.admin_client.get("/api/scim/v2/Users/9999")
        self.assertEqual(r.status_code, 404)

    def test_user_query(self):
        username = uuid.uuid4().hex
        first_name = uuid.uuid4().hex
        last_name = uuid.uuid4().hex
        email = f"{uuid.uuid4().hex}@example.com"
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": username,
            "name": {
                "givenName": first_name,
                "familyName": last_name,
            },
            "emails": [
                {
                    "value": email,
                    "type": "work",
                    "primary": True,
                }
            ],
        }
        r = self.admin_client.post("/api/scim/v2/Users", data=payload, format="json")
        self.assertEqual(r.status_code, 201)

        r = self.admin_client.get(
            f'/api/scim/v2/Users?filter=emails.value eq "{email}"'
        )

        self.assertEqual(r.json()["totalResults"], 1)
        user_list = r.json()["Resources"]
        self.assertEqual(len(user_list), 1)
        self.assertEqual(user_list[0]["userName"], username)
        self.assertEqual(user_list[0]["emails"][0]["value"], email)
