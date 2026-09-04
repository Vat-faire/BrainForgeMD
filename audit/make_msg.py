"""Build a synthetic but structurally valid Outlook .msg file.

No Python library writes .msg, so this assembles the Compound File Binary (CFB/OLE2)
container by hand and fills it with the MAPI property streams extract-msg reads. It
exists so the audit can prove the .msg path really converts rather than only that
extract-msg imports.

Usage: python audit/make_msg.py <output.msg>
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

SECTOR = 512
MINI_SECTOR = 64
MINI_CUTOFF = 4096
FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
NOSTREAM = 0xFFFFFFFF

DIR_ENTRY_SIZE = 128
ENTRIES_PER_SECTOR = SECTOR // DIR_ENTRY_SIZE  # 4

STGTY_STORAGE = 1
STGTY_STREAM = 2
STGTY_ROOT = 5


class Entry:
    def __init__(self, name: str, kind: int, data: bytes = b"") -> None:
        self.name = name
        self.kind = kind
        self.data = data
        self.child = NOSTREAM
        self.left = NOSTREAM
        self.right = NOSTREAM
        self.start = ENDOFCHAIN
        self.size = 0


def _utf16(text: str) -> bytes:
    return text.encode("utf-16-le")


def _chain(count: int, first: int) -> list[int]:
    """FAT entries for a `count`-sector chain starting at index `first`."""
    return [first + i + 1 for i in range(count - 1)] + [ENDOFCHAIN]


def build_msg(subject: str, sender: str, to: str, body: str) -> bytes:
    # 0037001F subject, 0C1A001F sender name, 0E04001F display-to, 1000001F body.
    # 001F is the PT_UNICODE property type, so payloads are UTF-16LE.
    streams = [
        ("__substg1.0_0037001F", _utf16(subject)),
        ("__substg1.0_0C1A001F", _utf16(sender)),
        ("__substg1.0_0E04001F", _utf16(to)),
        ("__substg1.0_1000001F", _utf16(body)),
    ]

    # A minimal top-level property stream: 32 reserved bytes then one 16-byte entry per
    # variable-length property giving its tag, flags and byte length.
    properties = bytearray(b"\x00" * 32)
    for name, payload in streams:
        tag = int(name.split("_")[-1], 16)
        properties += struct.pack("<IIII", tag, 0x00000006, len(payload), 0)
    streams.append(("__properties_version1.0", bytes(properties)))

    entries = [Entry("Root Entry", STGTY_ROOT)]
    for name, payload in streams:
        entries.append(Entry(name, STGTY_STREAM, payload))

    # Every stream here is under the 4096-byte cutoff, so they all live in the mini
    # stream, which is itself an ordinary chained stream owned by the root entry.
    mini_stream = bytearray()
    mini_fat: list[int] = []
    for entry in entries[1:]:
        payload = entry.data
        used = (len(payload) + MINI_SECTOR - 1) // MINI_SECTOR or 1
        entry.start = len(mini_fat)
        entry.size = len(payload)
        mini_fat.extend(_chain(used, len(mini_fat)))
        mini_stream += payload.ljust(used * MINI_SECTOR, b"\x00")

    # Directory tree: the root's child is the first stream, the rest hang off it as a
    # right-leaning list. Readers accept an unbalanced tree.
    entries[0].child = 1
    for index in range(1, len(entries) - 1):
        entries[index].right = index + 1

    directory = bytearray()
    for entry in entries:
        name = _utf16(entry.name) + b"\x00\x00"
        block = bytearray(DIR_ENTRY_SIZE)
        block[0 : len(name)] = name
        struct.pack_into("<H", block, 64, len(name))
        block[66] = entry.kind
        block[67] = 1  # black
        struct.pack_into("<III", block, 68, entry.left, entry.right, entry.child)
        struct.pack_into("<I", block, 116, entry.start)
        struct.pack_into("<Q", block, 120, entry.size)
        directory += block
    while len(directory) % SECTOR:
        directory += b"\xff" * 8 + bytearray(DIR_ENTRY_SIZE - 8)

    mini_fat_bytes = bytearray()
    for value in mini_fat:
        mini_fat_bytes += struct.pack("<I", value)
    while len(mini_fat_bytes) % SECTOR:
        mini_fat_bytes += struct.pack("<I", FREESECT)

    mini_stream_padded = bytes(mini_stream).ljust(
        ((len(mini_stream) + SECTOR - 1) // SECTOR) * SECTOR, b"\x00"
    )

    dir_sectors = len(directory) // SECTOR
    minifat_sectors = len(mini_fat_bytes) // SECTOR
    ministream_sectors = len(mini_stream_padded) // SECTOR

    # Layout: [FAT][directory][miniFAT][mini stream]
    fat_start = 0
    dir_start = 1
    minifat_start = dir_start + dir_sectors
    ministream_start = minifat_start + minifat_sectors
    total_sectors = 1 + dir_sectors + minifat_sectors + ministream_sectors

    entries[0].start = ministream_start
    entries[0].size = len(mini_stream)
    # Rewrite the root entry now that its stream location is known.
    struct.pack_into("<I", directory, 116, entries[0].start)
    struct.pack_into("<Q", directory, 120, entries[0].size)

    fat = [FREESECT] * (SECTOR // 4)
    fat[fat_start] = FATSECT
    for index, value in enumerate(_chain(dir_sectors, dir_start)):
        fat[dir_start + index] = value
    for index, value in enumerate(_chain(minifat_sectors, minifat_start)):
        fat[minifat_start + index] = value
    for index, value in enumerate(_chain(ministream_sectors, ministream_start)):
        fat[ministream_start + index] = value
    assert total_sectors <= len(fat), "one FAT sector is enough for a fixture this small"
    fat_bytes = b"".join(struct.pack("<I", value) for value in fat)

    header = bytearray(SECTOR)
    header[0:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    struct.pack_into("<H", header, 24, 0x003E)  # minor version
    struct.pack_into("<H", header, 26, 0x0003)  # major version 3
    struct.pack_into("<H", header, 28, 0xFFFE)  # little endian
    struct.pack_into("<H", header, 30, 9)  # 512-byte sectors
    struct.pack_into("<H", header, 32, 6)  # 64-byte mini sectors
    struct.pack_into("<I", header, 44, 1)  # FAT sector count
    struct.pack_into("<I", header, 48, dir_start)
    struct.pack_into("<I", header, 56, MINI_CUTOFF)
    struct.pack_into("<I", header, 60, minifat_start)
    struct.pack_into("<I", header, 64, minifat_sectors)
    struct.pack_into("<I", header, 68, ENDOFCHAIN)  # first DIFAT sector
    struct.pack_into("<I", header, 72, 0)  # DIFAT sector count
    struct.pack_into("<I", header, 76, fat_start)  # DIFAT[0]
    for slot in range(1, 109):
        struct.pack_into("<I", header, 76 + slot * 4, FREESECT)

    return bytes(header) + fat_bytes + bytes(directory) + bytes(mini_fat_bytes) + mini_stream_padded


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "mail.msg")
    target.write_bytes(
        build_msg(
            subject="MARKER_MSG_SUBJECT",
            sender="sender@example.test",
            to="receiver@example.test",
            body="MARKER_MSG_BODY synthetic Outlook message body.",
        )
    )
    print(f"wrote {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
