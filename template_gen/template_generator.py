"""
Template Generator - Creates portable view templates from entity schemas.

This module provides intelligent template generation by analyzing entity
schemas and creating well-structured templates with sensible defaults.
Users can then refine via natural language instructions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from schema_introspector import (
    EntitySchema,
    FieldCategory,
    FieldInfo,
    get_available_schemas,
    get_schema_summary,
    introspect_model,
)
from template_schema import (
    Alignment,
    Condition,
    ConditionOperator,
    DetailConfig,
    FieldDef,
    FieldFormat,
    FormatOptions,
    HeaderConfig,
    LayoutConfig,
    PortableViewTemplate,
    Section,
    SectionType,
    StyleConfig,
    TableColumn,
    TableConfig,
    TextConfig,
    create_detail_section,
    create_divider_section,
    create_header_section,
    create_table_section,
    create_text_section,
)


def _resolve_display_path(field: FieldInfo) -> str:
    """Get the best display path for a field.
    
    For nested objects (contacts, companies), append .ShortLabel.
    For simple fields, return the path as-is.
    """
    if field.category in (FieldCategory.CONTACT, FieldCategory.NESTED):
        # Check if child has ShortLabel
        if field.child_fields:
            for child in field.child_fields:
                if child.name.lower() == "short_label":
                    return f"{field.path}.ShortLabel"
        # Default for contacts/nested: assume ShortLabel exists
        return f"{field.path}.ShortLabel"
    return field.path


def _field_to_def(field: FieldInfo, resolve_nested: bool = True) -> FieldDef:
    """Convert FieldInfo to FieldDef for templates.
    
    Args:
        field: Field metadata
        resolve_nested: If True, resolve nested objects to their display path
    """
    format_type = FieldFormat.TEXT
    format_options = None
    
    # Determine the path - resolve nested objects if requested
    path = _resolve_display_path(field) if resolve_nested else field.path
    
    if field.format_hint == "currency":
        format_type = FieldFormat.CURRENCY
        format_options = FormatOptions(decimals=2)
    elif field.format_hint == "date":
        format_type = FieldFormat.DATE
    elif field.format_hint == "datetime":
        format_type = FieldFormat.DATETIME
    elif field.format_hint == "decimal":
        format_type = FieldFormat.DECIMAL
        format_options = FormatOptions(decimals=2)
    elif field.category == FieldCategory.BOOLEAN:
        format_type = FieldFormat.BOOLEAN
    elif field.category == FieldCategory.NUMERIC:
        format_type = FieldFormat.NUMBER
    
    return FieldDef(
        path=path,
        label=field.label,
        format=format_type,
        format_options=format_options,
    )


def _select_header_fields(schema: EntitySchema) -> tuple[str, Optional[str], List[FieldInfo]]:
    """Select fields for header section.
    
    Returns:
        Tuple of (title_template, subtitle_template, additional_fields)
    """
    identity = schema.identity_fields()
    
    # Find best title field
    title_field = None
    subtitle_field = None
    
    # Priority: number > name > subject > title > id
    priority = ["number", "name", "subject", "title", "id"]
    for p in priority:
        matches = [f for f in identity if p in f.name.lower()]
        if matches:
            title_field = matches[0]
            break
    
    if not title_field and identity:
        title_field = identity[0]
    
    # Look for description or subject as subtitle
    text_blocks = schema.text_blocks()
    desc_fields = [f for f in text_blocks if "description" in f.name.lower()]
    if desc_fields:
        subtitle_field = desc_fields[0]
    elif len(identity) > 1:
        # Use second identity field as subtitle
        remaining = [f for f in identity if f != title_field]
        if remaining:
            subtitle_field = remaining[0]
    
    title_template = f"{{{title_field.path}}}" if title_field else "{Number}"
    subtitle_template = f"{{{subtitle_field.path}}}" if subtitle_field else None
    
    return title_template, subtitle_template, []


def _select_summary_fields(schema: EntitySchema, max_fields: int = 6) -> List[FieldInfo]:
    """Select key fields for the summary section."""
    candidates: List[FieldInfo] = []
    
    # Priority: status > type/category > key contacts > key dates
    status = schema.by_category(FieldCategory.STATUS)
    if status:
        candidates.extend(status[:2])
    
    lookups = schema.by_category(FieldCategory.LOOKUP)
    type_fields = [f for f in lookups if "type" in f.name.lower() or "category" in f.name.lower()]
    candidates.extend(type_fields[:1])
    
    contacts = schema.contact_fields()
    # Prioritize assigned_to, author, contractor
    priority_contacts = []
    for pattern in ["assigned", "author", "contractor", "client"]:
        matches = [f for f in contacts if pattern in f.name.lower()]
        priority_contacts.extend(matches[:1])
    candidates.extend(priority_contacts[:2])
    
    dates = schema.date_fields()
    # Prioritize date, due_date, schedule_start
    priority_dates = []
    for pattern in ["^date$", "due", "schedule_start", "schedule_end"]:
        import re
        matches = [f for f in dates if re.search(pattern, f.name.lower())]
        priority_dates.extend(matches[:1])
    candidates.extend(priority_dates[:2])
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in candidates:
        if f.path not in seen:
            seen.add(f.path)
            unique.append(f)
    
    return unique[:max_fields]


def _select_financial_fields(schema: EntitySchema, min_fields: int = 2) -> List[FieldInfo]:
    """Select financial fields for dedicated section.
    
    Args:
        schema: Entity schema
        min_fields: Minimum number of financial fields required to warrant a section
    """
    financials = schema.financial_fields()
    
    # Don't create a financial section for just 1-2 fields
    if len(financials) < min_fields:
        return []
    
    # Prioritize "total" fields
    totals = [f for f in financials if "total" in f.name.lower()]
    others = [f for f in financials if f not in totals]
    
    # Return totals first, then others, limited to reasonable count
    result = totals[:4] + others[:4]
    return result[:6]


def _select_text_blocks(schema: EntitySchema) -> List[FieldInfo]:
    """Select text block fields that warrant their own sections."""
    blocks = schema.text_blocks()
    
    # Prioritize: scope > description > notes > question > response
    priority = ["scope", "description", "notes", "question", "response", "answer"]
    
    ordered = []
    for p in priority:
        matches = [f for f in blocks if p in f.name.lower() and f not in ordered]
        ordered.extend(matches)
    
    # Add any remaining
    for f in blocks:
        if f not in ordered:
            ordered.append(f)
    
    return ordered[:5]  # Limit to 5 text blocks


# Fields to exclude from tables (internal metadata, not useful for reports)
_TABLE_EXCLUDE_FIELDS = {
    # Internal IDs and keys
    "partition_id", "group_partition_id", "domain_key", "personal_domain_key",
    "community_contact_key", "local_contact_key", "id", "key", "guid",
    # Contact internal fields (not useful in tables)
    "middle_name", "prefix", "suffix", "fax", "direct",
    "contact_full_name_label", "company_contact_label", "contact_company_label",
    "long_label",  # short_label is better for tables
    # Other internal fields
    "type_", "group_name",
}


def _has_useful_child_fields(field: FieldInfo) -> bool:
    """Check if a collection has child fields worth displaying."""
    if not field.child_fields:
        return False
    
    useful = [f for f in field.child_fields 
              if f.name.lower() not in _TABLE_EXCLUDE_FIELDS
              and f.category not in (FieldCategory.REFERENCE, FieldCategory.NESTED)]
    return len(useful) >= 2


def _select_table_collections(schema: EntitySchema) -> List[FieldInfo]:
    """Select collections suitable for table display."""
    collections = schema.collections()
    
    # Filter out references, comments, and collections without useful fields
    tables = []
    for coll in collections:
        if "reference" in coll.name.lower():
            continue
        if "comment" in coll.name.lower():
            continue
        if "notification" in coll.name.lower():
            continue  # Internal workflow data
        if "distribution" in coll.name.lower():
            continue  # Internal workflow data
        if _has_useful_child_fields(coll):
            tables.append(coll)
    
    return tables[:3]  # Limit to 3 tables


def _build_table_columns(field: FieldInfo, max_columns: int = 5) -> List[TableColumn]:
    """Build table columns from collection field's child fields."""
    if not field.child_fields:
        return []
    
    columns = []
    
    # Filter out excluded fields first
    available_fields = [
        f for f in field.child_fields
        if f.name.lower() not in _TABLE_EXCLUDE_FIELDS
        and f.category not in (FieldCategory.COLLECTION, FieldCategory.NESTED, FieldCategory.REFERENCE)
    ]
    
    # Prioritize: short_label/name > email > number > description > status > amounts > dates
    priority_patterns = [
        (["short_label", "name", "label"], 25, Alignment.LEFT),
        (["email", "email_address"], 25, Alignment.LEFT),
        (["number", "code"], 15, Alignment.LEFT),
        (["description", "subject", "title"], 35, Alignment.LEFT),
        (["status", "response"], 15, Alignment.CENTER),
        (["company", "office"], 20, Alignment.LEFT),
        (["amount", "value", "total", "cost"], 15, Alignment.RIGHT),
        (["date"], 15, Alignment.CENTER),
    ]
    
    selected: List[FieldInfo] = []
    
    for patterns, _, _ in priority_patterns:
        for pattern in patterns:
            matches = [
                f for f in available_fields
                if pattern in f.name.lower() and f not in selected
            ]
            if matches:
                selected.append(matches[0])
                break
    
    # Fill remaining slots with any available fields
    for f in available_fields:
        if len(selected) >= max_columns:
            break
        if f not in selected:
            selected.append(f)
    
    # Build columns
    for child in selected[:max_columns]:
        # Determine width based on type
        width = 20
        alignment = Alignment.LEFT
        
        if child.category == FieldCategory.FINANCIAL:
            alignment = Alignment.RIGHT
            width = 15
        elif child.category == FieldCategory.DATE:
            alignment = Alignment.CENTER
            width = 15
        elif child.category == FieldCategory.STATUS:
            alignment = Alignment.CENTER
            width = 12
        elif "description" in child.name.lower() or "name" in child.name.lower():
            width = 30
        elif "email" in child.name.lower():
            width = 25
        elif "short_label" in child.name.lower() or "label" in child.name.lower():
            width = 25
        
        columns.append(
            TableColumn(
                field=_field_to_def(child, resolve_nested=False),
                width=width,
                alignment=alignment,
            )
        )
    
    return columns


def generate_template(
    schema: EntitySchema,
    name: Optional[str] = None,
    description: Optional[str] = None,
    include_financials: bool = True,
    include_text_blocks: bool = True,
    include_tables: bool = True,
    style: Optional[StyleConfig] = None,
) -> PortableViewTemplate:
    """Generate a complete template from an entity schema.
    
    This creates an intelligent default template that users can refine.
    
    Args:
        schema: The entity schema to generate from
        name: Template name (auto-generated if not provided)
        description: Template description
        include_financials: Whether to include financial section
        include_text_blocks: Whether to include text block sections
        include_tables: Whether to include table sections for collections
        style: Custom style configuration
    
    Returns:
        A complete PortableViewTemplate
    """
    sections: List[Section] = []
    order = 0
    
    # 1. Header section
    title_tpl, subtitle_tpl, header_fields = _select_header_fields(schema)
    sections.append(Section(
        type=SectionType.HEADER,
        order=order,
        header_config=HeaderConfig(
            title_template=title_tpl,
            subtitle_template=subtitle_tpl,
            show_logo=True,  # Include company logo by default
            fields=[_field_to_def(f) for f in header_fields],
        ),
    ))
    order += 1
    
    # 2. Summary section (key metadata)
    summary_fields = _select_summary_fields(schema)
    if summary_fields:
        sections.append(Section(
            type=SectionType.DETAIL,
            title=None,  # No title for primary summary
            order=order,
            detail_config=DetailConfig(
                fields=[_field_to_def(f) for f in summary_fields],
                columns=2,
                show_labels=True,
            ),
        ))
        order += 1
    
    # 3. Divider
    sections.append(Section(
        type=SectionType.DIVIDER,
        order=order,
    ))
    order += 1
    
    # 4. Financials section (if applicable)
    if include_financials:
        financial_fields = _select_financial_fields(schema)
        if financial_fields:
            sections.append(Section(
                type=SectionType.DETAIL,
                title="Financials",
                order=order,
                detail_config=DetailConfig(
                    fields=[_field_to_def(f) for f in financial_fields],
                    columns=2,
                    show_labels=True,
                ),
            ))
            order += 1
    
    # 5. Text block sections
    if include_text_blocks:
        text_blocks = _select_text_blocks(schema)
        for block in text_blocks:
            sections.append(Section(
                type=SectionType.TEXT,
                title=block.label,
                order=order,
                condition=Condition(
                    field=block.path,
                    op=ConditionOperator.NOT_EMPTY,
                ),
                text_config=TextConfig(
                    content=f"{{{block.path}}}",
                ),
            ))
            order += 1
    
    # 6. Table sections for collections
    if include_tables:
        tables = _select_table_collections(schema)
        for table_field in tables:
            columns = _build_table_columns(table_field)
            if columns:
                # Find financial columns for subtotals
                subtotal_fields = [
                    col.field.path
                    for col in columns
                    if col.field.format == FieldFormat.CURRENCY
                ]
                
                sections.append(Section(
                    type=SectionType.TABLE,
                    title=table_field.label,
                    order=order,
                    condition=Condition(
                        field=table_field.path,
                        op=ConditionOperator.NOT_EMPTY,
                    ),
                    table_config=TableConfig(
                        source=table_field.path,
                        columns=columns,
                        show_header=True,
                        show_subtotals=bool(subtotal_fields),
                        subtotal_fields=subtotal_fields,
                    ),
                ))
                order += 1
    
    # Footer is intentionally omitted - key fields like assigned_to
    # are already included in the summary section above
    
    # Build template
    template = PortableViewTemplate(
        name=name or f"{schema.name} Report",
        description=description or f"Auto-generated portable view for {schema.name}",
        entity_def=schema.entity_def,
        layout=LayoutConfig(),
        style=style or StyleConfig(),
        sections=sections,
        source_type="generated",
    )
    
    return template


def generate_minimal_template(
    schema: EntitySchema,
    fields: Optional[List[str]] = None,
) -> PortableViewTemplate:
    """Generate a minimal template with only specified fields.
    
    Args:
        schema: The entity schema
        fields: List of field paths to include (uses identity if not provided)
    
    Returns:
        A minimal template
    """
    sections = []
    
    # Header
    title_tpl, subtitle_tpl, _ = _select_header_fields(schema)
    sections.append(Section(
        type=SectionType.HEADER,
        order=0,
        header_config=HeaderConfig(
            title_template=title_tpl,
            subtitle_template=subtitle_tpl,
        ),
    ))
    
    # If specific fields requested, add them
    if fields:
        field_defs = []
        for path in fields:
            # Find field in schema
            matching = [f for f in schema.fields if f.path == path]
            if matching:
                field_defs.append(_field_to_def(matching[0]))
            else:
                # Create generic field def
                field_defs.append(FieldDef(path=path))
        
        if field_defs:
            sections.append(Section(
                type=SectionType.DETAIL,
                order=1,
                detail_config=DetailConfig(
                    fields=field_defs,
                    columns=2,
                ),
            ))
    
    return PortableViewTemplate(
        name=f"{schema.name} Summary",
        entity_def=schema.entity_def,
        sections=sections,
        source_type="generated",
    )


# ============================================================================
# CLI / Demo
# ============================================================================

if __name__ == "__main__":
    import json
    from pathlib import Path
    
    schemas = get_available_schemas()
    
    for name, schema in schemas.items():
        print(f"\n{'='*60}")
        print(f"Generating template for: {schema.name}")
        print(f"{'='*60}")
        
        template = generate_template(schema)
        
        # Save to file
        output_path = Path("pv_templates/saved") / f"generated-{name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(template.model_dump(), f, indent=2, default=str)
        
        print(f"Saved: {output_path}")
        print(f"Sections: {len(template.sections)}")
        for section in template.get_sections_ordered():
            print(f"  - {section.type.value}: {section.title or '(untitled)'}")
