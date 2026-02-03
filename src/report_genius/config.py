"""
Configuration for report-genius package.

Centralizes path configuration and settings.
"""
from pathlib import Path

# Base paths
PACKAGE_DIR = Path(__file__).parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent

# Template storage
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = DATA_DIR / "templates" / "saved"
SAMPLE_TEMPLATES_DIR = DATA_DIR / "sample_templates"

# Output directories
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUT_DIR = PROJECT_ROOT / "output_json"

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    return TEMPLATES_DIR


def get_template_path(template_id: str) -> Path:
    """Get path for a specific template."""
    return TEMPLATES_DIR / f"{template_id}.json"


__all__ = [
    "PROJECT_ROOT",
    "DATA_DIR", 
    "TEMPLATES_DIR",
    "SAMPLE_TEMPLATES_DIR",
    "REPORTS_DIR",
    "OUTPUT_DIR",
    "get_templates_dir",
    "get_template_path",
]
