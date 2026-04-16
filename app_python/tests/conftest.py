"""
Pytest configuration: isolated VISITS_FILE and clean state per test.
"""

import os
import tempfile

import pytest


def pytest_configure(config):
    fd, path = tempfile.mkstemp(prefix="visits_", suffix=".txt")
    os.close(fd)
    os.environ["VISITS_FILE"] = path


@pytest.fixture(autouse=True)
def _reset_visits_file():
    path = os.environ.get("VISITS_FILE")
    if path and os.path.exists(path):
        os.remove(path)
    yield
