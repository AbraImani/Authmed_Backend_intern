from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import User
from .serializers import UserSerializer, MeSerializer
from authmed_intern.permissions import TenantPermission
from organizations.tenancy import TenantQuerysetMixin, get_active_membership

class UserViewSet(TenantQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    read_capability = "members"

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=MeSerializer, parameters=[OpenApiParameter("X-Organization-ID", int, OpenApiParameter.HEADER, description="Select an organization with an active local membership.")])
    def get(self, request):
        membership = get_active_membership(request, required=False)
        return Response(MeSerializer(request.user, context={"membership": membership}).data)
