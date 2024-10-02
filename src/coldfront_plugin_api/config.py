from coldfront.config.base import INSTALLED_APPS
from coldfront.config.env import ENV  # noqa: F401

for app in ["rest_framework", "coldfront_plugin_api", "django_scim"]:
    if app not in INSTALLED_APPS:
        INSTALLED_APPS.append(app)

# Settings for django_scim module
SCIM_SERVICE_PROVIDER = {
    "NETLOC": "localhost",
    "USER_ADAPTER": "coldfront_plugin_api.scim_v2.adapter_user.SCIMColdfrontUser",
    "USER_FILTER_PARSER": "coldfront_plugin_api.scim_v2.filters.ColdfrontUserFilterQuery",
    "GROUP_MODEL": "coldfront.core.allocation.models.Allocation",  # Because our SCIM Group is an allocation
    "GROUP_ADAPTER": "coldfront_plugin_api.scim_v2.adapter_group.SCIMColdfrontGroup",
    "GROUP_FILTER_PARSER": "coldfront_plugin_api.scim_v2.filters.ColdfrontGroupFilterQuery",
    "GET_IS_AUTHENTICATED_PREDICATE": "coldfront_plugin_api.utils.is_user_superuser",
    "AUTH_CHECK_MIDDLEWARE": "coldfront_plugin_api.scim_v2.auth_middleware.SCIMColdfrontAuthCheckMiddleware",
}
