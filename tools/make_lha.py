#!/usr/bin/env python3
"""The release LhA: everything under STAGING, as Amiga LhA writes it.

    python3 tools/make_lha.py STAGING OUT.lha EPOCH

Members are the files under STAGING in byte order of their paths, each
stamped EPOCH (seconds, UTC), so the same staging tree makes the same bytes.
Files already compressed (Ogg, PNG, JPEG, ZIP, TTF) and files over 4 MB are
stored (-lh0-); the rest are packed with -lh5- when that helps. StartGame,
which IconX or Execute starts, gets the AmigaDOS "s" bit.
tools/lha_archive.py writes the archive (level-1 headers, OS id 'A').
MIT, Copyright (c) 2026 AmiCradle Team.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lha_archive  # noqa: E402

STORE_SUFFIXES = {".ogg", ".png", ".jpg", ".jpeg", ".zip", ".ttf", ".otf", ".pak", ".wav"}
STORE_ABOVE = 4 * 1024 * 1024
SCRIPT_BIT = 0x40
SCRIPTS = {"StartGame"}


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.split("\n\n")[1])
        return 2
    staging, out, epoch = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])
    os.environ["TZ"] = "UTC"            # LhA stamps are local time: make local UTC
    time.tzset()
    paths = sorted((p for p in staging.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(staging).as_posix().encode("latin-1"))
    blob = bytearray()
    for p in paths:
        rel = p.relative_to(staging).as_posix()
        data = p.read_bytes()
        m = lha_archive.Member(rel, data, SCRIPT_BIT if p.name in SCRIPTS else 0, "", epoch)
        method = "lh0" if (p.suffix.lower() in STORE_SUFFIXES or len(data) > STORE_ABOVE) else "auto"
        blob += lha_archive.pack([m], method)[:-1]     # pack() ends each archive with a 0: one at the end
    blob.append(0)
    out.write_bytes(bytes(blob))
    digest = hashlib.sha256(blob).hexdigest()
    Path(str(out) + ".sha256").write_text(f"{digest}  {out.name}\n")
    print(f"{out.name}: {len(blob)} bytes, {len(paths)} files, sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
