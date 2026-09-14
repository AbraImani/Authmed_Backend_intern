from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer
from authmed_intern.permissions import IsAdminRole


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
