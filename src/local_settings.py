# This file is only provided for testing!
# ColdFront Plugin Cloud is only imported as a utility to make use of its
# testing classes and functions and is not required for the operation
# of this plugin.
import os
import pkgutil

from coldfront.config.settings import *  # noqa: F403
from django.conf import settings  # noqa: F401

plugin_cloud = pkgutil.get_loader("coldfront_plugin_cloud.config")
include(plugin_cloud.get_filename())  # noqa: F405

plugin_api = pkgutil.get_loader("coldfront_plugin_api.config")
include(plugin_api.get_filename())  # noqa: F405


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

if os.getenv("PLUGIN_AUTH_OIDC") == "True":
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"].append(
        "mozilla_django_oidc.contrib.drf.OIDCAuthentication",
    )

# Settings for django_scim module
SCIM_SERVICE_PROVIDER = {
    "NETLOC": "localhost",
    "USER_ADAPTER": "coldfront_plugin_api.scim_v2.adapter_user.SCIMColdfrontUser",
    "USER_FILTER_PARSER": "coldfront_plugin_api.scim_v2.filters.ColdfrontUserFilterQuery",
    "GROUP_MODEL": "coldfront.core.allocation.models.Allocation",  # Because our SCIM Group is an allocation
    "GROUP_ADAPTER": "coldfront_plugin_api.scim_v2.adapter_group.SCIMColdfrontGroup",
    "GROUP_FILTER_PARSER": "coldfront_plugin_api.scim_v2.filters.ColdfrontGroupFilterQuery",
    "GET_IS_AUTHENTICATED_PREDICATE": "coldfront_plugin_api.utils.is_user_superuser",
}
