"""Shared pytest configuration for platform-specific regression cases."""

import os

import pytest


_HOST_SPECIFIC_ARCHIVE_TEST = "test_archive_member_with_invalid_host_name_is_a_clean_error"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip the Windows-invalid filename regression where that name is legal.

    The ``....//escape.txt`` fixture exercises Windows trailing-dot path semantics.
    POSIX filesystems can represent that path normally, so requiring ``ValueError`` on
    Linux/macOS would test the operating system rather than BrainForgeMD. A separate
    cross-platform regression test simulates an actual host write failure and verifies
    that BrainForgeMD normalizes it to ``ValueError``.
    """
    if os.name == "nt":
        return

    marker = pytest.mark.skip(reason="fixture is invalid on Windows but legal on POSIX filesystems")
    for item in items:
        if item.name == _HOST_SPECIFIC_ARCHIVE_TEST:
            item.add_marker(marker)
