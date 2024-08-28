# For onbarding-tools
export KEYCLOAK_USERNAME=admin
export KEYCLOAK_PASSWORD=nomoresecret
export KEYCLOAK_URL="http://localhost:8080"
export OIDC_CLIENT_ID=coldfront
export OIDC_CLIENT_SECRET=nomoresecret
export HORIZON_URL="http://foo"

# For coldfront oidc plugin
export DJANGO_SETTINGS_MODULE="local_settings"
export PLUGIN_AUTH_OIDC=True
export OIDC_RP_CLIENT_ID="coldfront"
export OIDC_RP_CLIENT_SECRET='nomoresecret'
export OIDC_OP_AUTHORIZATION_ENDPOINT="http://localhost:8080/realms/master/protocol/openid-connect/auth"
export OIDC_OP_TOKEN_ENDPOINT="http://localhost:8080/realms/master/protocol/openid-connect/token"
export OIDC_OP_USER_ENDPOINT="http://localhost:8080/realms/master/protocol/openid-connect/userinfo"
export OIDC_RP_SIGN_ALGO='RS256'
export OIDC_OP_JWKS_ENDPOINT="http://localhost:8080/realms/master/protocol/openid-connect/certs"

coldfront test coldfront_plugin_api.tests.functional.test_scim_auth
