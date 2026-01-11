"""Pytest configuration for the tests directory."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Remove the imported test_dockerfile function from test_docker_ops.py."""
    # test_docker_ops.py imports test_dockerfile function from docker_ops module
    # Pytest treats this as a test when it shouldn't be
    # Filter out module-level test_dockerfile (not in a class)
    filtered = []
    for item in items:
        # Skip module-level test_dockerfile in test_docker_ops.py
        # Real tests are in TestTestDockerfile class (has :: separator)
        if item.nodeid == "tests/test_docker_ops.py::test_dockerfile":
            continue
        filtered.append(item)
    items[:] = filtered
