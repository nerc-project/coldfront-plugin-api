from django_scim.adapters import SCIMGroup
from django_scim import constants, exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from coldfront.core.allocation.models import AllocationUser, AllocationUserStatusChoice
from coldfront.core.project.models import (
    ProjectUser,
    ProjectUserStatusChoice,
    ProjectUserRoleChoice,
)
from coldfront.core.allocation import signals

from coldfront_plugin_api import utils


class SCIMColdfrontGroup(SCIMGroup):
    id_field = "id"

    def handle_operations(self, operations):
        allocation = self.obj
        project = self.obj.project

        # Implement only add and remove
        for operation in operations:
            value = operation["value"]
            if isinstance(value, dict):
                value = [x["value"] for x in operation["value"]["members"]]
            elif isinstance(value, list):
                value = [x["value"] for x in operation["value"]]

            if operation["op"] == "add":
                for submitted_user in value:
                    try:
                        user = utils.get_or_fetch_user(username=submitted_user)
                    except ObjectDoesNotExist:
                        raise exceptions.BadRequestError

                    self._set_user_status_on_project(
                        project, user, "Active", "User", True
                    )

                    au = self._set_user_status_on_allocation(allocation, user, "Active")
                    signals.allocation_activate_user.send(
                        sender=self.__class__,
                        allocation_user_pk=au.pk,
                    )

            elif operation["op"] == "remove":
                for submitted_user in value:
                    user = User.objects.get(username=submitted_user)
                    au = self._set_user_status_on_allocation(
                        allocation, user, "Removed"
                    )
                    signals.allocation_remove_user.send(
                        sender=self.__class__,
                        allocation_user_pk=au.pk,
                    )
            else:
                # Replace is not implemented yet.
                raise NotImplementedError

        return

    def to_dict(self):
        d = {
            "schemas": [constants.SchemaURI.GROUP],
            "id": self.obj.pk,
            "displayName": f"Members of allocation {self.obj.pk} of project {self.obj.project.title}",
            "members": [
                {
                    "value": x.user.username,
                    "$ref": x.user.username,
                    "display": x.user.username,
                }
                for x in AllocationUser.objects.filter(
                    allocation=self.obj, status__name="Active"
                )
            ],
        }

        return d

    def from_dict(self, d):
        # Not needed. Not implemented for now
        return

    @staticmethod
    def _set_user_status_on_allocation(allocation, user, status):
        au = AllocationUser.objects.filter(allocation=allocation, user=user).first()
        if au:
            au.status = AllocationUserStatusChoice.objects.get(name=status)
            au.save()
        else:
            au = AllocationUser.objects.create(
                allocation=allocation,
                user=user,
                status=AllocationUserStatusChoice.objects.get(name=status),
            )
        return au

    @staticmethod
    def _set_user_status_on_project(project, user, status, role, enable_notifications):
        pu = ProjectUser.objects.filter(project=project, user=user).first()

        if pu:
            pu.status = ProjectUserStatusChoice.objects.get(name=status)
            pu.save()
        else:
            pu = ProjectUser.objects.create(
                project=project,
                user=user,
                status=ProjectUserStatusChoice.objects.get(name=status),
                role=ProjectUserRoleChoice.objects.get(name=role),
                enable_notifications=enable_notifications,
            )
        return pu
