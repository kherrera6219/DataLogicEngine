"""Build and check the SDK wheel without importing the application checkout.

Run with the SDK's declared build backend and runtime dependencies installed.
The check uses no package index and installs the built wheel into a temporary
directory without resolving dependencies.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PIP_NO_INDEX"] = "1"
    with TemporaryDirectory(prefix="dle-sdk-wheel-") as temporary:
        root = Path(temporary)
        wheels = root / "wheels"
        target = root / "installed"
        wheels.mkdir()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheels),
                str(project),
            ],
            cwd=root,
            env=environment,
            check=True,
        )
        candidates = list(wheels.glob("ukg_sdk-*.whl"))
        if len(candidates) != 1:
            raise RuntimeError("Expected exactly one built ukg_sdk wheel")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(target),
                str(candidates[0]),
            ],
            cwd=root,
            env=environment,
            check=True,
        )
        code = (
            "import pathlib, sys; "
            "root = pathlib.Path(sys.argv[1]).resolve(); "
            "sys.path.insert(0, str(root)); "
            "import ukg_sdk; from ukg_sdk.egress import sync_client; "
            "assert pathlib.Path(ukg_sdk.__file__).resolve().is_relative_to(root); "
            "assert 'core.security.egress_guard' not in sys.modules; "
            "print('Standalone SDK wheel import verified')"
        )
        subprocess.run(
            [sys.executable, "-I", "-c", code, str(target)],
            cwd=root,
            env=environment,
            check=True,
        )


if __name__ == "__main__":
    main()
