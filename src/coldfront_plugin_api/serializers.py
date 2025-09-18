import logging

from rest_framework import serializers

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationStatusChoice,
    AllocationAttributeType,
)
from coldfront.core.allocation.models import Project, Resource


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "pi", "description", "field_of_science", "status"]
        read_only_fields = ["title", "pi", "description", "field_of_science", "status"]

    id = serializers.IntegerField()
    pi = serializers.SerializerMethodField()
    field_of_science = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_pi(self, obj: Project) -> str:
        return obj.pi.email

    def get_field_of_science(self, obj: Project) -> str:
        return obj.field_of_science.description

    def get_status(self, obj: Project) -> str:
        return obj.status.name


class AllocationAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationAttribute
        fields = ["attribute_type", "value"]

    attribute_type = (
        serializers.SlugRelatedField(  # Peforms validation to ensure attribute exists
            read_only=False,
            slug_field="name",
            queryset=AllocationAttributeType.objects.all(),
            source="allocation_attribute_type",
        )
    )
    value = serializers.CharField(read_only=False)


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "name", "resource_type"]

    id = serializers.IntegerField()
    name = serializers.CharField(required=False)
    resource_type = serializers.SerializerMethodField(required=False)

    def get_resource_type(self, obj: Resource):
        return obj.resource_type.name


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = ["id", "project", "description", "resources", "status", "attributes"]

    resources = ResourceSerializer(many=True)
    project = ProjectSerializer()
    attributes = AllocationAttributeSerializer(
        many=True, source="allocationattribute_set", required=False
    )
    status = serializers.SlugRelatedField(
        slug_field="name", queryset=AllocationStatusChoice.objects.all()
    )

    # TODO (Quan): What about default start/end dates? Default quantity? Description? Justification?

    def create(self, validated_data):
        project_obj = Project.objects.get(id=validated_data["project"]["id"])
        resource_obj = Resource.objects.get(id=validated_data["resources"][0]["id"])
        allocation = Allocation.objects.create(
            project=project_obj, status=validated_data["status"]
        )
        allocation.resources.add(resource_obj)
        allocation.save()

        # TODO (Quan): If the status is `Active`, do we fire the `activate_allocation`
        # signal as well to allow creating the project on remote cluster?

        for attribute in validated_data.pop("allocationattribute_set", []):
            AllocationAttribute.objects.create(
                allocation=allocation,
                allocation_attribute_type=attribute["allocation_attribute_type"],
                value=attribute["value"],
            )

        logger.info(
            f"Created allocation {allocation.id} for project {project_obj.title}"
        )
        return allocation

    def update(self, allocation: Allocation, validated_data):
        """Only allow updating allocation attributes for now"""
        # TODO (Quan) Do we want to allow updating any other allocation properties?
        new_allocation_attributes = validated_data.pop("allocationattribute_set", [])
        for attribute in new_allocation_attributes:
            allocation_attribute, _ = AllocationAttribute.objects.get_or_create(
                allocation=allocation,
                allocation_attribute_type=attribute["allocation_attribute_type"],
            )
            allocation_attribute.value = attribute["value"]
            allocation_attribute.save()

        logger.info(
            f"Updated allocation {allocation.id} for project {allocation.project.title}"
        )
        return allocation
