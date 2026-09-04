"""Cross-platform archive error normalization regressions."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from brainforgemd.archive import ArchiveLimits, extract_archive


def test_archive_write_oserror_is_normalized_to_value_error(tmp_path: Path, monkeypatch) -> None:
    """Host filesystem write failures must surface as the archive API's ValueError.

    This deliberately simulates the OS refusing a destination write so the behaviour is
    reproducible on Windows, Linux, and macOS instead of depending on one platform's
    filename rules.
    """
    archive_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("folder/member.txt", "payload")

    destination = tmp_path / "dest"
    refused = destination / "folder" / "member.txt"
    real_open = Path.open

    def refusing_open(self: Path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == refused and "w" in mode:
            raise OSError(22, "simulated host filesystem rejection")
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", refusing_open)

    with pytest.raises(ValueError, match="Archive member cannot be written on this host"):
        extract_archive(archive_path, destination, ArchiveLimits())

    assert not refused.exists()
