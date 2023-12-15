# Coldfront API Plugin
REST API plugin for ColdFront.

See `openapi.yaml` for OpenAPI specification.

The plugin can be enabled through 2 steps:
1. Add `coldfront_plugin_api` to `INSTALLED_APPS`
in the Django `local_settings.py` file located in this repo. Make sure to enable this
settings file by setting the DJANGO_SETTINGS_MODULE env var to point to the
aforementioned settings file. For more information: [Django settings](https://docs.djangoproject.com/en/4.2/topics/settings/#designating-the-settings)

2. Since ColdFront doesn't currently provide a mechanism for allowing out of tree
plugins to expose URLs, apply the patch file at
`patches/01_add_api_urls.patch` to `config/urls.py` in the Coldfront package
after installing it.

If the environment variable `PLUGIN_AUTH_OIDC` is detected, authentication
will be done through `mozilla-django-oidc`, using the same configuration
as the rest of ColdFront.

**Note**: If using service accounts and Keycloak, it is necessary to add
`openid` to the client scope of the service account performing the API
request.  This step is because  the `mozilla-django-oidc` Django Rest
Framework implementation uses the `userinfo` endpoint to validate tokens and
that endpoint [requires] `openid` scope. If you're receiving a 403 Forbidden
and wondering why, that might be the cause. For more information, see
[client scope documentation].

[requires]: https://github.com/keycloak/keycloak/pull/14237
[client scope documentation]: https://access.redhat.com/documentation/en-us/red_hat_single_sign-on_continuous_delivery/2/html/server_administration_guide/clients#client_scopes
