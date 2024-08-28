from django.core.management import call_command

from coldfront.core.allocation.models import (
    AllocationUser,
    Allocation,
    AllocationUserStatusChoice,
)
from coldfront.core.project.models import ProjectUser
from coldfront_plugin_api.tests import base

from unittest.mock import patch


class TestFixAllocation(base.TestBase):
    @patch("coldfront_plugin_api.management.commands.fix_allocation_users.logger")
    def test_command_output(self, mock_logger):
        call_command("fix_allocation_users")
        self.assertEqual(0, mock_logger.warn.call_count)

        user = self.new_user()
        allocation = Allocation.objects.first()

        # Test with inconsistency
        AllocationUser.objects.create(
            user=user,
            allocation=allocation,
            status=AllocationUserStatusChoice.objects.get(name="Active"),
        )

        call_command("fix_allocation_users")
        call_args = mock_logger.warn.call_args.args
        self.assertIn(user.username, call_args[0])
        self.assertIn("pk = " + str(allocation.pk), call_args[0])

        # Test for project that user is not assigned to it
        project = allocation.project
        p_user = ProjectUser.objects.filter(project=project).filter(user=user)
        self.assertFalse(p_user.exists())

        # Test --apply
        call_command("fix_allocation_users", "--apply")
        p_user = ProjectUser.objects.filter(project=project).filter(user=user)
        self.assertTrue(p_user.exists())
