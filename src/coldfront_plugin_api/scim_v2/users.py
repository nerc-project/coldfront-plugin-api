from django.contrib.auth.models import User
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from coldfront_plugin_api import auth, utils


def user_to_api_representation(user: User) -> dict:
    return {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user.username,
        "externalId": user.username,
        "userName": user.username,
        "name": {
            "givenName": user.first_name,
            "familyName": user.last_name,
        },
        "emails": [
            {
                "value": user.email,
                "type": "work",
                "primary": True,
            }
        ],
        "meta": {
            "resourceType": "User",
            "created": user.date_joined,
        },
    }


class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = auth.AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        users = User.objects.all()
        return Response(
            [user_to_api_representation(user) for user in users]
        )

    def post(self, request, format=None):
        """
        Create a new user.

        At a minimum, payload needs to contain the following:
        {
            "schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName":"fake-user-1"
        }

        If user exists through one of the configured search providers,
        additional information will be fetched from there.

        Otherwise, for setting the attributes manually, please see function
        user_to_api_representation for example payload.
        """
        username = request.data.get("userName", "")

        if (
            request.data["schemas"] != ["urn:ietf:params:scim:schemas:core:2.0:User"]
            or not username
            or len(username.split()) > 1
        ):
            return Response(status=400)

        # Attempt to fetch the user from the search provider
        found = utils.find_user(username)

        # If the user is not found in the search provider,
        # allow the API client to specify the values that would have
        # otherwise been fetched.
        # This allows preregistering a user that doesn't have a corresponding
        # identity provider yet.
        if not found:
            name_dict = request.data.get("name", {})
            email_list = request.data.get("emails", [{}])
            found = {
                "username": username,
                "first_name": name_dict.get("givenName", ""),
                "last_name": name_dict.get("familyName", ""),
                "email": email_list[0].get("value", "")
            }

        user = utils.create_user(**found)

        return Response(user_to_api_representation(user), 201)


class UserDetail(APIView):
    """
    View to query a specific user in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    authentication_classes = auth.AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get(self, request, username, format=None):
        try:
            allocation = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=404)
        return Response(user_to_api_representation(allocation))
