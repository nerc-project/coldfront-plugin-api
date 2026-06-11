from rest_framework import serializers

from coldfront.core.allocation.models import Allocation, AllocationAttribute
from coldfront.core.project.models import Project, ProjectAttribute


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "pi",
            "description",
            "field_of_science",
            "status",
            "attributes",
        ]

    pi = serializers.SerializerMethodField()
    field_of_science = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    # is_externally_funded = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()

    def get_pi(self, obj: Project) -> str:
        return obj.pi.email

    def get_field_of_science(self, obj: Project) -> str:
        return obj.field_of_science.description

    def get_status(self, obj: Project) -> str:
        return obj.status.name

    def get_attributes(self, obj: Project):
        attrs = ProjectAttribute.objects.filter(project=obj)
        return {a.proj_attr_type.name: a.value for a in attrs}

    # def get_is_externally_funded(self, obj: Project) -> bool | None:
    #     is_externally_funded_attr = ProjectAttribute.objects.filter(
    #         project=obj, proj_attr_type__name="Is Externally Funded"
    #     ).first()
    #     return (
    #         is_externally_funded_attr.value.lower() == "yes"
    #         if is_externally_funded_attr
    #         else None
    #     )


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
