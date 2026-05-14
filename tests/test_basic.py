import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_command_runs(capsys):
    call_command("seed_demo")
    captured = capsys.readouterr()
    assert "Demo data seeded." in captured.out
