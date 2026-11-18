#!/usr/bin/env python3
"""Cross-platform Blender executable locator."""

from __future__ import annotations

import json
import os
import platform
import shutil
from pathlib import Path


def find_blender() -> tuple[str | None, str]:
    env_bin = os.environ.get("BLENDER_BIN")
    if env_bin and Path(env_bin).exists():
        return str(Path(env_bin)), "env:BLENDER_BIN"

    on_path = shutil.which("blender")
    if on_path:
        return on_path, "PATH"

    system = platform.system()
    candidates: list[Path] = []
    if system == "Windows":
        base = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation"
        if base.exists():
            candidates.extend(sorted(base.glob("Blender */blender.exe"), reverse=True))
    elif system == "Darwin":
        candidates.append(Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    else:
        candidates.extend([Path("/usr/bin/blender"), Path("/usr/local/bin/blender")])

    for c in candidates:
        if c.exists():
            return str(c), "default_install_dir"

    return None, "not_found"


def main() -> int:
    path, source = find_blender()
    print(json.dumps({"found": path is not None, "path": path, "source": source}, indent=2))
    return 0 if path else 1


if __name__ == "__main__":
    raise SystemExit(main())
