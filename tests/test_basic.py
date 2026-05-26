"""
AuthMed Basic Functionality Tests

Imports:
- pytest: Testing framework with Django integration and fixtures
- django.core.management.call_command: Utility to run Django management commands

Tests basic functionality including management commands for seeding demo data.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_command_runs(capsys):
    """Test seed_demo management command creates demo data and outputs success message.
    
    Verifies that the seed_demo command initializes demo data and displays confirmation.
    """
    call_command("seed_demo")
    captured = capsys.readouterr()
    assert "Demo data seeded." in captured.out
