"""
Usage: register_users_from_csv.py [OPTIONS]

  Create and register users into an allocation.

  Environment variables CLIENT_ID and CLIENT_SECRET must be set, corresponding
  to a service account in Keycloak. (ex. xdmod-client)

Options:
  --csv-file PATH                 The format of the CSV is:
                                  username,firstName,lastName,allocationId
  --add-to-rhods-notebooks-namespace
                                  Add users to the `rhods-notebooks` namespace
                                  (TAs/Profs). Requires `oc` command and
                                  cluster admin access to OpenShift.
  --help                          Show this message and exit.

"""
import csv
import logging
import os
import re
import sys
import time

import click
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScimClient(object):
    def __init__(
        self, scim_url, keycloak_url, keycloak_client_id, keycloak_client_secret
    ):
        self.scim_url = scim_url
        self.keycloak_url = keycloak_url
        self.keycloak_client_id = keycloak_client_id
        self.keycloak_client_secret = keycloak_client_secret
        self.session = self.refresh_session()

    def refresh_session(self):
        """Authenticate as a client with Keycloak to receive an access token."""
        token_url = f"{self.keycloak_url}/auth/realms/mss/protocol/openid-connect/token"

        r = requests.post(
            token_url,
            data={"grant_type": "client_credentials"},
            auth=HTTPBasicAuth(self.keycloak_client_id, self.keycloak_client_secret),
        )
        client_token = r.json()["access_token"]

        session = requests.session()
        headers = {
            "Authorization": f"Bearer {client_token}",
            "Content-Type": "application/json",
        }
        session.headers.update(headers)

        logger.info("Authenticated with Keycloak")
        return session

    def create_user(self, username, first_name, last_name, email):
        """Create a user."""
        url = f"{self.scim_url}/Users/{username}"
        r = self.session.get(url)
        if r.status_code == 200:
            print(f"User {username} exists.")
        if r.status_code in [404, 500]:
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
                ],
            }
            r = self.session.post(f"{self.scim_url}/Users", json=payload)
            if r.status_code == 201:
                print(f"Created user {username}.")
            else:
                logger.error(
                    f"Error creating user {username}: {r.status_code}: {r.text}"
                )
                sys.exit(1)

    def add_user_to_group(self, username, allocation):
        r = self.session.get(f"{self.scim_url}/Groups/{allocation}")
        if r.status_code == 200 and username not in [
            x.get("value") for x in r.json().get("members", {})
        ]:
            payload = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                "Operations": [
                    {"op": "add", "value": {"members": [{"value": username}]}}
                ],
            }
            r = self.session.patch(f"{self.scim_url}/Groups/{allocation}", json=payload)
            if r.status_code in [200, 201]:
                print(f"Added user {username} to allocation {allocation}.")
            else:
                logger.error(f"Error adding user {username}: {r.status_code}: {r.text}")
                sys.exit(1)


def get_sanitized_name(name):
    """
    Returns a sanitized name that only contains lowercase
    alphanumeric characters and dashes (not leading or trailing.)
    """
    name = name.lower()

    # replace special characters with dashes
    name = re.sub("[^a-z0-9-]", "-", name)

    # remove repeated and trailing dashes
    name = re.sub("-+", "-", name).strip("-")
    return name


@click.command(
    help=(
        "Create and register users into an allocation.\n\n"
        "Environment variables CLIENT_ID and CLIENT_SECRET must be set, "
        "corresponding to a service account in Keycloak. (ex. xdmod-client)"
    )
)
@click.option(
    "--csv-file",
    type=click.Path(),
    help="The format of the CSV is: username,firstName,lastName,allocationId",
)
@click.option(
    "--add-to-rhods-notebooks-namespace",
    is_flag=True,
    default=False,
    help=(
        "Add users to the `rhods-notebooks` namespace (TAs/Profs). "
        "Requires `oc` command and cluster admin access to OpenShift."
    ),
)
def main(csv_file, add_to_rhods_notebooks_namespace):
    client = ScimClient(
        "https://coldfront.mss.mghpcc.org/api/scim/v2",
        "https://keycloak.mss.mghpcc.org",
        os.environ.get("CLIENT_ID"),
        os.environ.get("CLIENT_SECRET"),
    )

    with open(csv_file, newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",", quotechar="|")
        for index, row in enumerate(reader):
            logger.info(f"Processing: {row}.")

            client.create_user(
                username=row[0], first_name=row[1], last_name=row[2], email=row[0]
            )
            client.add_user_to_group(username=row[0], allocation=row[3])

            if add_to_rhods_notebooks_namespace:
                logger.info("Adding user to rhods notebooks.")
                sanitized_name = get_sanitized_name(row[0])
                os.system(
                    f"oc -n rhods-notebooks create rolebinding {sanitized_name} --clusterrole=edit --user={row[0]} --as system:admin"
                )

            # Rate-limiting
            time.sleep(0.5)

            if index % 50 == 49:
                client.session = client.refresh_session()


if __name__ == "__main__":
    main()
