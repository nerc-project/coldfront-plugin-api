from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AllocationUser
from coldfront.core.project.models import Project, ProjectUser, ProjectUserStatusChoice, ProjectUserRoleChoice

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "A command that adds users who have been assigned allocations to those allocations' project. Made to fix a \
    database inconsistency where a user is assigned to an allocation, but may not have been assigned to the allocation's project. \
    Run this command with no options to see the list of users with this inconsistency. Run with '--apply' to fix them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true", 
            help="Applies changes to database to fix all allocation user inconsistencies"
        )
        return 0
    
    def handle(self, *args, **options):
        
        # Check all allocation users
        for a_user in AllocationUser.objects.filter(status__name="Active"):

            user = a_user.user
            project = a_user.allocation.project
            p_user_list = ProjectUser.objects.filter(user=user) # User maybe assigned to more than 1 project

            is_broken = True
            for p_user in p_user_list:
                if p_user.project == project:
                    is_broken = False
                    break

            if is_broken:
                if options["apply"]:
                    new_p_user = ProjectUser.objects.create(
                        project=a_user.allocation.project,
                        user=user,
                        status=ProjectUserStatusChoice.objects.get(name="Active"),
                        role=ProjectUserRoleChoice.objects.get(name="User"),
                        enable_notifications = True
                    )
                    logger.warn(f"Added User {user.username} to project '{project.title}'")
                else:
                    logger.warn(f"User {user.username} assgined to allocation pk = {a_user.allocation.pk}, but not in allocation's project '{project.title}'")