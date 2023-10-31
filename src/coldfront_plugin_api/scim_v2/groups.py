from coldfront.core.allocation import signals
from coldfront.core.allocation.models import Allocation, AllocationUser, AllocationUserStatusChoice
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from coldfront_plugin_api import auth, utils


def allocation_to_group_view(allocation: Allocation) -> dict:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": allocation.pk,
        "displayName": f"Members of allocation {allocation.pk} of project {allocation.project.title}",
        "members": [
            {
                "value": x.user.username,
                "$ref": x.user.username,
                "display": x.user.username,
            } for x in AllocationUser.objects.filter(allocation=allocation,status__name="Active")
        ]
    }


class ListGroups(APIView):
    """
    View to list all groups in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = auth.AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all groups.
        """
        allocations = Allocation.objects.filter(status__name="Active")
        return Response(
            [allocation_to_group_view(allocation) for allocation in allocations]
        )


class GroupDetail(APIView):
    """
    View to list all groups in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = auth.AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get(self, request, pk, format=None):
        allocation = Allocation.objects.get(pk=pk)
        return Response(allocation_to_group_view(allocation))

    def patch(self, request, pk, format=None):
        if (
                request.data["schemas"] != ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]
                or request.data.get("path", "members") != "members"
        ):
            return Response(status=400)

        allocation = Allocation.objects.get(pk=pk)
        for operation in request.data["Operations"]:
            value = operation["value"]
            if type(value) == dict:
                value = [x["value"] for x in operation["value"]["members"]]
            elif type(value) == list:
                value = [x["value"] for x in operation["value"]]

            if operation["op"] == "add":
                for submitted_user in value:
                    try:
                        user = utils.get_or_fetch_user(username=submitted_user)
                    except ObjectDoesNotExist:
                        return Response(status=400)

                    au = self._set_user_status_on_allocation(
                        allocation, user, "Active"
                    )
                    signals.allocation_activate_user.send(
                        sender=self.__class__, allocation_user_pk=au.pk,
                    )
            elif operation["op"] == "remove":
                for submitted_user in value:
                    user = User.objects.get(username=submitted_user)
                    au = self._set_user_status_on_allocation(
                        allocation, user, "Removed"
                    )
                    signals.allocation_remove_user.send(
                        sender=self.__class__, allocation_user_pk=au.pk,
                    )
            else:
                # Replace is not implemented yet.
                raise NotImplementedError

        return Response(allocation_to_group_view(allocation))

    @staticmethod
    def _set_user_status_on_allocation(allocation, user, status):
        au = AllocationUser.objects.filter(
            allocation=allocation,
            user=user
        ).first()
        if au:
            au.status = AllocationUserStatusChoice.objects.get(name=status)
            au.save()
        else:
            au = AllocationUser.objects.create(
                allocation=allocation,
                user=user,
                status=AllocationUserStatusChoice.objects.get(name=status)
            )
        return au
