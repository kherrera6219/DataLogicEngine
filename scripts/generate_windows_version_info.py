#!/usr/bin/env python3
"""Generate PyInstaller Windows version metadata from product authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def render_version_info(authority: dict) -> str:
    product = authority["product"]
    file_parts = tuple(int(part) for part in str(product["windows_file_version"]).split("."))
    if len(file_parts) != 4:
        raise ValueError("windows_file_version must contain exactly four numeric parts")
    version = str(product["version"])
    name = str(product["name"])
    return f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_parts},
    prodvers={file_parts},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Kevin Herrera'),
          StringStruct('FileDescription', 'DataLogicEngine governed backend runtime'),
          StringStruct('FileVersion', '{product['windows_file_version']}'),
          StringStruct('InternalName', 'DataLogic_Backend'),
          StringStruct('LegalCopyright', 'Copyright (c) 2026 Kevin Herrera'),
          StringStruct('OriginalFilename', 'DataLogic_Backend.exe'),
          StringStruct('ProductName', '{name}'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authority",
        type=Path,
        default=ROOT / "config" / "product-versions.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "build" / "backend-version-info.txt",
    )
    args = parser.parse_args(argv)
    authority = json.loads(args.authority.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_version_info(authority), encoding="utf-8")
    print(f"Windows version metadata: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
