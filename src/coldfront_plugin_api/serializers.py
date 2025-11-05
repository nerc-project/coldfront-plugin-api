import logging
from datetime import datetime, timedelta

from rest_framework import serializers

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationStatusChoice,
    AllocationAttributeType,
)
from coldfront.core.allocation.models import Project, Resource
from coldfront.core.allocation import signals


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
        fields = ["id", "project", "description", "resource", "status", "attributes"]

    resource = serializers.SerializerMethodField()
    project = ProjectSerializer()
    attributes = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_resource(self, obj: Allocation) -> dict:
        resource = obj.resources.first()
        return {"name": resource.name, "resource_type": resource.resource_type.name}

    def get_attributes(self, obj: Allocation):
        attrs = AllocationAttribute.objects.filter(allocation=obj)
        return {
            a.allocation_attribute_type.name: obj.get_attribute(
                a.allocation_attribute_type.name
            )
            for a in attrs
        }

    def get_status(self, obj: Allocation) -> str:
        return obj.status.name


class AllocationSerializerV2(serializers.ModelSerializer):
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

    def create(self, validated_data):
        project_obj = Project.objects.get(id=validated_data["project"]["id"])
        resource_obj = Resource.objects.get(id=validated_data["resources"][0]["id"])
        allocation = Allocation.objects.create(
            project=project_obj,
            status=validated_data["status"],
            justification="",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
        )
        allocation.resources.add(resource_obj)
        allocation.save()

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
        """
        Only allow updating allocation status for now

        Certain status transitions will have side effects (activating/deactivating allocations)
        """

        old_status = allocation.status.name
        new_status = validated_data.get("status", old_status).name

        allocation.status = validated_data.get("status", allocation.status)
        allocation.save()

        if old_status == "New" and new_status == "Active":
            signals.allocation_activate.send(
                sender=self.__class__, allocation_pk=allocation.pk
            )
        elif old_status == "Active" and new_status in ["Denied", "Revoked"]:
            signals.allocation_disable.send(
                sender=self.__class__, allocation_pk=allocation.pk
            )

        logger.info(
            f"Updated allocation {allocation.id} for project {allocation.project.title}"
        )
        return allocation
