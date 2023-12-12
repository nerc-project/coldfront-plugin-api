# Coldfront API Plugin
REST API plugin for ColdFront.

See `openapi.yaml` for OpenAPI specification.

ColdFront doesn't currently provide a mechanism for allowing out of tree
plugins to expose URLs, so applying the patch file at
`patches/01_add_api_urls.patch` is required.

The plugin can be enabled by adding `coldfront_plugin_api` to `INSTALLED_APPS`
in the Django `local_settings.py`.

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
