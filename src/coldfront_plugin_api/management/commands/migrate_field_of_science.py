import csv

from django.core.management.base import BaseCommand
from coldfront.core.project.models import Project
from coldfront.core.field_of_science.models import FieldOfScience

import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """Migrates Coldfront's list of fields of sciences (fos), changing what
    fos a project can be assigned to, and updating the fos in all existing projects.

    Requires a csv, tab-seperated, containing two columns, the first containing the list of old fos,
    the second containing the new fos that the old fos will map onto.

    I.e to map 'Quantum Mechanics' and 'Photonics' to 'Physics', provide this csv:
        Quantum Mechanics   Physics
        Photonics   Physics
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--mapping",
            required=True,
            help="required tab-seperated csv file to provide mapping for migration",
        )

    def handle(self, *args, **options):
        mapping_csv = options["mapping"]
        mapping_dict, new_fos_set = self._load_fos_map(mapping_csv)
        self._validate_old_fos(mapping_dict)
        self._create_new_fos(new_fos_set)
        self._migrate_fos(mapping_dict)

        logger.info("Fos migration completed!")

    @staticmethod
    def _load_fos_map(mapping_csv):
        mapping_dict = dict()
        new_fos_set = set()
        with open(mapping_csv, "r") as f:
            rd = csv.reader(f, delimiter="\t")
            for row in rd:
                old_fos, new_fos = row
                mapping_dict[old_fos] = new_fos
                new_fos_set.add(new_fos)

        return [mapping_dict, new_fos_set]

    @staticmethod
    def _validate_old_fos(mapping_dict):
        for old_fos_name in list(mapping_dict.keys()):
            if not FieldOfScience.objects.filter(description=old_fos_name):
                logger.warn(f"Old field of science {old_fos_name} does not exist")

    @staticmethod
    def _create_new_fos(new_fos_set):
        for new_fos_name in new_fos_set:
            FieldOfScience.objects.get_or_create(
                is_selectable=True,  # Assuming we want all new fos to be selectable
                description=new_fos_name,  # Also assuming we don't care about NSF codes
            )

    @staticmethod
    def _migrate_fos(mapping_dict):
        # Migrate all projects to new fos
        for project in Project.objects.all():
            cur_fos_name = project.field_of_science.description
            if cur_fos_name in mapping_dict.keys():
                new_fos_name = mapping_dict[cur_fos_name]
                new_fos = FieldOfScience.objects.get(description=new_fos_name)
                project.field_of_science = new_fos
                project.save()
                logger.info(
                    f"Migrated fos for project {project.pk} from {cur_fos_name} to {new_fos_name}"
                )

        # Remove old fos from database
        for old_fos_name in list(mapping_dict.keys()):
            FieldOfScience.objects.get(description=old_fos_name).delete()
