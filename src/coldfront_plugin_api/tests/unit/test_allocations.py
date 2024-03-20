from os import devnull
import sys

from coldfront.core.allocation import models as allocation_models
from django.core.management import call_command
from coldfront_plugin_cloud.tests import base
from coldfront_plugin_cloud import attributes
from rest_framework.test import APIClient


class TestAllocation(base.TestBase):
    def setUp(self) -> None:
        # Otherwise output goes to the terminal for every test that is run
        backup, sys.stdout = sys.stdout, open(devnull, "a")
        call_command("initial_setup", "-f")
        call_command("load_test_data")
        call_command("register_cloud_attributes")
        sys.stdout = backup

        self.resource = self.new_resource(name="Devstack", auth_url="http://localhost")

    @staticmethod
    def new_allocation_attribute(allocation, attribute, value):
        au, _ = allocation_models.AllocationAttribute.objects.get_or_create(
            allocation=allocation,
            allocation_attribute_type=allocation_models.AllocationAttributeType.objects.get(
                name=attribute
            ),
            value=value,
        )
        return au

    @property
    def admin_client(self):
        client = APIClient()
        client.login(username="admin", password="test1234")
        return client

    def test_list_allocations(self):
        user = self.new_user()
        project = self.new_project(pi=user)
        allocation = self.new_allocation(project, self.resource, 1)

        response = self.admin_client.get("/api/allocations")
        self.assertEqual(response.status_code, 200)
        self.assertIn(allocation.id, [a["id"] for a in response.json()])

        for allocation in response.json():
            self.assertEqual(allocation["status"], "Active")

    def test_list_all_allocations(self):
        user = self.new_user()
        project = self.new_project(pi=user)
        allocation = self.new_allocation(project, self.resource, 1)
        allocation.status = allocation_models.AllocationStatusChoice.objects.get(
            name="Expired"
        )
        allocation.save()
        self.assertEqual(allocation.status.name, "Expired")

        # Expired allocation will not display without ?all query
        response = self.admin_client.get("/api/allocations")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(allocation.id, [a["id"] for a in response.json()])

        # Expired allocation shows up when using ?all query
        response = self.admin_client.get("/api/allocations?all=true")
        self.assertEqual(response.status_code, 200)
        self.assertIn(allocation.id, [a["id"] for a in response.json()])

    def test_filter_allocations(self):
        user1 = self.new_user()
        project1 = self.new_project(pi=user1)
        project2 = self.new_project(pi=user1)
        allocation1 = self.new_allocation(project1, self.resource, 1)
        allocation2 = self.new_allocation(project1, self.resource, 2)
        allocation3 = self.new_allocation(project2, self.resource, 1)
        aa1 = self.new_allocation_attribute(allocation1, attributes.QUOTA_LIMITS_CPU, 1)
        self.new_allocation_attribute(allocation2, attributes.QUOTA_LIMITS_CPU, 1)
        aa3 = self.new_allocation_attribute(allocation3, attributes.QUOTA_LIMITS_CPU, 3)
        aa4 = self.new_allocation_attribute(
            allocation1, attributes.QUOTA_LIMITS_MEMORY, 64
        )
        self.new_allocation_attribute(allocation2, attributes.QUOTA_LIMITS_MEMORY, 128)
        self.new_allocation_attribute(allocation3, attributes.QUOTA_LIMITS_MEMORY, 64)

        # Filter by project title
        r_json = self.admin_client.get(
            f"/api/allocations?project__title={project1.title}"
        ).json()
        self.assertEqual(len(r_json), 2)
        self.assertEqual(r_json[0]["project"]["title"], project1.title)

        # Filter by project pi email
        r_json = self.admin_client.get(
            f"/api/allocations?project__pi__email={user1.email}"
        ).json()
        self.assertEqual(len(r_json), 3)
        self.assertEqual(r_json[0]["project"]["pi"], user1.email)

        # Filter by resource type
        r_json = self.admin_client.get(
            f"/api/allocations?resources__resource_type__name={self.resource.resource_type.name}"
        ).json()
        self.assertEqual(len(r_json), 3)
        self.assertEqual(
            r_json[0]["resource"]["resource_type"], self.resource.resource_type.name
        )

        # Filter by 1 attribute with conditional or
        r_json = self.admin_client.get(
            "/api/allocations?attr_{}={}&attr_{}={}".format(
                attributes.QUOTA_LIMITS_CPU,
                aa1.value,
                attributes.QUOTA_LIMITS_CPU,
                aa3.value,
            )
        ).json()
        self.assertEqual(len(r_json), 3)
        self.assertIn(attributes.QUOTA_LIMITS_CPU, r_json[0]["attributes"])

        # Filter by two allocation attributes, with conditional or
        r_json = self.admin_client.get(
            "/api/allocations?attr_{}={}&attr_{}={}".format(
                attributes.QUOTA_LIMITS_CPU,
                aa1.value,
                attributes.QUOTA_LIMITS_MEMORY,
                aa4.value,
            )
        ).json()
        self.assertEqual(len(r_json), 1)
        self.assertEqual(
            r_json[0]["attributes"][attributes.QUOTA_LIMITS_CPU], aa1.value
        )
        self.assertEqual(
            r_json[0]["attributes"][attributes.QUOTA_LIMITS_MEMORY], aa4.value
        )

        # Filter by non-existant attribute
        r_json = self.admin_client.get("/api/allocations?attr_fake=fake").json()
        self.assertEqual(r_json, [])

        r_json = self.admin_client.get(
            "/api/allocations?fake_model_attribute=fake"
        ).json()
        self.assertEqual(r_json, [])
