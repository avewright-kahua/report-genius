"""
Design System - Document archetypes and design principles for template generation.

This module encodes professional document design knowledge that the agent uses
to create templates that follow proper information architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TemplateArchetype(str, Enum):
    """Document archetypes that determine structure and tone."""
    
    FORMAL_DOCUMENT = "formal_document"
    EXECUTIVE_SUMMARY = "executive_summary"
    AUDIT_RECORD = "audit_record"
    ACTION_TRACKER = "action_tracker"
    FINANCIAL_REPORT = "financial_report"
    CORRESPONDENCE = "correspondence"
    FIELD_REPORT = "field_report"
    CHECKLIST = "checklist"


class InformationDensity(str, Enum):
    """How much information to include per page."""
    
    SPARSE = "sparse"
    BALANCED = "balanced"
    DENSE = "dense"


class VisualTone(str, Enum):
    """Visual treatment of the document."""
    
    MINIMAL = "minimal"
    PROFESSIONAL = "professional"
    DETAILED = "detailed"


@dataclass
class DesignGuidelines:
    """Design guidelines for a specific archetype."""
    
    archetype: TemplateArchetype
    density: InformationDensity
    tone: VisualTone
    
    section_priority: List[str] = field(default_factory=list)
    emphasize_categories: List[str] = field(default_factory=list)
    suppress_categories: List[str] = field(default_factory=list)
    
    preferred_columns: int = 2
    show_logos: bool = True
    include_footer: bool = True
    
    max_table_columns: int = 6
    include_subtotals: bool = True
    
    show_empty_text_blocks: bool = False
    max_text_blocks: int = 3


ARCHETYPE_GUIDELINES: Dict[TemplateArchetype, DesignGuidelines] = {
    
    TemplateArchetype.FORMAL_DOCUMENT: DesignGuidelines(
        archetype=TemplateArchetype.FORMAL_DOCUMENT,
        density=InformationDensity.BALANCED,
        tone=VisualTone.PROFESSIONAL,
        section_priority=["header", "identity", "parties", "terms", "signatures"],
        emphasize_categories=["identity", "contact", "status", "financial"],
        suppress_categories=["reference", "nested"],
        preferred_columns=2,
        show_logos=True,
        include_footer=True,
        max_text_blocks=4,
    ),
    
    TemplateArchetype.EXECUTIVE_SUMMARY: DesignGuidelines(
        archetype=TemplateArchetype.EXECUTIVE_SUMMARY,
        density=InformationDensity.SPARSE,
        tone=VisualTone.MINIMAL,
        section_priority=["header", "kpis", "status", "next_steps"],
        emphasize_categories=["identity", "status", "financial"],
        suppress_categories=["text_block", "collection", "reference"],
        preferred_columns=3,
        show_logos=True,
        include_footer=False,
        max_table_columns=4,
        max_text_blocks=1,
    ),
    
    TemplateArchetype.AUDIT_RECORD: DesignGuidelines(
        archetype=TemplateArchetype.AUDIT_RECORD,
        density=InformationDensity.DENSE,
        tone=VisualTone.DETAILED,
        section_priority=["header", "identity", "all_details", "chronology", "attachments"],
        emphasize_categories=["identity", "date", "status", "financial", "contact"],
        suppress_categories=[],
        preferred_columns=2,
        show_logos=True,
        include_footer=True,
        max_table_columns=8,
        include_subtotals=True,
        show_empty_text_blocks=True,
        max_text_blocks=10,
    ),
    
    TemplateArchetype.ACTION_TRACKER: DesignGuidelines(
        archetype=TemplateArchetype.ACTION_TRACKER,
        density=InformationDensity.BALANCED,
        tone=VisualTone.PROFESSIONAL,
        section_priority=["header", "status", "assignment", "dates", "description"],
        emphasize_categories=["identity", "status", "contact", "date"],
        suppress_categories=["financial", "reference"],
        preferred_columns=2,
        show_logos=False,
        include_footer=True,
        max_table_columns=5,
    ),
    
    TemplateArchetype.FINANCIAL_REPORT: DesignGuidelines(
        archetype=TemplateArchetype.FINANCIAL_REPORT,
        density=InformationDensity.BALANCED,
        tone=VisualTone.DETAILED,
        section_priority=["header", "summary_totals", "breakdown", "line_items", "notes"],
        emphasize_categories=["identity", "financial", "date"],
        suppress_categories=["text_block", "reference"],
        preferred_columns=2,
        show_logos=True,
        include_footer=True,
        max_table_columns=6,
        include_subtotals=True,
    ),
    
    TemplateArchetype.CORRESPONDENCE: DesignGuidelines(
        archetype=TemplateArchetype.CORRESPONDENCE,
        density=InformationDensity.BALANCED,
        tone=VisualTone.PROFESSIONAL,
        section_priority=["header", "from_to", "subject", "body", "response", "attachments"],
        emphasize_categories=["identity", "contact", "date", "text_block"],
        suppress_categories=["financial", "collection"],
        preferred_columns=2,
        show_logos=True,
        include_footer=True,
        max_text_blocks=5,
    ),
    
    TemplateArchetype.FIELD_REPORT: DesignGuidelines(
        archetype=TemplateArchetype.FIELD_REPORT,
        density=InformationDensity.BALANCED,
        tone=VisualTone.DETAILED,
        section_priority=["header", "location", "conditions", "observations", "photos", "actions"],
        emphasize_categories=["identity", "date", "text_block", "lookup"],
        suppress_categories=["financial"],
        preferred_columns=2,
        show_logos=True,
        include_footer=True,
        max_text_blocks=6,
    ),
    
    TemplateArchetype.CHECKLIST: DesignGuidelines(
        archetype=TemplateArchetype.CHECKLIST,
        density=InformationDensity.DENSE,
        tone=VisualTone.MINIMAL,
        section_priority=["header", "items", "signatures"],
        emphasize_categories=["identity", "status", "boolean"],
        suppress_categories=["text_block", "financial"],
        preferred_columns=1,
        show_logos=False,
        include_footer=True,
        max_table_columns=4,
    ),
}


class DesignSystem:
    """Document design system that provides intelligent layout decisions."""
    
    def __init__(self):
        self.guidelines = ARCHETYPE_GUIDELINES
    
    def infer_archetype(
        self,
        entity_name: str,
        user_intent: Optional[str] = None,
        field_categories: Optional[Dict[str, int]] = None,
    ) -> TemplateArchetype:
        """Infer the best archetype based on entity characteristics and user intent."""
        if field_categories is None:
            field_categories = {}
        
        name_lower = entity_name.lower()
        intent_lower = (user_intent or "").lower()
        
        # Check user intent first
        if intent_lower:
            if any(kw in intent_lower for kw in ["executive", "summary", "brief", "quick"]):
                return TemplateArchetype.EXECUTIVE_SUMMARY
            if any(kw in intent_lower for kw in ["audit", "compliance", "complete", "full"]):
                return TemplateArchetype.AUDIT_RECORD
            if any(kw in intent_lower for kw in ["financial", "cost", "budget", "money"]):
                return TemplateArchetype.FINANCIAL_REPORT
            if any(kw in intent_lower for kw in ["field", "observation", "inspection", "site"]):
                return TemplateArchetype.FIELD_REPORT
            if any(kw in intent_lower for kw in ["checklist", "punch", "list"]):
                return TemplateArchetype.CHECKLIST
        
        # Infer from entity name
        if any(kw in name_lower for kw in ["contract", "agreement", "amendment"]):
            if field_categories.get("financial", 0) > 3:
                return TemplateArchetype.FINANCIAL_REPORT
            return TemplateArchetype.FORMAL_DOCUMENT
        
        if any(kw in name_lower for kw in ["rfi", "request", "submittal", "transmittal"]):
            return TemplateArchetype.CORRESPONDENCE
        
        if any(kw in name_lower for kw in ["invoice", "payment", "budget", "cost"]):
            return TemplateArchetype.FINANCIAL_REPORT
        
        if any(kw in name_lower for kw in ["observation", "inspection", "daily", "report"]):
            return TemplateArchetype.FIELD_REPORT
        
        if any(kw in name_lower for kw in ["punch", "checklist", "snag"]):
            return TemplateArchetype.CHECKLIST
        
        if any(kw in name_lower for kw in ["change", "order", "modification"]):
            return TemplateArchetype.FORMAL_DOCUMENT
        
        # Default based on field composition
        if field_categories.get("financial", 0) > 5:
            return TemplateArchetype.FINANCIAL_REPORT
        if field_categories.get("text_block", 0) > 3:
            return TemplateArchetype.CORRESPONDENCE
        
        return TemplateArchetype.FORMAL_DOCUMENT
    
    def get_guidelines(self, archetype: TemplateArchetype) -> DesignGuidelines:
        """Get design guidelines for an archetype."""
        return self.guidelines.get(archetype, self.guidelines[TemplateArchetype.FORMAL_DOCUMENT])
    
    def suggest_section_groupings(
        self,
        archetype: TemplateArchetype,
        available_fields: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Suggest how to group fields into sections based on archetype."""
        guidelines = self.get_guidelines(archetype)
        suggestions = []
        
        # Group fields by category
        by_category: Dict[str, List[Dict]] = {}
        for f in available_fields:
            cat = f.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)
        
        # Apply archetype-specific logic
        if archetype == TemplateArchetype.EXECUTIVE_SUMMARY:
            suggestions = self._suggest_executive_sections(by_category, guidelines)
        elif archetype == TemplateArchetype.FINANCIAL_REPORT:
            suggestions = self._suggest_financial_sections(by_category, guidelines)
        elif archetype == TemplateArchetype.CORRESPONDENCE:
            suggestions = self._suggest_correspondence_sections(by_category, guidelines)
        else:
            suggestions = self._suggest_standard_sections(by_category, guidelines)
        
        return suggestions
    
    def _suggest_executive_sections(
        self,
        by_category: Dict[str, List[Dict]],
        guidelines: DesignGuidelines,
    ) -> List[Dict[str, Any]]:
        """Executive summary: KPIs at top, minimal text."""
        sections = []
        
        identity = by_category.get("identity", [])
        if identity:
            sections.append({
                "title": None,
                "type": "header",
                "fields": [f["path"] for f in identity[:2]],
                "rationale": "Clean header with document identifier"
            })
        
        status = by_category.get("status", [])
        dates = by_category.get("date", [])[:2]
        if status or dates:
            sections.append({
                "title": "Status",
                "type": "detail",
                "fields": [f["path"] for f in status[:3]] + [f["path"] for f in dates],
                "rationale": "Key status indicators at a glance"
            })
        
        financial = by_category.get("financial", [])
        totals = [f for f in financial if "total" in f.get("name", "").lower()]
        if totals:
            sections.append({
                "title": "Financial Summary",
                "type": "detail",
                "fields": [f["path"] for f in totals[:4]],
                "rationale": "High-level financial figures"
            })
        
        return sections
    
    def _suggest_financial_sections(
        self,
        by_category: Dict[str, List[Dict]],
        guidelines: DesignGuidelines,
    ) -> List[Dict[str, Any]]:
        """Financial report: Emphasis on numbers and line items."""
        sections = []
        
        identity = by_category.get("identity", [])
        sections.append({
            "title": None,
            "type": "header",
            "fields": [f["path"] for f in identity[:2]],
            "rationale": "Document identification"
        })
        
        financial = by_category.get("financial", [])
        totals = [f for f in financial if "total" in f.get("name", "").lower()]
        if totals:
            sections.append({
                "title": "Summary",
                "type": "detail",
                "fields": [f["path"] for f in totals],
                "rationale": "Financial totals prominently displayed"
            })
        
        contacts = by_category.get("contact", [])
        if contacts:
            sections.append({
                "title": "Parties",
                "type": "detail",
                "fields": [f["path"] for f in contacts[:4]],
                "rationale": "Contractor, client, and key contacts"
            })
        
        collections = by_category.get("collection", [])
        for coll in collections[:2]:
            sections.append({
                "title": coll.get("label", "Items"),
                "type": "table",
                "fields": [coll["path"]],
                "rationale": "Line item breakdown with amounts"
            })
        
        return sections
    
    def _suggest_correspondence_sections(
        self,
        by_category: Dict[str, List[Dict]],
        guidelines: DesignGuidelines,
    ) -> List[Dict[str, Any]]:
        """Correspondence: From/To, Subject, Body, Response pattern."""
        sections = []
        
        identity = by_category.get("identity", [])
        sections.append({
            "title": None,
            "type": "header",
            "fields": [f["path"] for f in identity[:2]],
            "rationale": "Document number and subject"
        })
        
        contacts = by_category.get("contact", [])
        from_to = [f for f in contacts if any(kw in f.get("name", "").lower() 
                   for kw in ["from", "to", "author", "assigned", "responder"])]
        if from_to:
            sections.append({
                "title": None,
                "type": "detail",
                "fields": [f["path"] for f in from_to[:4]],
                "rationale": "Who sent this and who needs to respond"
            })
        
        dates = by_category.get("date", [])
        if dates:
            sections.append({
                "title": "Dates",
                "type": "detail",
                "fields": [f["path"] for f in dates[:4]],
                "rationale": "Key dates and deadlines"
            })
        
        text_blocks = by_category.get("text_block", [])
        for block in text_blocks[:4]:
            sections.append({
                "title": block.get("label"),
                "type": "text",
                "fields": [block["path"]],
                "rationale": "Main content body"
            })
        
        return sections
    
    def _suggest_standard_sections(
        self,
        by_category: Dict[str, List[Dict]],
        guidelines: DesignGuidelines,
    ) -> List[Dict[str, Any]]:
        """Standard document with logical groupings."""
        sections = []
        
        identity = by_category.get("identity", [])
        sections.append({
            "title": None,
            "type": "header",
            "fields": [f["path"] for f in identity[:2]],
            "rationale": "Document identification"
        })
        
        status = by_category.get("status", [])
        contacts = by_category.get("contact", [])[:2]
        dates = by_category.get("date", [])[:2]
        summary_fields = status + contacts + dates
        if summary_fields:
            sections.append({
                "title": None,
                "type": "detail",
                "fields": [f["path"] for f in summary_fields[:6]],
                "rationale": "Key metadata at a glance"
            })
        
        financial = by_category.get("financial", [])
        if financial:
            sections.append({
                "title": "Financials",
                "type": "detail",
                "fields": [f["path"] for f in financial[:6]],
                "rationale": "Financial details grouped together"
            })
        
        text_blocks = by_category.get("text_block", [])
        for block in text_blocks[:guidelines.max_text_blocks]:
            sections.append({
                "title": block.get("label"),
                "type": "text",
                "fields": [block["path"]],
                "rationale": "Long-form content"
            })
        
        collections = by_category.get("collection", [])
        for coll in collections[:2]:
            sections.append({
                "title": coll.get("label"),
                "type": "table",
                "fields": [coll["path"]],
                "rationale": "Tabular data"
            })
        
        return sections
