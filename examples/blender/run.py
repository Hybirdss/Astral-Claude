"""Create and verify a fresh example with the installed Blender, on any supported OS."""

import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", default=shutil.which("blender"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/lamp"))
    args = parser.parse_args()
    if not args.blender:
        parser.error("Blender not on PATH; pass --blender with its executable path.")
    output = args.output.resolve()
    if output.exists():
        parser.error("Output directory already exists; choose a fresh path to preserve prior work.")
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    subprocess.run(
        [
            args.blender,
            "--background",
            "--factory-startup",
            "--threads",
            "4",
            "--python-exit-code",
            "1",
            "--python",
            str(here / "scene.py"),
            "--",
            str(output),
        ],
        check=True,
    )
    subprocess.run(
        [
            args.blender,
            "--background",
            str(output / "lamp.blend"),
            "--python-exit-code",
            "1",
            "--python",
            str(here / "verify.py"),
            "--",
            str(output),
        ],
        check=True,
    )
    print(f"Created and structurally verified: {output}")
    print(
        "Open lamp.png to evaluate appearance; the structural checks do not judge visual quality."
    )


if __name__ == "__main__":
    main()
