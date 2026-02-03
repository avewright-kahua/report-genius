"""
Legacy wrapper for DOCX token injection.

Use report_genius.injection.docx_token_injector instead.
"""

from report_genius.injection.docx_token_injector import *  # noqa: F401,F403
from report_genius.injection.docx_token_injector import main as _main


if __name__ == "__main__":
    raise SystemExit(_main())
