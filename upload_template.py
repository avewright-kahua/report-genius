#!/usr/bin/env python
"""
Quick script to upload a DOCX template for processing.

Usage:
    python upload_template.py path/to/template.docx [entity_type]

Examples:
    python upload_template.py my_rfi.docx RFI
    python upload_template.py invoice_form.docx Invoice
    python upload_template.py template.docx  # Auto-detect entity
"""

import sys
import shutil
from pathlib import Path

UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


def upload_template(file_path: str, entity_type: str = None):
    """Copy a DOCX file to the uploads directory."""
    src = Path(file_path)
    
    if not src.exists():
        print(f"Error: File not found: {file_path}")
        return None
    
    if not src.suffix.lower() in ('.docx', '.doc'):
        print(f"Error: Not a Word document: {file_path}")
        return None
    
    # Copy to uploads
    dest = UPLOADS_DIR / src.name
    shutil.copy2(src, dest)
    
    print(f"✓ Uploaded: {src.name}")
    print(f"  Location: {dest}")
    print()
    
    # Generate the command to tell the agent
    entity_hint = entity_type or "RFI"
    print("Now tell the agent:")
    print(f'  "Process {src.name} as a {entity_hint} template"')
    print()
    print("Or for full analysis:")
    print(f'  "Analyze and complete {src.name} for {entity_hint}"')
    
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    file_path = sys.argv[1]
    entity_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    upload_template(file_path, entity_type)
