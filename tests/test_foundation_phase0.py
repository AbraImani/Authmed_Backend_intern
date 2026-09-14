"""Structural regressions: no import-order or migration bypass is permitted."""
import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest
from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("first_import", [
    "inspections.tasks", "inspections.services.processing", "authmed_intern.urls",
])
def test_imports_work_in_a_fresh_process(first_import):
    code = (
        "import django; django.setup(); "
        f"import {first_import}; "
        "import inspections.models, inspections.serializers, inspections.tasks; "
        "import inspections.services.processing, authmed_intern.urls"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=ROOT,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "authmed_intern.test_settings"},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_models_match_migration_graph():
    loader = MigrationLoader(None)
    changes = MigrationAutodetector(
        loader.project_state(), ProjectState.from_apps(apps),
    ).changes(graph=loader.graph)
    assert changes == {}


def test_clean_database_can_apply_all_real_migrations():
    result = subprocess.run(
        [sys.executable, "-B", "manage.py", "migrate", "--noinput", "--verbosity=0",
         "--settings=authmed_intern.test_settings"],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_openapi_is_structurally_valid_and_runs_are_read_only():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    validate_schema(schema)
    assert set(schema["paths"]["/api/processing-runs/"]) == {"get"}
    assert set(schema["paths"]["/api/processing-runs/{id}/"]) == {"get"}
    properties = schema["components"]["schemas"]["InspectionProcessingRun"]["properties"]
    assert "enrichment_summary" not in properties


@pytest.mark.parametrize("filename", ["inspections/models.py", "inspections/serializers.py"])
def test_no_duplicate_methods_in_models_or_serializers(filename):
    tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
            assert len(names) == len(set(names)), node.name
