"""
Create and register users into an allocation.

Usage:
    python3 register_users_from_csv.py <input.csv> <scim_v2_base_url>

Configuration:
- The format of the CSV is:
username,firstName,lastName,allocationId

- Environment variables CLIENT_ID and CLIENT_SECRET must be set,
corresponding to a service account in Keycloak.
"""
import csv
import logging
import os
import re
import sys

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger()


class ScimClient(object):

    def __init__(self, scim_url, keycloak_url, keycloak_client_id,
                 keycloak_client_secret):
        self.scim_url = scim_url
        self.session = self.get_session(keycloak_url,
                                        keycloak_client_id,
                                        keycloak_client_secret)

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

    def create_user(self, username, first_name, last_name, email):
        """Create a user."""
        url = f"{self.scim_url}/Users/{username}"
        r = self.session.get(url)
        if r.status_code == 200:
            print(f"User {username} exists.")
        if r.status_code == 404:
            print(f"Creating user {username}.")
            payload = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": username,
                "name": {
                    "givenName": first_name,
                    "familyName": last_name,
                },
                "emails": [
                    {
                        "value": email,
                        "type": "work",
                        "primary": True,
                    }
                ]
            }
            r = self.session.post(
                f"{self.scim_url}/Users",
                json=payload
            )
            if r.status_code == 201:
                print(f"Created user {username}.")

    def add_user_to_group(self, username, allocation):
        r = self.session.get(
            f"{self.scim_url}/Groups/{allocation}"
        )
        if r.status_code == 200 and username not in [
            x.get("value") for x in r.json().get("members", {})
        ]:
            payload = {
                "schemas": [
                    "urn:ietf:params:scim:api:messages:2.0:PatchOp"
                ],
                "Operations": [
                    {
                        "op": "add",
                        "value": {
                            "members": [
                                {
                                    "value": username
                                }
                            ]
                        }
                    }
                ]
            }
            r = self.session.patch(
                f"{self.scim_url}/Groups/{allocation}",
                json=payload
            )
            if r.status_code in [200, 201]:
                print(f"Added user {username} to allocation {allocation}.")


def get_sanitized_name(name):
    '''
    Returns a sanitized name that only contains lowercase
    alphanumeric characters and dashes (not leading or trailing.)
    '''
    name = name.lower()

    # replace special characters with dashes
    name = re.sub('[^a-z0-9-]', '-', name)

    # remove repeated and trailing dashes
    name = re.sub('-+', '-', name).strip('-')
    return name


def main():
    client = ScimClient(
        sys.argv[2],
        "https://keycloak.mss.mghpcc.org",
        os.environ.get('CLIENT_ID'),
        os.environ.get('CLIENT_SECRET')
    )

    with open(sys.argv[1], newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            print(f"Processing: {row}.")

            client.create_user(username=row[0],
                               first_name=row[1],
                               last_name=row[2],
                               email=row[0])
            client.add_user_to_group(username=row[0],
                                     allocation=row[3])

            # Add to rhods-notebook namespace
            sanitized_name = get_sanitized_name(row[0])
            os.system(f"oc -n rhods-notebooks create rolebinding {sanitized_name} --role=edit --user={row[0]}")


if __name__ == "__main__":
    main()
