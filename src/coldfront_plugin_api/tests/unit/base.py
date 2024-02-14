import sys
from os import devnull
import uuid

from coldfront.core.allocation.models import (
    Allocation,
    AllocationStatusChoice,
    AllocationUser,
    AllocationUserStatusChoice,
)

from django.contrib.auth.models import User
from coldfront.core.project.models import (
    Project,
    ProjectUser,
    ProjectUserRoleChoice,
    ProjectUserStatusChoice,
    ProjectStatusChoice,
)
from django.core.management import call_command
from django.test import TestCase


class TestBase(TestCase):
    def setUp(self) -> None:
        # Otherwise output goes to the terminal for every test that is run
        backup, sys.stdout = sys.stdout, open(devnull, "a")
        call_command("initial_setup", "-f")
        call_command("load_test_data")
        call_command("register_cloud_attributes")
        sys.stdout = backup

    @staticmethod
    def new_user(username=None) -> User:
        username = username or f"{uuid.uuid4().hex}@example.com"
        User.objects.create(username=username, email=username)
        return User.objects.get(username=username)

    def new_project(self, title=None, pi=None) -> Project:
        title = title or uuid.uuid4().hex
        pi = pi or self.new_user()
        status = ProjectStatusChoice.objects.get(name="New")

        Project.objects.create(title=title, pi=pi, status=status)
        return Project.objects.get(title=title)

    @staticmethod
    def new_project_user(user, project, role="Manager", status="Active"):
        pu, _ = ProjectUser.objects.get_or_create(
            user=user,
            project=project,
            role=ProjectUserRoleChoice.objects.get(name=role),
            status=ProjectUserStatusChoice.objects.get(name=status),
        )
        return pu

    @staticmethod
    def new_allocation(project, resource, quantity):
        allocation, _ = Allocation.objects.get_or_create(
            project=project,
            justification="a justification for testing data",
            quantity=quantity,
            status=AllocationStatusChoice.objects.get(name="Active"),
        )
        allocation.resources.add(resource)
        return allocation

    @staticmethod
    def new_allocation_user(allocation, user):
        au, _ = AllocationUser.objects.get_or_create(
            allocation=allocation,
            user=user,
            status=AllocationUserStatusChoice.objects.get(name="Active"),
        )
        return au
