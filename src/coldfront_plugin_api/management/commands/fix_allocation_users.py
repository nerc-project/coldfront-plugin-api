from django.core.management.base import BaseCommand, CommandError
from coldfront.core.allocation.models import Allocation, AllocationUser, AllocationUserStatusChoice
from coldfront.core.project.models import Project, ProjectUser, ProjectUserStatusChoice, ProjectUserRoleChoice

import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "A Fix command that adds users assigned to allocations to the project that those allocations belong to"

    def handle(self, *args, **options):
        self.stdout.write(
                self.style.SUCCESS('TESTING FIX COMMAND')
            )
        
        # Check all allocations
        for a_user in AllocationUser.objects.filter(status__name="Active"):
            user = a_user.user
            p_user = ProjectUser.objects.filter(user=user)
            if not p_user:

                logger.warn("User not in project of allocation")
                # new_p_user = ProjectUser.objects.create(
                #     project=a_user.allocation.project,
                #     user=user,
                #     status=ProjectUserStatusChoice.objects.get(name="Active"),
                #     role=ProjectUserRoleChoice.objects.get(name="User"),
                #     enable_notifications = True
                # )

        # Add to project