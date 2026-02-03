# Report Genius

AI-powered portable view template system for Kahua construction management. Enables users to create, manage, and render professional document templates for Kahua entities with intelligent design assistance.

## Quick Start

```bash
# Install as package (recommended)
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start the backend
python server.py

# Start the frontend (separate terminal)
cd web && npm install && npm run dev
```

## Package Structure

```
report-genius/
├── src/report_genius/              # Main Python package (CANONICAL)
│   ├── __init__.py                 # Package exports
│   ├── templates/                  # Template schema and archetypes
│   │   ├── schema.py               # CANONICAL schema definitions
│   │   └── archetypes.py           # Design archetypes
│   ├── rendering/                  # DOCX generation
│   │   └── docx.py                 # SOTA renderer
│   ├── models/                     # Kahua entity models
│   │   ├── common.py               # Shared types
│   │   ├── rfi.py                  # RFI model
│   │   ├── submittal.py            # Submittal model
│   │   └── ...                     # Other entity models
│   ├── agent/                      # LangGraph agent modules
│   └── api/                        # FastAPI endpoint modules
│
├── template_gen/                   # Legacy (being migrated to src/)
├── web/                            # React frontend
├── docs/                           # Documentation
├── data/templates/                 # Template storage
│
├── server.py                       # Main API entrypoint
├── langgraph_agent.py              # Legacy wrapper (use report_genius.agent)
├── pyproject.toml                  # Package config
└── README.md
```

## Usage

### Python Package

```python
from report_genius import (
    PortableViewTemplate,
    Section,
    SectionType,
    DocxRenderer,
)
from report_genius.models import RFIModel
from report_genius.templates import create_detail_section

# Create a template
template = PortableViewTemplate(
    name="My RFI Template",
    entity_def="kahua_AEC_RFI.RFI",
    sections=[...]
)

# Render to DOCX
renderer = DocxRenderer(template)
renderer.render_to_file("output.docx")
```

## Token Injection (DOCX)

For uploaded “blank” templates, the token injector detects placeholder patterns and
inserts Kahua tokens directly into the DOCX.

Canonical module:
`report_genius.injection.docx_token_injector`

Quick CLI:
```bash
python -m report_genius.injection.docx_token_injector path/to/template.docx
```

API endpoints:
- `POST /api/template/upload-analyze`
- `POST /api/template/inject-tokens`

Fixtures for injection tests live in `tests/fixtures/docx`.

## Agent Tooling Defaults

Legacy PV/template tools are disabled by default to keep the toolset focused.
Set `RG_ENABLE_LEGACY_TOOLS=true` to include them.

Conversation summarization (for long sessions):
- `RG_SUMMARY_TRIGGER_MESSAGES` (default 24)
- `RG_SUMMARY_KEEP_MESSAGES` (default 12)

Token injection confidence threshold:
- `RG_INJECTION_CONFIDENCE_THRESHOLD` (default 0.7)

## Eval Harness

Run a lightweight eval for routing + injection:

```bash
python scripts/eval_agent.py
```

## Template Archetypes

8 pre-defined design patterns optimized for different use cases:

| Archetype | Purpose | Best For |
|-----------|---------|----------|
| `formal_document` | Official records | Contracts, Change Orders |
| `executive_summary` | High-level overviews | Status reports |
| `audit_record` | Compliance tracking | Inspections, Audits |
| `action_tracker` | Status monitoring | RFIs, Submittals |
| `financial_report` | Money matters | Invoices, Budgets |
| `correspondence` | Communication records | Letters, Memos |
| `field_report` | On-site documentation | Daily logs |
| `checklist` | Task verification | Punchlists |

## Supported Entity Types

- **ExpenseContract** - Contract management
- **RFI** - Request for Information
- **Submittal** - Submittal management
- **ExpenseChangeOrder** - Change orders
- **FieldObservation** - Field reports
- **Invoice** - Invoice processing

## API Endpoints

```
GET  /health                        # Health check
POST /chat                          # Chat with agent

GET  /api/pv-templates              # List templates
GET  /api/pv-templates/{id}         # Get template
POST /api/pv-templates/{id}/render  # Render to DOCX

GET  /api/archetypes                # List design archetypes
POST /api/compose                   # Create from archetype

GET  /reports/{filename}            # Download rendered report
```

## Kahua Placeholder Syntax

Templates use Kahua's placeholder syntax for data binding:

```
[Attribute(Number)]                                    # Simple attribute
[Currency(Source=Attribute,Path=Amount,Format="C2")]   # Currency
[Date(Source=Attribute,Path=DueDate,Format="d")]       # Date
[Boolean(IsApproved,true=Yes,false=No)]                # Boolean
[StartTable(Name=Items,Source=Attribute,Path=Items)]   # Table start
[EndTable]                                             # Table end
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint & format
ruff check . && ruff format .

# Type check
mypy src/report_genius
```

## Migration Notes (v0.2.0)

The codebase has been consolidated:

- **Import from `report_genius`** instead of legacy modules
- `pv_template_schema` → `report_genius.templates`
- `template_gen.template_schema` → `report_genius.templates`
- Entity models → `report_genius.models`

Legacy imports show deprecation warnings but continue to work.

## License

Proprietary - Kahua, Inc.
