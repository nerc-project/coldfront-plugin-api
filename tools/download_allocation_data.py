"""
Download ColdFront allocation data.

Usage:
    python3 download_allocation_data.py <coldfront_allocation_api_url> <output_file>

- Environment variables CLIENT_ID and CLIENT_SECRET must be set,
corresponding to a service account in Keycloak.
"""
import json
import logging
import os
import sys

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger()


class ColdFrontClient(object):
    def __init__(self, keycloak_url, keycloak_client_id, keycloak_client_secret):
        self.session = self.get_session(
            keycloak_url, keycloak_client_id, keycloak_client_secret
        )

    @staticmethod
    def get_session(keycloak_url, keycloak_client_id, keycloak_client_secret):
        """Authenticate as a client with Keycloak to receive an access token."""
        token_url = f"{keycloak_url}/auth/realms/mss/protocol/openid-connect/token"

        r = requests.post(
            token_url,
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(keycloak_client_id, keycloak_client_secret),
        )
        client_token = r.json()["access_token"]

        session = requests.session()
        headers = {
            "Authorization": f"Bearer {client_token}",
            "Content-Type": "application/json",
        }
        session.headers.update(headers)
        return session


def main():
    client = ColdFrontClient(
        "https://keycloak.mss.mghpcc.org",
        os.environ.get("CLIENT_ID"),
        os.environ.get("CLIENT_SECRET"),
    )
    r = client.session.get(sys.argv[1])

    with open(sys.argv[2], "w") as output:
        json.dump(r.json(), output)


if __name__ == "__main__":
    main()
