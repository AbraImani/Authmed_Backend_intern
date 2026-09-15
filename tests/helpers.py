from django.contrib.auth import get_user_model
from organizations.models import OrganizationMembership
from organizations.roles import Role


def create_member_user(*, organization=None, role=Role.INSPECTOR, site=None, **kwargs):
    user = get_user_model().objects.create_user(**kwargs)
    if organization is not None:
        OrganizationMembership.objects.create(user=user, organization=organization,
            role=role, primary_site=site, is_active=user.is_active)
    return user


def firebase_token_for(username):
    user = get_user_model().objects.get(username=username)
    if not user.firebase_uid:
        user.firebase_uid = "test-user-" + str(user.pk)
        user.save(update_fields=["firebase_uid"])
    return "test-firebase:" + user.firebase_uid
