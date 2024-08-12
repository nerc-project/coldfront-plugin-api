from coldfront.core.user import utils as user_utils
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def find_user(username):
    """Searches for a user in the configured search providers."""
    search = user_utils.CombinedUserSearch(username, "username_only")
    results = search.search().get("matches")

    found = None
    if results:
        for entry in results:
            if entry.get("username") == username:
                found = entry

    return found


def create_user(username, first_name, last_name, email):
    user_obj, _ = User.objects.get_or_create(username=username)
    user_obj.first_name = first_name
    user_obj.last_name = last_name
    user_obj.email = email
    user_obj.save()

    return user_obj


def get_or_fetch_user(username):
    """
    Gets user from ColdFront, or creates it with information from configured
    search providers based on the username.

    Example: If ColdFront is configured to search for users in Keycloak, and
    the user doesn't exist in ColdFront yet, but does in Keycloak, this method
    will create the user in ColdFront with the information returned from
    the identity provider.
    """
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        found = find_user(username)
        if not found:
            raise

        user = create_user(
            username=username,
            first_name=found.get("first_name", ""),
            last_name=found.get("last_name", ""),
            email=found.get("email", ""),
        )

    return user


def is_user_superuser(user: User):
    """
    As a temporary hack, this function will handle raising the appropriate 403 error if
    user is authenticated, but not superuser
    """
    if user.is_authenticated and not user.is_staff:
        raise PermissionDenied
    else:
        return user.is_authenticated
