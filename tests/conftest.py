"""Shared pytest configuration for superseded host-specific regression cases."""

import os

import pytest


_WINDOWS_INVALID_NAME_TEST = "test_archive_member_with_invalid_host_name_is_a_clean_error"
_SUPERSEDED_CASE_COLLISION_TEST = "test_archive_members_differing_only_by_case_are_reported"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip regressions whose original assertions depended on host filesystem semantics.

    Each skipped case has a stricter portable replacement in
    ``tests/test_archive_portability.py``. The Windows-invalid-name fixture is legal on
    POSIX hosts. The original case-collision test also expected different behaviour on
    different operating systems; BrainForgeMD now deliberately rejects non-portable
    case-only archive collisions everywhere so the same archive cannot yield different
    corpora by host OS.
    """
    for item in items:
        if item.name == _SUPERSEDED_CASE_COLLISION_TEST:
            item.add_marker(
                pytest.mark.skip(reason="superseded by deterministic cross-platform collision test")
            )
        elif item.name == _WINDOWS_INVALID_NAME_TEST and os.name != "nt":
            item.add_marker(
                pytest.mark.skip(reason="fixture is invalid on Windows but legal on POSIX filesystems")
            )
