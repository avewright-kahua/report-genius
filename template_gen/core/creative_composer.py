"""
Creative Template Composer - Generates visually sophisticated template structures.

This module goes beyond basic field placement to create templates that follow
professional document design principles with thoughtful information architecture.

Design Philosophy:
- Every section should have a clear purpose
- Visual hierarchy guides the reader's eye
- Related information is grouped logically
- White space is used intentionally
- Conditionals ensure clean output with no empty sections
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

# Import from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema_introspector import EntitySchema, FieldCategory, FieldInfo, get_schema_summary
from template_schema import (
    Alignment,
    Condition,
    ConditionOperator,
    DetailConfig,
    DividerConfig,
    FieldDef,
    FieldFormat,
    FormatOptions,
    HeaderConfig,
    LayoutConfig,
    LayoutType,
    PortableViewTemplate,
    Section,
    SectionType,
    SpacerConfig,
    StyleConfig,
    TableColumn,
    TableConfig,
    TextConfig,
)

from .design_system import (
    DesignGuidelines,
    DesignSystem,
    InformationDensity,
    TemplateArchetype,
    VisualTone,
)


class SectionPurpose(str, Enum):
    """Semantic purpose of a section - drives design decisions."""
    
    IDENTITY = "identity"           # Who/what is this document
    ROUTING = "routing"             # Who sent it, who receives it
    STATUS_BANNER = "status_banner" # Current state at a glance
    KEY_METRICS = "key_metrics"     # Important numbers
    PARTIES = "parties"             # Companies/contacts involved
    SCHEDULE = "schedule"           # Dates and timeline
    FINANCIALS = "financials"       # Money-related fields
    NARRATIVE = "narrative"         # Long-form content
    LINE_ITEMS = "line_items"       # Tabular breakdown
    ATTACHMENTS = "attachments"     # Related documents
    SIGNATURES = "signatures"       # Approval/sign-off area
    METADATA = "metadata"           # Additional details


@dataclass
class ComposedSection:
    """A section with design intent."""
    
    purpose: SectionPurpose
    section: Section
    design_notes: str
    priority: int  # Lower = higher priority (appears first)


class CreativeComposer:
    """Composes templates with design intelligence."""
    
    def __init__(self, design_system: Optional[DesignSystem] = None):
        self.design_system = design_system or DesignSystem()
    
    def compose(
        self,
        schema: EntitySchema,
        archetype: TemplateArchetype,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> PortableViewTemplate:
        """Compose a creative, well-designed template.
        
        Args:
            schema: Entity schema to build from
            archetype: Template archetype guiding structure
            user_preferences: Optional customization hints
        
        Returns:
            A professionally designed template
        """
        preferences = user_preferences or {}
        guidelines = self.design_system.get_guidelines(archetype)
        
        # Analyze the schema
        analysis = self._analyze_schema(schema)
        
        # Compose sections based on archetype
        if archetype == TemplateArchetype.EXECUTIVE_SUMMARY:
            sections = self._compose_executive_summary(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.FINANCIAL_REPORT:
            sections = self._compose_financial_report(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.CORRESPONDENCE:
            sections = self._compose_correspondence(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.AUDIT_RECORD:
            sections = self._compose_audit_record(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.ACTION_TRACKER:
            sections = self._compose_action_tracker(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.FIELD_REPORT:
            sections = self._compose_field_report(schema, analysis, guidelines, preferences)
        elif archetype == TemplateArchetype.CHECKLIST:
            sections = self._compose_checklist(schema, analysis, guidelines, preferences)
        else:
            sections = self._compose_formal_document(schema, analysis, guidelines, preferences)
        
        # Sort by priority and assign order
        sections.sort(key=lambda s: s.priority)
        for i, cs in enumerate(sections):
            cs.section.order = i
        
        # Build the template
        template_name = preferences.get("name") or self._generate_template_name(schema, archetype)
        
        return PortableViewTemplate(
            name=template_name,
            description=f"{archetype.value.replace('_', ' ').title()} for {schema.name}",
            entity_def=schema.entity_def,
            layout=self._create_layout(guidelines),
            style=self._create_style(guidelines, preferences),
            sections=[cs.section for cs in sections],
            source_type="generated",
            tags=[archetype.value, schema.name.lower()],
        )
    
    def _analyze_schema(self, schema: EntitySchema) -> Dict[str, Any]:
        """Analyze schema for intelligent field selection."""
        summary = get_schema_summary(schema)
        
        # Categorize fields for quick access
        fields_by_cat = summary["fields_by_category"]
        
        # Find specific field patterns
        analysis = {
            "identity": self._find_identity_fields(schema),
            "title_field": self._find_best_title_field(schema),
            "subtitle_field": self._find_subtitle_field(schema),
            "status_field": self._find_status_field(schema),
            "key_contacts": self._find_key_contacts(schema),
            "key_dates": self._find_key_dates(schema),
            "totals": self._find_total_fields(schema),
            "line_items": self._find_line_item_collections(schema),
            "text_blocks": self._find_text_blocks(schema),
            "field_counts": summary["field_counts"],
            "all_fields": schema.fields,
        }
        
        return analysis
    
    # ========== Archetype Composers ==========
    
    def _compose_executive_summary(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Executive summary: Quick overview with KPIs."""
        sections = []
        priority = 0
        
        # Minimal header - just the identifier
        sections.append(self._create_identity_header(
            analysis, priority, compact=True
        ))
        priority += 1
        
        # Status banner - the one thing you need to know
        if analysis["status_field"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.STATUS_BANNER,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(analysis["status_field"])],
                        columns=1,
                        layout=LayoutType.HORIZONTAL,
                        show_labels=True,
                    ),
                ),
                design_notes="Prominent status indicator",
                priority=priority,
            ))
            priority += 1
        
        # Key metrics row - totals and key numbers
        if analysis["totals"]:
            metric_fields = analysis["totals"][:4]  # Max 4 KPIs
            sections.append(ComposedSection(
                purpose=SectionPurpose.KEY_METRICS,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in metric_fields],
                        columns=len(metric_fields),
                        layout=LayoutType.HORIZONTAL,
                        show_labels=True,
                    ),
                ),
                design_notes="Key financial metrics at a glance",
                priority=priority,
            ))
            priority += 1
        
        # Timeline - just key dates
        if analysis["key_dates"]:
            date_fields = analysis["key_dates"][:3]
            sections.append(ComposedSection(
                purpose=SectionPurpose.SCHEDULE,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in date_fields],
                        columns=len(date_fields),
                        layout=LayoutType.HORIZONTAL,
                        show_labels=True,
                    ),
                ),
                design_notes="Timeline overview",
                priority=priority,
            ))
        
        return sections
    
    def _compose_financial_report(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Financial report: Emphasis on numbers and line items."""
        sections = []
        priority = 0
        
        # Header with logo
        sections.append(self._create_identity_header(analysis, priority, show_logo=True))
        priority += 1
        
        # Summary totals - prominent
        if analysis["totals"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.KEY_METRICS,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Summary",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in analysis["totals"]],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Financial totals prominently displayed",
                priority=priority,
            ))
            priority += 1
        
        # Parties section
        if analysis["key_contacts"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.PARTIES,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Parties",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in analysis["key_contacts"][:4]],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Contractor, client, and key contacts",
                priority=priority,
            ))
            priority += 1
        
        # Dates
        if analysis["key_dates"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.SCHEDULE,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Schedule",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in analysis["key_dates"]],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Key dates and timeline",
                priority=priority,
            ))
            priority += 1
        
        # Line items table
        for line_items in analysis["line_items"]:
            sections.append(self._create_line_items_table(
                line_items, priority, show_subtotals=True
            ))
            priority += 1
        
        return sections
    
    def _compose_correspondence(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Correspondence: Question/Answer or Request/Response pattern."""
        sections = []
        priority = 0
        
        # Header
        sections.append(self._create_identity_header(analysis, priority, show_logo=True))
        priority += 1
        
        # Routing - From/To pattern
        routing_fields = self._find_routing_fields(schema)
        if routing_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.ROUTING,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in routing_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Who sent this and who responds",
                priority=priority,
            ))
            priority += 1
        
        # Status + Dates row
        status_date_fields = []
        if analysis["status_field"]:
            status_date_fields.append(analysis["status_field"])
        status_date_fields.extend(analysis["key_dates"][:2])
        
        if status_date_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.STATUS_BANNER,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in status_date_fields],
                        columns=len(status_date_fields),
                        layout=LayoutType.HORIZONTAL,
                        show_labels=True,
                    ),
                ),
                design_notes="Status and key dates",
                priority=priority,
            ))
            priority += 1
        
        # Divider before content
        sections.append(ComposedSection(
            purpose=SectionPurpose.METADATA,
            section=Section(type=SectionType.DIVIDER, divider_config=DividerConfig()),
            design_notes="Visual separator",
            priority=priority,
        ))
        priority += 1
        
        # Text blocks (Question, Answer, Description, etc.)
        for text_block in analysis["text_blocks"][:4]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.NARRATIVE,
                section=Section(
                    type=SectionType.TEXT,
                    title=text_block.label,
                    condition=Condition(
                        field=text_block.path,
                        op=ConditionOperator.NOT_EMPTY,
                    ),
                    text_config=TextConfig(content=f"{{{text_block.path}}}"),
                ),
                design_notes=f"Content block: {text_block.label}",
                priority=priority,
            ))
            priority += 1
        
        return sections
    
    def _compose_formal_document(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Formal document: Professional layout with all key information."""
        sections = []
        priority = 0
        
        # Header with logo
        sections.append(self._create_identity_header(analysis, priority, show_logo=True))
        priority += 1
        
        # Summary metadata
        summary_fields = []
        if analysis["status_field"]:
            summary_fields.append(analysis["status_field"])
        summary_fields.extend(analysis["key_contacts"][:2])
        summary_fields.extend(analysis["key_dates"][:2])
        
        if summary_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.METADATA,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in summary_fields[:6]],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Key metadata at a glance",
                priority=priority,
            ))
            priority += 1
        
        # Divider
        sections.append(ComposedSection(
            purpose=SectionPurpose.METADATA,
            section=Section(type=SectionType.DIVIDER, divider_config=DividerConfig()),
            design_notes="Visual separator",
            priority=priority,
        ))
        priority += 1
        
        # Financials if significant
        if analysis["totals"] and len(analysis["totals"]) >= 3:
            sections.append(ComposedSection(
                purpose=SectionPurpose.FINANCIALS,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Financials",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in analysis["totals"][:6]],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Financial details grouped",
                priority=priority,
            ))
            priority += 1
        
        # Text blocks
        for text_block in analysis["text_blocks"][:guidelines.max_text_blocks]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.NARRATIVE,
                section=Section(
                    type=SectionType.TEXT,
                    title=text_block.label,
                    condition=Condition(
                        field=text_block.path,
                        op=ConditionOperator.NOT_EMPTY,
                    ),
                    text_config=TextConfig(content=f"{{{text_block.path}}}"),
                ),
                design_notes=f"Content: {text_block.label}",
                priority=priority,
            ))
            priority += 1
        
        # Line items
        for line_items in analysis["line_items"][:2]:
            sections.append(self._create_line_items_table(
                line_items, priority, show_subtotals=guidelines.include_subtotals
            ))
            priority += 1
        
        return sections
    
    def _compose_audit_record(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Audit record: Comprehensive with all details."""
        sections = []
        priority = 0
        
        # Header
        sections.append(self._create_identity_header(analysis, priority, show_logo=True))
        priority += 1
        
        # All identity/status fields
        id_fields = [f for f in schema.fields if f.category in (
            FieldCategory.IDENTITY, FieldCategory.STATUS
        )]
        if id_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.IDENTITY,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Identification",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in id_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Complete identification",
                priority=priority,
            ))
            priority += 1
        
        # All contacts
        contact_fields = schema.contact_fields()
        if contact_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.PARTIES,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Parties & Contacts",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in contact_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="All parties involved",
                priority=priority,
            ))
            priority += 1
        
        # All dates
        date_fields = schema.date_fields()
        if date_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.SCHEDULE,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Timeline",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in date_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Complete timeline",
                priority=priority,
            ))
            priority += 1
        
        # All financials
        financial_fields = schema.financial_fields()
        if financial_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.FINANCIALS,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Financial Details",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in financial_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Complete financial record",
                priority=priority,
            ))
            priority += 1
        
        # All text blocks
        for text_block in analysis["text_blocks"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.NARRATIVE,
                section=Section(
                    type=SectionType.TEXT,
                    title=text_block.label,
                    text_config=TextConfig(content=f"{{{text_block.path}}}"),
                ),
                design_notes=f"Content: {text_block.label}",
                priority=priority,
            ))
            priority += 1
        
        # All collections
        for line_items in analysis["line_items"]:
            sections.append(self._create_line_items_table(
                line_items, priority, show_subtotals=True
            ))
            priority += 1
        
        return sections
    
    def _compose_action_tracker(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Action tracker: Focus on status, assignments, due dates."""
        sections = []
        priority = 0
        
        # Compact header
        sections.append(self._create_identity_header(analysis, priority, compact=True))
        priority += 1
        
        # Status + Assignment row
        action_fields = []
        if analysis["status_field"]:
            action_fields.append(analysis["status_field"])
        
        # Find assigned_to type fields
        for contact in analysis["key_contacts"]:
            if any(kw in contact.name.lower() for kw in ["assigned", "owner", "responsible"]):
                action_fields.append(contact)
                break
        
        # Due date
        for date_field in analysis["key_dates"]:
            if any(kw in date_field.name.lower() for kw in ["due", "required", "target"]):
                action_fields.append(date_field)
                break
        
        if action_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.STATUS_BANNER,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in action_fields],
                        columns=len(action_fields),
                        layout=LayoutType.HORIZONTAL,
                        show_labels=True,
                    ),
                ),
                design_notes="Action status at a glance",
                priority=priority,
            ))
            priority += 1
        
        # Description/scope - just one main text block
        if analysis["text_blocks"]:
            main_text = analysis["text_blocks"][0]
            sections.append(ComposedSection(
                purpose=SectionPurpose.NARRATIVE,
                section=Section(
                    type=SectionType.TEXT,
                    title=main_text.label,
                    condition=Condition(
                        field=main_text.path,
                        op=ConditionOperator.NOT_EMPTY,
                    ),
                    text_config=TextConfig(content=f"{{{main_text.path}}}"),
                ),
                design_notes="Main content",
                priority=priority,
            ))
        
        return sections
    
    def _compose_field_report(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Field report: Observations, conditions, photos."""
        sections = []
        priority = 0
        
        # Header
        sections.append(self._create_identity_header(analysis, priority, show_logo=True))
        priority += 1
        
        # Location/conditions if available
        location_fields = [
            f for f in schema.fields
            if any(kw in f.name.lower() for kw in ["location", "area", "zone", "building"])
        ]
        condition_fields = [
            f for f in schema.fields
            if any(kw in f.name.lower() for kw in ["weather", "condition", "temperature"])
        ]
        
        context_fields = location_fields[:2] + condition_fields[:2]
        if context_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.METADATA,
                section=Section(
                    type=SectionType.DETAIL,
                    title="Site Context",
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in context_fields],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Location and conditions",
                priority=priority,
            ))
            priority += 1
        
        # Status and date
        status_date = []
        if analysis["status_field"]:
            status_date.append(analysis["status_field"])
        if analysis["key_dates"]:
            status_date.append(analysis["key_dates"][0])
        
        if status_date:
            sections.append(ComposedSection(
                purpose=SectionPurpose.STATUS_BANNER,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in status_date],
                        columns=2,
                        show_labels=True,
                    ),
                ),
                design_notes="Status and date",
                priority=priority,
            ))
            priority += 1
        
        # Observations/notes
        for text_block in analysis["text_blocks"]:
            sections.append(ComposedSection(
                purpose=SectionPurpose.NARRATIVE,
                section=Section(
                    type=SectionType.TEXT,
                    title=text_block.label,
                    condition=Condition(
                        field=text_block.path,
                        op=ConditionOperator.NOT_EMPTY,
                    ),
                    text_config=TextConfig(content=f"{{{text_block.path}}}"),
                ),
                design_notes=f"Observation: {text_block.label}",
                priority=priority,
            ))
            priority += 1
        
        return sections
    
    def _compose_checklist(
        self,
        schema: EntitySchema,
        analysis: Dict[str, Any],
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> List[ComposedSection]:
        """Checklist: Item-focused with status tracking."""
        sections = []
        priority = 0
        
        # Minimal header
        sections.append(self._create_identity_header(analysis, priority, compact=True))
        priority += 1
        
        # Status + completion info
        status_fields = []
        if analysis["status_field"]:
            status_fields.append(analysis["status_field"])
        
        # Look for completion-related fields
        for f in schema.fields:
            if any(kw in f.name.lower() for kw in ["complete", "closed", "done"]):
                status_fields.append(f)
                break
        
        if status_fields:
            sections.append(ComposedSection(
                purpose=SectionPurpose.STATUS_BANNER,
                section=Section(
                    type=SectionType.DETAIL,
                    title=None,
                    detail_config=DetailConfig(
                        fields=[self._field_to_def(f) for f in status_fields[:3]],
                        columns=len(status_fields[:3]),
                        show_labels=True,
                    ),
                ),
                design_notes="Status tracking",
                priority=priority,
            ))
            priority += 1
        
        # Items table if there's a collection
        for line_items in analysis["line_items"]:
            sections.append(self._create_line_items_table(
                line_items, priority, show_subtotals=False
            ))
            priority += 1
        
        return sections
    
    # ========== Helper Methods ==========
    
    def _create_identity_header(
        self,
        analysis: Dict[str, Any],
        priority: int,
        compact: bool = False,
        show_logo: bool = False,
    ) -> ComposedSection:
        """Create the header section."""
        title_field = analysis["title_field"]
        subtitle_field = analysis["subtitle_field"]
        
        title_template = f"{{{title_field.path}}}" if title_field else "{Number}"
        subtitle_template = f"{{{subtitle_field.path}}}" if subtitle_field else None
        
        header_fields = []
        if not compact and analysis["identity"]:
            # Add secondary identity fields
            for f in analysis["identity"]:
                if f != title_field and f != subtitle_field:
                    header_fields.append(self._field_to_def(f))
                if len(header_fields) >= 2:
                    break
        
        return ComposedSection(
            purpose=SectionPurpose.IDENTITY,
            section=Section(
                type=SectionType.HEADER,
                header_config=HeaderConfig(
                    title_template=title_template,
                    subtitle_template=subtitle_template,
                    fields=header_fields,
                    show_logo=show_logo,
                    layout=LayoutType.HORIZONTAL if compact else LayoutType.GRID,
                ),
            ),
            design_notes="Document identity and branding",
            priority=priority,
        )
    
    def _create_line_items_table(
        self,
        collection_field: FieldInfo,
        priority: int,
        show_subtotals: bool = True,
    ) -> ComposedSection:
        """Create a table section for line items."""
        columns = self._build_table_columns(collection_field)
        
        # Find currency columns for subtotals
        subtotal_fields = []
        if show_subtotals:
            subtotal_fields = [
                c.field.path for c in columns
                if c.field.format == FieldFormat.CURRENCY
            ]
        
        return ComposedSection(
            purpose=SectionPurpose.LINE_ITEMS,
            section=Section(
                type=SectionType.TABLE,
                title=collection_field.label,
                condition=Condition(
                    field=collection_field.path,
                    op=ConditionOperator.NOT_EMPTY,
                ),
                table_config=TableConfig(
                    source=collection_field.path,
                    columns=columns,
                    show_header=True,
                    show_subtotals=bool(subtotal_fields),
                    subtotal_fields=subtotal_fields,
                ),
            ),
            design_notes=f"Table: {collection_field.label}",
            priority=priority,
        )
    
    def _build_table_columns(
        self,
        collection_field: FieldInfo,
        max_columns: int = 6,
    ) -> List[TableColumn]:
        """Build intelligent table columns."""
        if not collection_field.child_fields:
            return []
        
        # Exclude internal fields
        excluded = {
            "id", "key", "guid", "partition_id", "domain_key",
            "long_label", "middle_name", "prefix", "suffix",
        }
        
        available = [
            f for f in collection_field.child_fields
            if f.name.lower() not in excluded
            and f.category not in (FieldCategory.COLLECTION, FieldCategory.NESTED, FieldCategory.REFERENCE)
        ]
        
        # Priority selection
        selected = []
        
        # 1. Identifier/name
        for f in available:
            if any(kw in f.name.lower() for kw in ["number", "name", "short_label", "code"]):
                selected.append(f)
                break
        
        # 2. Description
        for f in available:
            if any(kw in f.name.lower() for kw in ["description", "subject", "title"]) and f not in selected:
                selected.append(f)
                break
        
        # 3. Status
        for f in available:
            if "status" in f.name.lower() and f not in selected:
                selected.append(f)
                break
        
        # 4. Amount/value
        for f in available:
            if any(kw in f.name.lower() for kw in ["amount", "total", "value", "cost"]) and f not in selected:
                selected.append(f)
                break
        
        # Fill remaining
        for f in available:
            if len(selected) >= max_columns:
                break
            if f not in selected:
                selected.append(f)
        
        # Build columns
        columns = []
        for f in selected:
            alignment = Alignment.LEFT
            width = 20
            
            if f.category == FieldCategory.FINANCIAL:
                alignment = Alignment.RIGHT
                width = 15
            elif f.category == FieldCategory.DATE:
                alignment = Alignment.CENTER
                width = 12
            elif "description" in f.name.lower():
                width = 35
            
            columns.append(TableColumn(
                field=self._field_to_def(f, resolve_nested=False),
                width=width,
                alignment=alignment,
            ))
        
        return columns
    
    def _field_to_def(
        self,
        field: FieldInfo,
        resolve_nested: bool = True,
    ) -> FieldDef:
        """Convert FieldInfo to FieldDef."""
        path = field.path
        if resolve_nested and field.category in (FieldCategory.CONTACT, FieldCategory.NESTED):
            if field.child_fields:
                for child in field.child_fields:
                    if child.name.lower() == "short_label":
                        path = f"{field.path}.ShortLabel"
                        break
        
        format_type = FieldFormat.TEXT
        format_options = None
        
        if field.format_hint == "currency":
            format_type = FieldFormat.CURRENCY
            format_options = FormatOptions(decimals=2)
        elif field.format_hint == "date":
            format_type = FieldFormat.DATE
        elif field.format_hint == "datetime":
            format_type = FieldFormat.DATETIME
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
    
    def _find_identity_fields(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find identity fields."""
        return schema.identity_fields()
    
    def _find_best_title_field(self, schema: EntitySchema) -> Optional[FieldInfo]:
        """Find the best field for the document title."""
        identity = schema.identity_fields()
        
        # Priority: Number > Name > Subject > Title
        for pattern in ["number", "name", "subject", "title"]:
            for f in identity:
                if pattern in f.name.lower():
                    return f
        
        return identity[0] if identity else None
    
    def _find_subtitle_field(self, schema: EntitySchema) -> Optional[FieldInfo]:
        """Find a good subtitle field."""
        identity = schema.identity_fields()
        
        # Look for subject, description, or name
        for pattern in ["subject", "description", "name", "title"]:
            for f in identity:
                if pattern in f.name.lower():
                    return f
        
        # Look in text blocks
        text_blocks = schema.text_blocks()
        for pattern in ["subject", "description"]:
            for f in text_blocks:
                if pattern in f.name.lower():
                    return f
        
        return None
    
    def _find_status_field(self, schema: EntitySchema) -> Optional[FieldInfo]:
        """Find the primary status field."""
        status = schema.by_category(FieldCategory.STATUS)
        
        # Prefer field named "status"
        for f in status:
            if f.name.lower() == "status":
                return f
        
        return status[0] if status else None
    
    def _find_key_contacts(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find key contact fields in priority order."""
        contacts = schema.contact_fields()
        
        # Priority order
        priority = ["contractor", "client", "author", "assigned", "owner", "manager", "responder"]
        ordered = []
        
        for pattern in priority:
            for f in contacts:
                if pattern in f.name.lower() and f not in ordered:
                    ordered.append(f)
        
        # Add remaining
        for f in contacts:
            if f not in ordered:
                ordered.append(f)
        
        return ordered[:6]
    
    def _find_key_dates(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find key date fields in priority order."""
        dates = schema.date_fields()
        
        # Priority order
        priority = ["date", "due", "required", "start", "end", "submitted", "created"]
        ordered = []
        
        for pattern in priority:
            for f in dates:
                if pattern in f.name.lower() and f not in ordered:
                    ordered.append(f)
        
        # Add remaining
        for f in dates:
            if f not in ordered:
                ordered.append(f)
        
        return ordered[:6]
    
    def _find_total_fields(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find total/summary financial fields."""
        financials = schema.financial_fields()
        
        # Prioritize totals
        totals = [f for f in financials if "total" in f.name.lower()]
        others = [f for f in financials if f not in totals]
        
        return totals + others
    
    def _find_line_item_collections(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find collections suitable for table display."""
        collections = schema.collections()
        
        # Filter out unsuitable collections
        suitable = []
        for coll in collections:
            name_lower = coll.name.lower()
            if any(kw in name_lower for kw in ["reference", "comment", "notification", "distribution"]):
                continue
            if coll.child_fields and len(coll.child_fields) >= 2:
                suitable.append(coll)
        
        return suitable[:3]
    
    def _find_text_blocks(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find text block fields in priority order."""
        blocks = schema.text_blocks()
        
        # Priority order
        priority = ["scope", "description", "question", "answer", "response", "notes", "remarks"]
        ordered = []
        
        for pattern in priority:
            for f in blocks:
                if pattern in f.name.lower() and f not in ordered:
                    ordered.append(f)
        
        # Add remaining
        for f in blocks:
            if f not in ordered:
                ordered.append(f)
        
        return ordered
    
    def _find_routing_fields(self, schema: EntitySchema) -> List[FieldInfo]:
        """Find from/to routing fields for correspondence."""
        contacts = schema.contact_fields()
        
        routing = []
        for pattern in ["from", "author", "submitted_by", "to", "assigned", "responder"]:
            for f in contacts:
                if pattern in f.name.lower() and f not in routing:
                    routing.append(f)
        
        return routing[:4]
    
    def _create_layout(self, guidelines: DesignGuidelines) -> LayoutConfig:
        """Create layout config based on guidelines."""
        return LayoutConfig(
            orientation="portrait",
            margin_top=0.75 if guidelines.density != InformationDensity.DENSE else 0.5,
            margin_bottom=0.75 if guidelines.density != InformationDensity.DENSE else 0.5,
            margin_left=0.75,
            margin_right=0.75,
        )
    
    def _create_style(
        self,
        guidelines: DesignGuidelines,
        preferences: Dict[str, Any],
    ) -> StyleConfig:
        """Create style config based on guidelines and preferences."""
        style = StyleConfig()
        
        if guidelines.tone == VisualTone.MINIMAL:
            style.section_spacing = 0.15
        elif guidelines.tone == VisualTone.DETAILED:
            style.section_spacing = 0.3
        
        # Allow custom colors
        if "primary_color" in preferences:
            style.primary_color = preferences["primary_color"]
        if "secondary_color" in preferences:
            style.secondary_color = preferences["secondary_color"]
        
        return style
    
    def _generate_template_name(
        self,
        schema: EntitySchema,
        archetype: TemplateArchetype,
    ) -> str:
        """Generate a descriptive template name."""
        archetype_names = {
            TemplateArchetype.FORMAL_DOCUMENT: "Report",
            TemplateArchetype.EXECUTIVE_SUMMARY: "Executive Summary",
            TemplateArchetype.AUDIT_RECORD: "Audit Record",
            TemplateArchetype.ACTION_TRACKER: "Tracker",
            TemplateArchetype.FINANCIAL_REPORT: "Financial Report",
            TemplateArchetype.CORRESPONDENCE: "Correspondence",
            TemplateArchetype.FIELD_REPORT: "Field Report",
            TemplateArchetype.CHECKLIST: "Checklist",
        }
        
        archetype_name = archetype_names.get(archetype, "Report")
        return f"{schema.name} {archetype_name}"


# ============================================================================
# Convenience Functions
# ============================================================================

def compose_template(
    schema: EntitySchema,
    archetype: TemplateArchetype,
    **preferences,
) -> PortableViewTemplate:
    """Quick function to compose a template."""
    composer = CreativeComposer()
    return composer.compose(schema, archetype, preferences)


def auto_compose_template(schema: EntitySchema, user_intent: str = "") -> PortableViewTemplate:
    """Automatically compose a template with inferred archetype."""
    composer = CreativeComposer()
    design_system = DesignSystem()
    
    summary = get_schema_summary(schema)
    archetype = design_system.infer_archetype(
        entity_name=schema.name,
        field_categories=summary["field_counts"],
        user_intent=user_intent,
    )
    
    return composer.compose(schema, archetype)
