#!/usr/bin/env python3
"""
Prepare Crewai-maps-Scrapper project for Google Colab upload.

This script:
1. Creates a clean copy of your project
2. Removes unnecessary files (venv, __pycache__, logs, etc.)
3. Creates a ZIP file ready to upload to Colab
4. Verifies all necessary files are included
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Set


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def should_skip(path: Path, skip_patterns: Set[str]) -> bool:
    """Check if path matches skip patterns."""
    for pattern in skip_patterns:
        if pattern in path.parts:
            return True
        if path.name == pattern:
            return True
    return False


def prepare_for_colab(output_zip: str = "crewai-scraper-colab.zip") -> None:
    """Prepare project for Colab and create ZIP file."""

    project_root = get_project_root()
    temp_dir = project_root / ".colab_temp"
    output_path = project_root / output_zip

    # Clean up if temp dir exists
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    # Create temp directory
    temp_dir.mkdir(exist_ok=True)
    colab_dir = temp_dir / "scraper"
    colab_dir.mkdir(exist_ok=True)

    print("📦 Preparing your project for Colab...\n")

    # Patterns to skip
    skip_patterns = {
        "__pycache__",
        ".git",
        ".gitignore",
        "venv",
        ".venv",
        "env",
        ".eggs",
        "*.egg-info",
        ".pytest_cache",
        "node_modules",
        ".colab_temp",
        ".claude",
        ".vscode",
        "*.pyc",
    }

    # Files to copy
    files_to_copy = [
        "src",
        "requirements.txt",
        ".env",
        "README.md",
        "COLAB_GUIDE.md",
        "colab_setup.ipynb",
    ]

    # Copy files
    for item in files_to_copy:
        src = project_root / item

        if not src.exists():
            continue

        dst = colab_dir / item

        if src.is_file():
            shutil.copy2(src, dst)
            print(f"✓ Copied: {item}")
        elif src.is_dir():
            if item == "src":
                # Copy src with filtering
                shutil.copytree(
                    src,
                    dst,
                    ignore=shutil.ignore_patterns(*skip_patterns),
                    dirs_exist_ok=True
                )
            else:
                shutil.copytree(
                    src,
                    dst,
                    ignore=shutil.ignore_patterns(*skip_patterns),
                )
            print(f"✓ Copied: {item}/")

    # Verify structure
    print("\n📋 Verifying structure...")
    required_files = [
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

    missing = []
    for req_file in required_files:
        path = colab_dir / req_file
        if path.exists():
            print(f"✓ {req_file}")
        else:
            print(f"✗ {req_file}")
            missing.append(req_file)

    if missing:
        print(f"\n⚠️  Missing files: {missing}")
        print("These files are needed for the scraper to work.")
    else:
        print("\n✓ All required files present!")

    # Create ZIP file
    print(f"\n📦 Creating ZIP file: {output_zip}")

    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(colab_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if not should_skip(Path(root) / d, skip_patterns)]

            for file in files:
                file_path = Path(root) / file
                if should_skip(file_path, skip_patterns):
                    continue
                arcname = file_path.relative_to(temp_dir)
                zf.write(file_path, arcname)

    zip_size = output_path.stat().st_size / (1024 * 1024)  # MB
    print(f"✓ ZIP created: {output_zip} ({zip_size:.2f} MB)")

    # Print instructions
    print(f"\n🎉 Ready for Colab!")
    print(f"\nSteps to use in Google Colab:")
    print(f"1. Download '{output_zip}' file")
    print(f"2. Go to colab.research.google.com")
    print(f"3. Click File → Upload notebook")
    print(f"4. Select 'colab_setup.ipynb' from the ZIP")
    print(f"5. Run the notebook cells in order")
    print(f"6. When prompted, upload the entire ZIP file")
    print(f"\nOr extract the ZIP and upload files individually.")

    # Cleanup
    print(f"\n🧹 Cleaning up temporary files...")
    shutil.rmtree(temp_dir)
    print(f"✓ Done!\n")

    # Show file structure
    print(f"📂 File structure in ZIP:")
    with zipfile.ZipFile(output_path, "r") as zf:
        file_list = sorted(zf.namelist())
        for file in file_list[:20]:  # Show first 20
            indent = "  " * file.count("/")
            print(f"{indent}├ {Path(file).name}")
        if len(file_list) > 20:
            print(f"  ... and {len(file_list) - 20} more files")

    return output_path


if __name__ == "__main__":
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else "crewai-scraper-colab.zip"
    try:
        prepare_for_colab(output)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
