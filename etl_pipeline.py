"""
ETL Pipeline module that wraps the standalone ETL scripts.

The scripts in ``etl/`` are not a Python package, so we execute them
directly from their file paths instead of importing them as modules.
"""

from pathlib import Path
import runpy
import os


ROOT_DIR = Path(__file__).resolve().parent
ETL_DIR = ROOT_DIR / "etl"


def _run_script(script_name: str):
    """Execute one ETL script in its own __main__ namespace."""
    script_path = ETL_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"ETL script not found: {script_path}")
    previous_cwd = os.getcwd()
    try:
        os.chdir(ROOT_DIR)
        return runpy.run_path(str(script_path), run_name="__main__")
    finally:
        os.chdir(previous_cwd)


def run_extraction():
    """Run the extraction phase of ETL."""
    return _run_script("01_extract_from_excel.py")


def run_transformation():
    """Run the transformation phase of ETL."""
    return _run_script("02_clean_and_transform.py")


def run_load():
    """Run the load phase of ETL."""
    return _run_script("03_load_to_warehouse.py")


def run_full_pipeline():
    """Run the complete ETL pipeline sequentially."""
    print("Starting ETL pipeline...")

    print("\n[1/3] Running extraction...")
    run_extraction()

    print("\n[2/3] Running transformation...")
    run_transformation()

    print("\n[3/3] Running load...")
    run_load()

    print("\nETL pipeline completed successfully!")
