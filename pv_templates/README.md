# Portable View Template System

## Overview

This module enables AI-driven creation of reusable "Portable View" style report templates that work with any Kahua app. Unlike Kahua's native PV system which uses proprietary XML tokens tied to internal schema, this system:

1. **Uses API-available schema** - Relies on field definitions returned by Kahua's `/query` and `/schema` endpoints
2. **Agent-assisted creation** - Users provide examples (documents, images, descriptions) and the agent generates templates
3. **Cross-app reusability** - Templates define field mappings that adapt to different entity types

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Input Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  • Upload example document (PDF, Word, Image)                   │
│  • Describe desired layout in natural language                  │
│  • Drag-and-drop schema fields (future)                         │
│  • Canvas editor with Ctrl+K inline edits (future)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Template Analysis Agent                        │
├─────────────────────────────────────────────────────────────────┤
│  • Vision model analyzes uploaded documents/images              │
│  • Extracts layout structure (headers, tables, sections)        │
│  • Identifies data field placements                             │
│  • Maps to available schema fields from target app              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Portable Template Schema                        │
├─────────────────────────────────────────────────────────────────┤
│  {                                                               │
│    "name": "Contract Summary Report",                            │
│    "target_entity": "kahua_Contract.Contract",                   │
│    "layout": {                                                   │
│      "orientation": "portrait",                                  │
│      "margins": {...}                                            │
│    },                                                            │
│    "sections": [                                                 │
│      {                                                           │
│        "type": "header",                                         │
│        "fields": [                                               │
│          {"label": "Contract #", "path": "Number"},              │
│          {"label": "Date", "path": "Date", "format": "date"}     │
│        ]                                                         │
│      },                                                          │
│      {                                                           │
│        "type": "table",                                          │
│        "source": "Items",  // child entity path                  │
│        "columns": [...]                                          │
│      }                                                           │
│    ],                                                            │
│    "style": {                                                    │
│      "fonts": {...},                                             │
│      "colors": {...}                                             │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Template Renderer                               │
├─────────────────────────────────────────────────────────────────┤
│  • Fetches entity data via Kahua API                             │
│  • Resolves field paths to actual values                         │
│  • Generates Word document matching template layout              │
│  • Handles child entities (Items, References, etc.)              │
└─────────────────────────────────────────────────────────────────┘

```

## Token Mapping: Kahua Native vs API-Based

| Kahua Native Token | Our Approach |
|-------------------|--------------|
| `[Attribute(Number)]` | `{"path": "Number"}` - resolved via query response |
| `[Attribute(Contract.Status.Name)]` | `{"path": "Status.Name"}` - dot notation for nested |
| `[StartTable(Name=Items,Path=Items)]` | `{"type": "table", "source": "Items", "entity_def": "...ContractItem"}` |
| `[WorkBreakdown(Source=Project,...)]` | Aggregation query with cost unit calculations |
| `[StartList(Source=Attribute,...)]` | `{"type": "list", "source": "...", "path": "..."}` |

## Key Components

### 1. Template Schema (`pv_template_schema.py`)
Defines the JSON structure for portable templates with:
- Layout configuration (orientation, margins, columns)
- Section definitions (header, detail, table, chart, image)
- Field mappings with formatting options
- Style definitions (fonts, colors, spacing)

### 2. Template Analyzer (`pv_template_analyzer.py`)
Agent that:
- Accepts document uploads (uses vision model for images/PDFs)
- Extracts structural information from example documents
- Maps extracted fields to available schema from target app
- Generates template JSON

### 3. Template Renderer (`pv_template_renderer.py`)
- Takes template + entity data → Word document
- Handles all section types
- Supports conditional rendering
- Formats data according to field specs

### 4. Schema Discovery (`pv_schema_discovery.py`)
Tools for:
- Fetching available fields for any entity type
- Discovering child entities and relationships
- Caching schema for performance

## Usage Flow

### Creating a Template from Example

```python
# 1. User uploads an example document
example = await upload_document("contract_report.pdf")

# 2. Agent analyzes and creates template
template = await analyze_and_create_template(
    example=example,
    target_entity="kahua_Contract.Contract",
    user_guidance="I want a summary with contract items table"
)

# 3. User can refine via natural language
template = await refine_template(
    template=template,
    instruction="Make the header larger and add contractor company"
)

# 4. Save template for reuse
await save_template(template)
```

### Generating a Report

```python
# 1. Fetch entity data
data = await query_entity(
    entity_def="kahua_Contract.Contract",
    conditions=[{"path": "Number", "op": "eq", "value": "C-001"}]
)

# 2. Render with template
doc = await render_template(template, data)

# 3. Return Word document
return doc
```

## Future: Canvas Editor

The canvas editor will provide:

1. **Visual Template Builder**
   - Drag sections (header, table, text block) onto canvas
   - Resize and position elements
   - Preview with sample data

2. **Schema Field Palette**
   - Shows available fields from target entity
   - Drag fields into template sections
   - Auto-suggests related fields

3. **Inline Edit (Ctrl+K)**
   - Select any element
   - Describe change in natural language
   - Agent applies targeted modification

4. **Template Variants**
   - Clone and modify existing templates
   - A/B compare layouts
   - Version history

## Example Templates

See the `.docx` files in this folder for Kahua's native token-based templates.
Our system will produce similar visual output but use API-accessible data.
