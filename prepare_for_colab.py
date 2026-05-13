#!/usr/bin/env python3
"""
Prepare Crewai-maps-Scrapper project for Google Colab upload.

Run this script to create a clean ZIP file ready to upload to Colab:
    python prepare_for_colab.py

Output: crewai-scraper-colab.zip
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

SKIP_DIRS = {
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "env",
    ".eggs",
    ".pytest_cache",
    "node_modules",
    ".colab_temp",
    ".claude",
    ".vscode",
    ".idea",
}

SKIP_EXTENSIONS = {".pyc", ".pyo", ".log", ".err"}

SKIP_FILES = {".gitignore", ".DS_Store", "Thumbs.db", "prepare_for_colab.py"}

FILES_TO_INCLUDE = [
    "src",
    "requirements.txt",
    "README.md",
    "COLAB_GUIDE.md",
    "colab_setup.ipynb",
]


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIRS or name.endswith(".egg-info")


def should_skip_file(path: Path) -> bool:
    return path.name in SKIP_FILES or path.suffix in SKIP_EXTENSIONS


def copy_filtered(src: Path, dst: Path) -> None:
    """Recursively copy a directory, skipping unwanted files."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            if not should_skip_dir(item.name):
                copy_filtered(item, dst / item.name)
        elif item.is_file():
            if not should_skip_file(item):
                shutil.copy2(item, dst / item.name)


def prepare_for_colab(output_zip: str = "crewai-scraper-colab.zip") -> None:
    project_root = Path(__file__).parent
    temp_dir = project_root / ".colab_temp"
    output_path = project_root / output_zip

    # Clean up temp dir from any previous run
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    print("Preparing project for Colab...\n")

    # Copy selected files/folders into temp_dir (flat — no extra 'scraper/' wrapper)
    for item in FILES_TO_INCLUDE:
        src = project_root / item
        if not src.exists():
            print(f"  SKIP (not found): {item}")
            continue

        dst = temp_dir / item
        if src.is_file():
            shutil.copy2(src, dst)
            print(f"  OK  {item}")
        elif src.is_dir():
            copy_filtered(src, dst)
            print(f"  OK  {item}/")

    # Verify required files are present
    required = [
        "src/__init__.py",
        "src/main.py",
        "src/config.py",
        "src/tools/__init__.py",
        "src/tools/location_api.py",
        "src/tools/playwright_bot.py",
        "src/orchestration/__init__.py",
        "src/orchestration/pipeline.py",
        "requirements.txt",
    ]

    print("\nVerifying structure...")
    missing = []
    for f in required:
        p = temp_dir / f
        if p.exists():
            print(f"  FOUND  {f}")
        else:
            print(f"  MISSING {f}")
            missing.append(f)

    if missing:
        print(f"\nWARNING: {len(missing)} file(s) missing from output.")
    else:
        print("\nAll required files present.")

    # Create ZIP — files sit at root level (src/, requirements.txt, etc.)
    if output_path.exists():
        output_path.unlink()

    print(f"\nCreating {output_zip}...")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            root_path = Path(root)

            # Prune unwanted dirs in-place
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]

            for filename in files:
                file_path = root_path / filename
                if should_skip_file(file_path):
                    continue
                # arcname is relative to temp_dir so ZIP contains src/main.py etc.
                arcname = file_path.relative_to(temp_dir)
                zf.write(file_path, arcname)

    zip_size_kb = output_path.stat().st_size / 1024
    print(f"Done! {output_zip} ({zip_size_kb:.1f} KB)\n")

    # Show contents
    print("Contents of ZIP:")
    with zipfile.ZipFile(output_path, "r") as zf:
        for name in sorted(zf.namelist()):
            print(f"  {name}")

    # Cleanup temp dir
    shutil.rmtree(temp_dir)

    print(f"\nShare these two files with anyone who wants to run the scraper:")
    print(f"  1. {output_zip}")
    print(f"  2. colab_setup.ipynb")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "crewai-scraper-colab.zip"
    try:
        prepare_for_colab(out)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
