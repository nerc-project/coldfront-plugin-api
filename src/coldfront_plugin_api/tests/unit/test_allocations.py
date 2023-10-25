import json
import os
import unittest
from os import devnull
import sys

from coldfront_plugin_api import urls

from coldfront.core.allocation import models as allocation_models
from django.core.management import call_command
from coldfront_plugin_cloud.tests import base
from rest_framework.test import APIClient


class TestAllocation(base.TestBase):

    def setUp(self) -> None:
        # Otherwise output goes to the terminal for every test that is run
        backup, sys.stdout = sys.stdout, open(devnull, "a")
        call_command("initial_setup", "-f")
        call_command("load_test_data")
        call_command("register_cloud_attributes")
        sys.stdout = backup

        self.resource = self.new_resource(name="Devstack",
                                          auth_url="http://localhost")

    @property
    def admin_client(self):
        client = APIClient()
        client.login(username='admin', password='test1234')
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
        allocation.status = allocation_models.AllocationStatusChoice.objects.get(name="Expired")
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
