# Report Genius

AI-powered portable view template system for Kahua construction management. Enables users to create, manage, and render professional document templates for Kahua entities with intelligent design assistance.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start the backend
python server.py

# Start the frontend (separate terminal)
cd web
npm install
npm run dev
```

## Project Structure

```
report-genius/
├── src/report_genius/          # New Python package (in development)
│   ├── templates/              # Template schema and archetypes
│   ├── rendering/              # DOCX generation
│   ├── agent/                  # LangGraph agent modules
│   ├── api/                    # FastAPI endpoint modules
│   └── models/                 # Kahua entity definitions
├── template_gen/               # Template generation system
│   ├── core/                   # Design system and composer
│   ├── models/                 # Entity schema definitions
│   └── api/                    # Alternative API server
├── web/                        # React frontend
├── docs/                       # Documentation
├── data/pv_templates/          # Template storage
│
│ # Root-level application files
├── server.py                   # Main API entrypoint
├── langgraph_agent.py          # LangGraph agent implementation
├── unified_templates.py        # Template system bridge
├── template_builder_api.py     # Template builder API routes
├── pv_template_*.py            # Portable view template modules
├── pyproject.toml              # Python package config
└── README.md
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
GET  /api/archetypes              # List available archetypes
GET  /api/entities                # List supported entity types
POST /api/compose                 # Create template from archetype
GET  /api/render-docx/{id}        # Render template to DOCX
POST /api/agent/session           # Create agent session
POST /api/agent/{id}/execute      # Execute agent tool
```

## Kahua Placeholder Syntax

Templates use Kahua's placeholder syntax for data binding:

```
[Attribute(Number)]                        # Simple attribute
[Currency(Amount)]                         # Currency formatting
[Date(CreatedOn,format=MM/dd/yyyy)]        # Date formatting
[Boolean(IsApproved,true=Yes,false=No)]    # Boolean
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
```

## Documentation

See [docs/](docs/) for detailed documentation on Kahua portable view templates.

## License

Proprietary - Kahua, Inc.
