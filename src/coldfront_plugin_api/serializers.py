from rest_framework import serializers

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationStatusChoice,
    AllocationAttributeType,
)
from coldfront.core.allocation.models import Project, Resource


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "pi", "description", "field_of_science", "status"]

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
        fields = ["allocation_attribute_type", "value"]

    allocation_attribute_type = serializers.SlugRelatedField(
        read_only=False,
        slug_field="name",
        queryset=AllocationAttributeType.objects.all(),
    )
    value = serializers.CharField(read_only=False)


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = [
            "id",
            "project",
            "project_id",
            "description",
            "resource",
            "resources_id",
            "status",
            "allocationattribute_set",
        ]
        read_only_fields = ["status"]

    # Seperate serializer fields for reading and writing projects and resources
    resource = serializers.SerializerMethodField()
    resources_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Resource.objects.all(), source="resources", many=True
    )

    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Project.objects.all(),
        source="project",
    )

    allocationattribute_set = AllocationAttributeSerializer(many=True, required=False)

    def get_resource(self, obj: Allocation) -> dict:
        resource = obj.resources.first()
        return {"name": resource.name, "resource_type": resource.resource_type.name}

    def get_status(self, obj: Allocation) -> str:
        return obj.status.name

    def create(self, validated_data):
        allocation = Allocation.objects.create(
            project=validated_data["project"],
            status=AllocationStatusChoice.objects.get(
                name="Active"
            ),  # TODO: What should be the default status choice
        )
        allocation.resources.add(validated_data["resources"][0])
        allocation.save()

        allocation_attributes = validated_data.pop("allocationattribute_set", [])
        for attribute in allocation_attributes:
            AllocationAttribute.objects.create(
                allocation=allocation,
                allocation_attribute_type=attribute["allocation_attribute_type"],
                value=attribute["value"],
            )

        return allocation
