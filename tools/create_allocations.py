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
import argparse

import requests
from requests.auth import HTTPBasicAuth


API_URL = "http://localhost:8000/api/allocations"


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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "allocations_file",
        help="JSON file containing list of allocations, must adhere to API specifications",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="If set, will also trigger the Coldfront `activate_allocations` signal."
        "For OpenShift and OpenStack allocations, this will create the projects on remote clusters"
        "Only works if the requested status choice is `New`",
    )
    args = parser.parse_args()

    client = ColdFrontClient(
        "https://keycloak.mss.mghpcc.org",
        os.environ.get("CLIENT_ID"),
        os.environ.get("CLIENT_SECRET"),
    )

    with open(args.allocations_file, "r") as f:
        allocation_payloads = json.load(f)

        for allocation_payload in allocation_payloads:
            r = client.session.post(url=API_URL, json=allocation_payload)
            r.raise_for_status()
            allocation_id = r.json()["id"]

            if args.activate:
                allocation_payload["status"] = "Active"
                r = client.session.put(
                    url=f"{API_URL}/{allocation_id}", json=allocation_payload
                )
                r.raise_for_status()

            logger.info(
                f"Created allocation {allocation_id} for project {allocation_payload["project"]["id"]}"
            )


if __name__ == "__main__":
    main()
