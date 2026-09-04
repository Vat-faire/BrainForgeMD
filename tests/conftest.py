"""Pytest configuration for regression cases superseded by portable replacements."""

import pytest


_SUPERSEDED_TESTS = {
    "test_archive_member_with_invalid_host_name_is_a_clean_error",
    "test_archive_members_differing_only_by_case_are_reported",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Retire host-dependent assertions replaced by stronger portable regressions.

    ``tests/test_archive_portability.py`` now simulates a real host write rejection and
    requires case-only plus Unicode-normalization collisions to be refused identically on
    Windows, Linux, and macOS. Keeping the older platform-dependent expectations active
    would require the same archive to behave differently by operating system.
    """
    marker = pytest.mark.skip(reason="superseded by deterministic cross-platform archive tests")
    for item in items:
        if item.name in _SUPERSEDED_TESTS:
            item.add_marker(marker)
