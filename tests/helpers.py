from django.contrib.auth import get_user_model
from organizations.models import OrganizationMembership


def create_member_user(**kwargs):
    user = get_user_model().objects.create_user(**kwargs)
    if user.organization_id:
        OrganizationMembership.objects.create(
            user=user, organization=user.organization, role=user.role,
            primary_site=user.site, is_active=user.is_active,
        )
    return user
