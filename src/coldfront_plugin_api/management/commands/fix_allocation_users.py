from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationUser
from coldfront.core.project.models import (
    ProjectUser,
    ProjectUserStatusChoice,
    ProjectUserRoleChoice,
)

import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Ensures all allocation users belong to their allocation's project.
    Run with no arguements to only see which allocation users will be added to projects"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Applies changes to database by adding allocation users to projects",
        )

    def handle(self, *args, **options):
        # Check all allocation users
        for a_user in AllocationUser.objects.filter(status__name="Active"):
            user = a_user.user
            project = a_user.allocation.project
            p_user = ProjectUser.objects.filter(
                user=user, project=project
            )  # User maybe assigned to more than 1 project

            if not p_user:
                if options["apply"]:
                    ProjectUser.objects.create(
                        project=project,
                        user=user,
                        status=ProjectUserStatusChoice.objects.get(name="Active"),
                        role=ProjectUserRoleChoice.objects.get(name="User"),
                        enable_notifications=True,
                    )
                    logger.warn(
                        f"Added User {user.username} to project '{project.title}'"
                    )
                else:
                    logger.warn(
                        f"User {user.username} assgined to allocation pk = {a_user.allocation.pk}, but not in allocation's project '{project.title}'"
                    )
