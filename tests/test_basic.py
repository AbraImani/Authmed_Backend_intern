import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_seed_command_runs(capsys):
    call_command("seed_demo")
    captured = capsys.readouterr()
    assert "Demo data seeded successfully." in captured.out

    nathan = User.objects.get(username="nathan.cirhuza")
    assert nathan.first_name == "Nathan"
    assert nathan.last_name == "Cirhuza"
    assert nathan.email == "nathan@authmed.africa"
    assert nathan.role == "inspector"
    assert nathan.check_password("nathan@authmed.africa")
