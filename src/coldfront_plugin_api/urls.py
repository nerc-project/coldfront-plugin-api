from rest_framework import routers, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from django.db.models import Q
from django.core.exceptions import FieldError
from coldfront.core.allocation.models import Allocation
from django_scim import views as scim_views

from coldfront_plugin_api import auth, serializers


class AllocationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset implements the API to Coldfront's allocation object
    The API allows filtering allocations by any of Coldfront's allocation model attributes,
    as well as by Allocation Attributes.

    Filtering by allocation model attributes
    (i.e by pk, start_date, or even by attributes that span relationships, like project PI email)
    is possible by using the query parameters directly as Django query filters.

    For example, to filter by the allocation's project PI email: "/api/allocations?project__pi__email=test@bu.edu"

    Filtering using this method requires knowledge of the Allocation model schema and Django's filters
    Documentation of Coldfront Allocation model: https://coldfront.readthedocs.io/en/latest/apidocs/allocations/
    Documentation for Django's query syntax: https://docs.djangoproject.com/en/5.0/topics/db/queries/#lookups-that-span-relationships

    To filter by allocation attribute (AA) (i.e Quota Limits CPU),
    name the query as the AA (case insensitive), prefixed with "attr_"

    For all filters, you can also filter with conditional OR for the same model attribute or AA
    I.e, to find allocations with AA Quota Limits CPU equal to 2 OR 4:
    "/api/allocations?attr_quota limits cpu=2&attr_quota limits cpu=4"
    Note the presence of spaces in the AA names

    Filtering with conditional AND on two or more attributes is also possible
    I.e, to filter for allocations with AA Quota Limits CPU equal 2 AND Quota RAM equals 4G:
    "/api/allocations?attr_quota limits cpu=2&attr_quota ram=4G"

    In cases where an invalid model attribute or AA is queried, an empty list is returned
    """

    serializer_class = serializers.AllocationSerializer
    authentication_classes = auth.AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Allocation.objects.filter(status__name="Active")
        query_params = self.request.query_params

        if query_params.get("all") == "true":
            queryset = Allocation.objects.all()

        allocation_attr_prefix = "attr_"

        for query, val in query_params.items():
            if query == "all":
                continue
            if query.startswith(allocation_attr_prefix):
                attribute_query = query[len(allocation_attr_prefix) :]
                val_list = query_params.getlist(query)

                # Using Django's Q object to create OR query for attribute
                # https://docs.djangoproject.com/en/5.0/topics/db/queries/#complex-lookups-with-q-objects
                q_query = Q()
                for val in val_list:
                    q_query = q_query | Q(allocationattribute__value=val)

                queryset = queryset.filter(
                    q_query,
                    allocationattribute__allocation_attribute_type__name__iexact=attribute_query,
                )

            else:
                val_list = query_params.getlist(query)
                q_query = Q()
                for val in val_list:
                    q_query = q_query | Q(**{query: val})

                try:
                    queryset = queryset.filter(q_query)
                except FieldError:
                    queryset = queryset.none()

        return queryset


app_name = "scim"

router = routers.SimpleRouter(trailing_slash=False)
router.register(r"allocations", AllocationViewSet, basename="api-allocation")

urlpatterns = router.urls

urlpatterns += [
    path("scim/v2/Groups", scim_views.GroupsView.as_view(), name="groups"),
    path("scim/v2/Groups/<int:uuid>", scim_views.GroupsView.as_view(), name="groups"),
    path("scim/v2", scim_views.SCIMView.as_view(implemented=False), name="root"),
    path("scim/v2/Users", scim_views.UsersView.as_view(), name="users"),
    path("scim/v2/Users/<str:uuid>", scim_views.UsersView.as_view(), name="users"),
]
urlpatterns = format_suffix_patterns(urlpatterns)
