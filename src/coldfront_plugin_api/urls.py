import os

from rest_framework import routers, viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAdminUser
from mozilla_django_oidc.contrib.drf import OIDCAuthentication

from coldfront.core.allocation.models import Allocation

from coldfront_plugin_api import serializers

if os.getenv('PLUGIN_AUTH_OIDC') == 'True':
    AUTHENTICATION_CLASSES = [OIDCAuthentication, SessionAuthentication]
else:
    AUTHENTICATION_CLASSES = [SessionAuthentication, BasicAuthentication]


class AllocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.AllocationSerializer
    authentication_classes = AUTHENTICATION_CLASSES
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Allocation.objects.filter(status__name='Active')

        if self.request.query_params.get('all') == 'true':
            queryset = Allocation.objects.all()

        return queryset


router = routers.SimpleRouter()
router.register(r'allocations', AllocationViewSet, basename='api-allocation')

urlpatterns = router.urls
