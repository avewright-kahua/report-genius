"""
Smart Agent - SOTA agentic template generation with structured reasoning.

This module implements a state-of-the-art agent architecture using:
- Tool-based reasoning with structured outputs
- ReAct-style thinking with explicit planning
- Domain-specific design knowledge
- Multi-turn refinement with memory
- Comprehensive schema understanding

The agent doesn't just generate templates - it reasons about document design,
user intent, and information architecture to create purposeful documents.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypedDict, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .design_system import (
    DesignGuidelines,
    DesignSystem,
    InformationDensity,
    TemplateArchetype,
    VisualTone,
)

load_dotenv()


# ============================================================================
# Agent Configuration
# ============================================================================

SYSTEM_PROMPT = """You are an expert document designer specializing in construction and project management portable view templates.

## Your Expertise
- Professional document design and information architecture
- Kahua platform entity structures and portable view syntax
- Construction industry workflows (RFIs, Submittals, Contracts, Change Orders, etc.)
- Visual hierarchy and data presentation best practices

## Your Approach
1. **Understand Intent**: What is the user trying to accomplish? Who is the audience?
2. **Analyze Data**: What entity type are we working with? What fields are available?
3. **Design with Purpose**: Every section should serve a clear purpose. Don't just dump fields.
4. **Apply Best Practices**: Use appropriate archetypes, visual hierarchy, and information grouping.
5. **Iterate**: Make targeted refinements based on feedback.

## Design Principles
- **Visual Hierarchy**: Most important information should be most prominent
- **Logical Grouping**: Related fields belong together
- **Appropriate Density**: Match information density to document purpose
- **Conditional Content**: Hide empty sections; show relevant data
- **Professional Aesthetics**: Clean, scannable, purposeful layouts

## Template Archetypes
- FORMAL_DOCUMENT: Contracts, agreements requiring signatures
- EXECUTIVE_SUMMARY: Quick status overview for leadership
- AUDIT_RECORD: Complete record with all details for compliance
- ACTION_TRACKER: Focus on status, assignments, due dates
- FINANCIAL_REPORT: Cost breakdowns, line items, totals
- CORRESPONDENCE: RFIs, submittals, transmittals with question/answer pattern
- FIELD_REPORT: Observations, inspections, site conditions
- CHECKLIST: Punch lists, inspection items

## When Creating Templates
1. Identify the appropriate archetype based on entity type and user intent
2. Select fields that serve the document's purpose
3. Organize into logical sections with clear hierarchy
4. Apply conditional rendering for optional content
5. Consider the reader's workflow and information needs

## Output Format
Always provide structured responses using the available tools. Include your reasoning.
When showing template changes, explain what changed and why."""


class ToolDefinition(BaseModel):
    """Definition of a tool the agent can use."""
    
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    """A message in the conversation history."""
    
    role: Literal["user", "assistant", "system", "tool_result"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationState(BaseModel):
    """State maintained across the conversation."""
    
    model_config = {"use_enum_values": True}
    
    messages: List[AgentMessage] = Field(default_factory=list)
    current_template: Optional[Dict[str, Any]] = None
    current_entity_type: Optional[str] = None
    current_archetype: Optional[TemplateArchetype] = None
    pending_changes: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Tool Implementations
# ============================================================================

class AgentTools:
    """Tools available to the agent for template operations."""
    
    def __init__(self, schemas: Dict[str, Any], design_system: DesignSystem):
        self.schemas = schemas
        self.design_system = design_system
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for the LLM."""
        return [
            {
                "name": "list_entity_types",
                "description": "List all available entity types that can be used for templates. Returns entity names, descriptions, and field category summaries.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_entity_schema",
                "description": "Get detailed field information for an entity type. Use this to understand what data is available before designing a template.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "The entity type name (e.g., 'contract', 'rfi', 'submittal')"
                        },
                        "category_filter": {
                            "type": "string",
                            "description": "Optional filter by category (identity, financial, contact, text_block, collection, date, status, lookup, boolean)",
                            "enum": ["identity", "financial", "contact", "text_block", "collection", "date", "status", "lookup", "boolean", "numeric"]
                        }
                    },
                    "required": ["entity_type"]
                }
            },
            {
                "name": "analyze_design_requirements",
                "description": "Analyze what the user wants and recommend an appropriate template archetype and design approach. Call this before creating a template to ensure alignment with user needs.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "The entity type to analyze"
                        },
                        "user_intent": {
                            "type": "string",
                            "description": "What the user described wanting (in your own words based on conversation)"
                        },
                        "audience": {
                            "type": "string",
                            "description": "Who will read this document (executives, field workers, auditors, etc.)"
                        }
                    },
                    "required": ["entity_type", "user_intent"]
                }
            },
            {
                "name": "create_template",
                "description": "Create a new template with intelligent defaults based on the chosen archetype and entity type. The template will be created with appropriate sections, fields, and formatting.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "description": "The entity type to create a template for"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name for the template"
                        },
                        "archetype": {
                            "type": "string",
                            "description": "The template archetype to use",
                            "enum": ["formal_document", "executive_summary", "audit_record", "action_tracker", "financial_report", "correspondence", "field_report", "checklist"]
                        },
                        "custom_sections": {
                            "type": "array",
                            "description": "Optional list of custom section configurations",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "type": {"type": "string", "enum": ["header", "detail", "text", "table", "divider"]},
                                    "fields": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "include_fields": {
                            "type": "array",
                            "description": "Specific field paths to definitely include",
                            "items": {"type": "string"}
                        },
                        "exclude_fields": {
                            "type": "array",
                            "description": "Specific field paths to exclude",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["entity_type", "archetype"]
                }
            },
            {
                "name": "modify_template",
                "description": "Modify the current template by adding, removing, or changing sections and fields.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The operation to perform",
                            "enum": ["add_section", "remove_section", "add_fields", "remove_fields", "reorder_sections", "update_section", "change_layout"]
                        },
                        "target": {
                            "type": "string",
                            "description": "The section title or index to modify (for section operations)"
                        },
                        "config": {
                            "type": "object",
                            "description": "Configuration for the operation",
                            "properties": {
                                "section_type": {"type": "string"},
                                "title": {"type": "string"},
                                "fields": {"type": "array", "items": {"type": "string"}},
                                "columns": {"type": "integer"},
                                "new_order": {"type": "array", "items": {"type": "integer"}},
                                "position": {"type": "string", "enum": ["before", "after", "first", "last"]}
                            }
                        }
                    },
                    "required": ["operation"]
                }
            },
            {
                "name": "preview_template",
                "description": "Generate a preview of the current template showing how it will render with sample data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Preview format",
                            "enum": ["markdown", "structure", "kahua_syntax"]
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "explain_template",
                "description": "Get a detailed explanation of the current template's structure, design decisions, and how each section serves the document's purpose.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "suggest_improvements",
                "description": "Analyze the current template and suggest potential improvements based on best practices and the document's purpose.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "focus_area": {
                            "type": "string",
                            "description": "Optional area to focus suggestions on",
                            "enum": ["completeness", "readability", "hierarchy", "financials", "conditionals"]
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "export_template",
                "description": "Export the current template to a specific format for use.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "Export format",
                            "enum": ["json", "docx"]
                        },
                        "filename": {
                            "type": "string",
                            "description": "Optional filename for the export"
                        }
                    },
                    "required": ["format"]
                }
            }
        ]
    
    def _resolve_entity_type(self, entity_type: str) -> Optional[str]:
        """Resolve an entity type name (case-insensitive).
        
        Returns the actual key in self.schemas or None if not found.
        """
        entity_lower = entity_type.lower()
        for key in self.schemas:
            if key.lower() == entity_lower:
                return key
        return None
    
    def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Any, ConversationState]:
        """Execute a tool and return the result with updated state."""
        
        method = getattr(self, f"_tool_{tool_name}", None)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}, state
        
        return method(args, state)
    
    def _tool_list_entity_types(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """List available entity types."""
        result = []
        for name, schema in self.schemas.items():
            summary = self._get_schema_summary(schema)
            result.append({
                "name": name,
                "entity_def": schema.entity_def,
                "display_name": schema.name,
                "total_fields": len(schema.fields),
                "field_categories": summary["field_counts"],
                "has_collections": summary["field_counts"].get("collection", 0) > 0,
                "has_financials": summary["field_counts"].get("financial", 0) > 0,
            })
        
        return {"entities": result}, state
    
    def _tool_get_entity_schema(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Get detailed schema information."""
        entity_type_input = args.get("entity_type", "")
        entity_type = self._resolve_entity_type(entity_type_input)
        category_filter = args.get("category_filter")
        
        if not entity_type:
            return {
                "error": f"Unknown entity type: {entity_type_input}",
                "available": list(self.schemas.keys())
            }, state
        
        schema = self.schemas[entity_type]
        summary = self._get_schema_summary(schema)
        
        if category_filter:
            fields = summary["fields_by_category"].get(category_filter, [])
            return {
                "entity_type": entity_type,
                "category": category_filter,
                "fields": fields,
            }, state
        
        return {
            "entity_type": entity_type,
            "entity_def": schema.entity_def,
            "name": schema.name,
            "field_counts": summary["field_counts"],
            "fields_by_category": summary["fields_by_category"],
        }, state
    
    def _tool_analyze_design_requirements(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Analyze and recommend design approach."""
        entity_type_input = args.get("entity_type", "")
        entity_type = self._resolve_entity_type(entity_type_input)
        user_intent = args.get("user_intent", "")
        audience = args.get("audience", "general")
        
        if not entity_type:
            return {"error": f"Unknown entity type: {entity_type_input}"}, state
        
        schema = self.schemas[entity_type]
        summary = self._get_schema_summary(schema)
        
        # Infer archetype
        archetype = self.design_system.infer_archetype(
            entity_name=schema.name,
            field_categories=summary["field_counts"],
            user_intent=user_intent,
        )
        
        guidelines = self.design_system.get_guidelines(archetype)
        
        # Get section suggestions
        fields_for_suggestion = []
        for cat, fields in summary["fields_by_category"].items():
            for f in fields:
                f["category"] = cat
                fields_for_suggestion.append(f)
        
        section_suggestions = self.design_system.suggest_section_groupings(
            archetype=archetype,
            available_fields=fields_for_suggestion,
        )
        
        result = {
            "recommended_archetype": archetype.value,
            "archetype_description": self._describe_archetype(archetype),
            "design_guidelines": {
                "information_density": guidelines.density.value,
                "visual_tone": guidelines.tone.value,
                "preferred_columns": guidelines.preferred_columns,
                "show_logos": guidelines.show_logos,
                "max_text_blocks": guidelines.max_text_blocks,
            },
            "section_suggestions": section_suggestions,
            "key_fields_to_include": self._identify_key_fields(schema, archetype),
            "fields_to_consider_excluding": guidelines.suppress_categories,
        }
        
        # Update state
        state.current_entity_type = entity_type
        state.current_archetype = archetype
        
        return result, state
    
    def _tool_create_template(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Create a new template."""
        entity_type_input = args.get("entity_type", "")
        entity_type = self._resolve_entity_type(entity_type_input)
        name = args.get("name")
        archetype_str = args.get("archetype", "formal_document")
        custom_sections = args.get("custom_sections", [])
        include_fields = args.get("include_fields", [])
        exclude_fields = args.get("exclude_fields", [])
        
        if not entity_type:
            return {"error": f"Unknown entity type: {entity_type_input}"}, state
        
        schema = self.schemas[entity_type]
        archetype = TemplateArchetype(archetype_str)
        guidelines = self.design_system.get_guidelines(archetype)
        
        # Generate template
        from template_generator import generate_template
        from template_schema import PortableViewTemplate
        
        template = generate_template(
            schema=schema,
            name=name or f"{schema.name} - {archetype.value.replace('_', ' ').title()}",
            include_financials="financial" not in guidelines.suppress_categories,
            include_text_blocks="text_block" not in guidelines.suppress_categories,
            include_tables="collection" not in guidelines.suppress_categories,
        )
        
        # Apply custom sections if provided
        if custom_sections:
            template = self._apply_custom_sections(template, custom_sections, schema)
        
        # Filter fields
        if exclude_fields:
            template = self._filter_excluded_fields(template, exclude_fields)
        
        # Add requested fields
        if include_fields:
            template = self._add_requested_fields(template, include_fields, schema)
        
        # Store in state
        state.current_template = template.model_dump()
        state.current_entity_type = entity_type
        state.current_archetype = archetype
        
        # Generate summary
        sections_summary = [
            {
                "index": i,
                "type": s.type.value,
                "title": s.title,
                "field_count": self._count_section_fields(s),
            }
            for i, s in enumerate(template.get_sections_ordered())
        ]
        
        return {
            "success": True,
            "template_name": template.name,
            "template_id": template.id,
            "archetype": archetype.value,
            "sections": sections_summary,
            "total_sections": len(template.sections),
        }, state
    
    def _tool_modify_template(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Modify the current template."""
        if not state.current_template:
            return {"error": "No template currently loaded. Create one first."}, state
        
        operation = args.get("operation")
        target = args.get("target")
        config = args.get("config", {})
        
        from template_schema import (
            PortableViewTemplate, Section, SectionType,
            DetailConfig, TextConfig, TableConfig, HeaderConfig,
            FieldDef, FieldFormat, Condition, ConditionOperator, TableColumn,
        )
        
        template = PortableViewTemplate(**state.current_template)
        
        if operation == "add_section":
            section_type = SectionType(config.get("section_type", "detail"))
            new_section = self._create_section(
                section_type=section_type,
                title=config.get("title"),
                fields=config.get("fields", []),
                order=len(template.sections),
            )
            template.add_section(new_section)
            result = {"added_section": config.get("title") or section_type.value}
        
        elif operation == "remove_section":
            removed = False
            for i, section in enumerate(template.sections):
                if (target and section.title and target.lower() in section.title.lower()) or \
                   (target and target.isdigit() and int(target) == i):
                    template.sections.pop(i)
                    removed = True
                    break
            result = {"removed": removed, "target": target}
        
        elif operation == "add_fields":
            fields_to_add = config.get("fields", [])
            # Add to last detail section or create new one
            added_to = None
            for section in reversed(template.sections):
                if section.type == SectionType.DETAIL and section.detail_config:
                    schema = self.schemas.get(state.current_entity_type)
                    for path in fields_to_add:
                        field_def = self._make_field_def(path, schema)
                        section.detail_config.fields.append(field_def)
                    added_to = section.title or "detail section"
                    break
            
            if not added_to:
                # Create new section
                new_section = self._create_section(
                    section_type=SectionType.DETAIL,
                    title=config.get("title", "Additional Fields"),
                    fields=fields_to_add,
                    order=len(template.sections),
                )
                template.add_section(new_section)
                added_to = "new section"
            
            result = {"added_fields": fields_to_add, "to_section": added_to}
        
        elif operation == "remove_fields":
            fields_to_remove = set(f.lower() for f in config.get("fields", []))
            removed_count = 0
            
            for section in template.sections:
                if section.detail_config:
                    original_len = len(section.detail_config.fields)
                    section.detail_config.fields = [
                        f for f in section.detail_config.fields
                        if f.path.lower() not in fields_to_remove
                    ]
                    removed_count += original_len - len(section.detail_config.fields)
            
            result = {"removed_fields": removed_count}
        
        elif operation == "reorder_sections":
            new_order = config.get("new_order", [])
            if len(new_order) == len(template.sections):
                template.reorder_sections(new_order)
                result = {"reordered": True}
            else:
                result = {"error": "new_order must match section count"}
        
        elif operation == "update_section":
            updated = False
            for section in template.sections:
                if (target and section.title and target.lower() in section.title.lower()):
                    if "title" in config:
                        section.title = config["title"]
                    if "columns" in config and section.detail_config:
                        section.detail_config.columns = config["columns"]
                    updated = True
                    break
            result = {"updated": updated, "target": target}
        
        elif operation == "change_layout":
            if "columns" in config:
                for section in template.sections:
                    if section.detail_config:
                        section.detail_config.columns = config["columns"]
            result = {"layout_changed": True}
        
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        # Update state
        state.current_template = template.model_dump()
        
        return result, state
    
    def _tool_preview_template(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Generate template preview."""
        if not state.current_template:
            return {"error": "No template loaded"}, state
        
        format_type = args.get("format", "markdown")
        
        from template_schema import PortableViewTemplate
        from template_renderer import render_to_markdown, generate_sample_data
        
        template = PortableViewTemplate(**state.current_template)
        
        if format_type == "markdown":
            sample = generate_sample_data(template)
            preview = render_to_markdown(template, sample)
            return {"preview": preview, "format": "markdown"}, state
        
        elif format_type == "structure":
            sections = []
            for s in template.get_sections_ordered():
                section_info = {
                    "type": s.type.value,
                    "title": s.title,
                    "has_condition": s.condition is not None,
                }
                if s.detail_config:
                    section_info["fields"] = [f.path for f in s.detail_config.fields]
                if s.table_config:
                    section_info["source"] = s.table_config.source
                    section_info["columns"] = [c.field.path for c in s.table_config.columns]
                if s.text_config:
                    section_info["content_template"] = s.text_config.content[:100]
                sections.append(section_info)
            
            return {"structure": sections, "format": "structure"}, state
        
        elif format_type == "kahua_syntax":
            from docx_renderer import render_template_to_docx
            # Return a summary of the Kahua placeholders that would be generated
            placeholders = self._extract_kahua_placeholders(template)
            return {"placeholders": placeholders, "format": "kahua_syntax"}, state
        
        return {"error": f"Unknown format: {format_type}"}, state
    
    def _tool_explain_template(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Explain the current template."""
        if not state.current_template:
            return {"error": "No template loaded"}, state
        
        from template_schema import PortableViewTemplate
        template = PortableViewTemplate(**state.current_template)
        
        explanations = []
        for i, section in enumerate(template.get_sections_ordered()):
            exp = {
                "section": i + 1,
                "type": section.type.value,
                "title": section.title,
                "purpose": self._explain_section_purpose(section),
            }
            
            if section.condition:
                exp["conditional"] = f"Only shown when {section.condition.field} {section.condition.op.value}"
            
            if section.detail_config:
                exp["fields"] = [
                    {"path": f.path, "label": f.label, "format": f.format.value}
                    for f in section.detail_config.fields
                ]
            
            explanations.append(exp)
        
        return {
            "template_name": template.name,
            "entity": template.entity_def,
            "archetype": state.current_archetype.value if state.current_archetype else "unknown",
            "sections": explanations,
            "design_rationale": self._generate_design_rationale(template, state),
        }, state
    
    def _tool_suggest_improvements(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Suggest template improvements."""
        if not state.current_template:
            return {"error": "No template loaded"}, state
        
        focus_area = args.get("focus_area")
        
        from template_schema import PortableViewTemplate
        template = PortableViewTemplate(**state.current_template)
        
        suggestions = []
        
        # Analyze completeness
        if not focus_area or focus_area == "completeness":
            if state.current_entity_type:
                schema = self.schemas.get(state.current_entity_type)
                if schema:
                    missing = self._find_missing_key_fields(template, schema)
                    if missing:
                        suggestions.append({
                            "area": "completeness",
                            "suggestion": f"Consider adding these commonly used fields: {', '.join(missing[:5])}",
                            "action": "add_fields",
                            "fields": missing[:5],
                        })
        
        # Analyze readability
        if not focus_area or focus_area == "readability":
            large_sections = [
                s for s in template.sections
                if s.detail_config and len(s.detail_config.fields) > 8
            ]
            if large_sections:
                suggestions.append({
                    "area": "readability",
                    "suggestion": "Some sections have many fields. Consider splitting for better readability.",
                    "sections": [s.title for s in large_sections],
                })
        
        # Analyze hierarchy
        if not focus_area or focus_area == "hierarchy":
            if not any(s.type.value == "header" for s in template.sections):
                suggestions.append({
                    "area": "hierarchy",
                    "suggestion": "Template lacks a header section. Add one for clear document identity.",
                })
        
        # Analyze conditionals
        if not focus_area or focus_area == "conditionals":
            text_sections = [s for s in template.sections if s.type.value == "text"]
            unconditional_text = [s for s in text_sections if not s.condition]
            if unconditional_text:
                suggestions.append({
                    "area": "conditionals",
                    "suggestion": "Text sections without conditions may show empty content. Add visibility conditions.",
                    "sections": [s.title for s in unconditional_text],
                })
        
        return {"suggestions": suggestions}, state
    
    def _tool_export_template(
        self,
        args: Dict[str, Any],
        state: ConversationState,
    ) -> Tuple[Dict[str, Any], ConversationState]:
        """Export the template."""
        if not state.current_template:
            return {"error": "No template loaded"}, state
        
        format_type = args.get("format", "json")
        filename = args.get("filename")
        
        from template_schema import PortableViewTemplate
        template = PortableViewTemplate(**state.current_template)
        
        if format_type == "json":
            output = template.model_dump_json(indent=2)
            if filename:
                path = Path(f"pv_templates/generated/{filename}.json")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(output)
                return {"exported": str(path), "format": "json"}, state
            return {"template_json": output, "format": "json"}, state
        
        elif format_type == "docx":
            from docx_renderer import DocxRenderer
            
            renderer = DocxRenderer(template)
            
            if filename:
                path = Path(f"pv_templates/generated/{filename}.docx")
                path.parent.mkdir(parents=True, exist_ok=True)
                renderer.render_to_file(path)
                return {"exported": str(path), "format": "docx"}, state
            
            # Return as bytes
            doc_bytes = renderer.render_to_bytes()
            import base64
            encoded = base64.b64encode(doc_bytes).decode()
            return {"docx_base64": encoded, "format": "docx"}, state
        
        return {"error": f"Unknown format: {format_type}"}, state
    
    # ========== Helper Methods ==========
    
    def _get_schema_summary(self, schema) -> Dict[str, Any]:
        """Get summary of schema fields by category."""
        from schema_introspector import get_schema_summary
        return get_schema_summary(schema)
    
    def _describe_archetype(self, archetype: TemplateArchetype) -> str:
        """Get human-readable archetype description."""
        descriptions = {
            TemplateArchetype.FORMAL_DOCUMENT: "Professional document suitable for contracts and agreements requiring signatures",
            TemplateArchetype.EXECUTIVE_SUMMARY: "Condensed overview highlighting key metrics and status for quick review",
            TemplateArchetype.AUDIT_RECORD: "Comprehensive record capturing all details for compliance and audit purposes",
            TemplateArchetype.ACTION_TRACKER: "Task-focused document emphasizing assignments, status, and due dates",
            TemplateArchetype.FINANCIAL_REPORT: "Cost-centered document with line items, breakdowns, and totals",
            TemplateArchetype.CORRESPONDENCE: "Communication document with question/answer or request/response pattern",
            TemplateArchetype.FIELD_REPORT: "Observation-based document for site conditions and inspections",
            TemplateArchetype.CHECKLIST: "Item-based document for tracking completion of tasks",
        }
        return descriptions.get(archetype, "General purpose document")
    
    def _identify_key_fields(self, schema, archetype: TemplateArchetype) -> List[str]:
        """Identify key fields based on archetype."""
        guidelines = self.design_system.get_guidelines(archetype)
        key_fields = []
        
        for field in schema.fields:
            if field.category.value in guidelines.emphasize_categories:
                key_fields.append(field.path)
        
        return key_fields[:15]  # Limit to most important
    
    def _create_section(
        self,
        section_type,
        title: Optional[str],
        fields: List[str],
        order: int,
    ):
        """Create a section from configuration."""
        from template_schema import (
            Section, SectionType, DetailConfig, TextConfig,
            FieldDef, FieldFormat, Condition, ConditionOperator,
        )
        
        field_defs = [FieldDef(path=p) for p in fields]
        
        if section_type == SectionType.DETAIL:
            return Section(
                type=section_type,
                title=title,
                order=order,
                detail_config=DetailConfig(
                    fields=field_defs,
                    columns=2 if len(fields) > 2 else 1,
                ),
            )
        elif section_type == SectionType.TEXT:
            content = fields[0] if fields else ""
            return Section(
                type=section_type,
                title=title,
                order=order,
                condition=Condition(field=content, op=ConditionOperator.NOT_EMPTY) if content else None,
                text_config=TextConfig(content=f"{{{content}}}"),
            )
        else:
            return Section(type=section_type, title=title, order=order)
    
    def _make_field_def(self, path: str, schema) -> "FieldDef":
        """Create a FieldDef for a path."""
        from template_schema import FieldDef, FieldFormat
        
        if schema:
            for field in schema.fields:
                if field.path.lower() == path.lower():
                    from template_generator import _field_to_def
                    return _field_to_def(field)
        
        return FieldDef(path=path)
    
    def _count_section_fields(self, section) -> int:
        """Count fields in a section."""
        if section.detail_config:
            return len(section.detail_config.fields)
        if section.header_config:
            return len(section.header_config.fields)
        if section.table_config:
            return len(section.table_config.columns)
        return 0
    
    def _explain_section_purpose(self, section) -> str:
        """Explain what a section is for."""
        purposes = {
            "header": "Document identification and branding",
            "detail": "Key-value field display",
            "text": "Long-form content display",
            "table": "Tabular data for collections/line items",
            "divider": "Visual separation between content areas",
            "spacer": "Vertical whitespace",
            "image": "Visual content display",
        }
        return purposes.get(section.type.value, "Content section")
    
    def _generate_design_rationale(self, template, state: ConversationState) -> str:
        """Generate explanation of design choices."""
        if not state.current_archetype:
            return "Standard document layout"
        
        archetype = state.current_archetype
        guidelines = self.design_system.get_guidelines(archetype)
        
        return (
            f"This template uses the {archetype.value.replace('_', ' ')} pattern, "
            f"optimized for {guidelines.density.value} information density with a "
            f"{guidelines.tone.value} visual style."
        )
    
    def _find_missing_key_fields(self, template, schema) -> List[str]:
        """Find commonly used fields not in the template."""
        # Get all field paths in template
        template_fields = set()
        for section in template.sections:
            if section.detail_config:
                template_fields.update(f.path.lower() for f in section.detail_config.fields)
            if section.header_config:
                template_fields.update(f.path.lower() for f in section.header_config.fields)
        
        # Key field patterns
        key_patterns = ["number", "status", "date", "author", "assigned", "description", "total"]
        missing = []
        
        for field in schema.fields:
            if field.path.lower() not in template_fields:
                if any(p in field.name.lower() for p in key_patterns):
                    missing.append(field.path)
        
        return missing
    
    def _extract_kahua_placeholders(self, template) -> List[Dict[str, str]]:
        """Extract the Kahua placeholders that would be generated."""
        from docx_renderer import (
            build_attribute_placeholder,
            build_currency_placeholder,
            build_date_placeholder,
        )
        
        placeholders = []
        for section in template.sections:
            if section.detail_config:
                for field in section.detail_config.fields:
                    if field.format.value == "currency":
                        ph = build_currency_placeholder(field.path)
                    elif field.format.value in ("date", "datetime"):
                        ph = build_date_placeholder(field.path)
                    else:
                        ph = build_attribute_placeholder(field.path)
                    placeholders.append({"field": field.path, "placeholder": ph})
        
        return placeholders
    
    def _apply_custom_sections(self, template, custom_sections, schema):
        """Apply custom section configurations."""
        # Clear existing sections if custom ones provided
        if custom_sections:
            from template_schema import SectionType
            template.sections = []
            for i, cs in enumerate(custom_sections):
                section = self._create_section(
                    section_type=SectionType(cs.get("type", "detail")),
                    title=cs.get("title"),
                    fields=cs.get("fields", []),
                    order=i,
                )
                template.sections.append(section)
        return template
    
    def _filter_excluded_fields(self, template, exclude_fields):
        """Remove excluded fields from template."""
        exclude_set = set(f.lower() for f in exclude_fields)
        for section in template.sections:
            if section.detail_config:
                section.detail_config.fields = [
                    f for f in section.detail_config.fields
                    if f.path.lower() not in exclude_set
                ]
        return template
    
    def _add_requested_fields(self, template, include_fields, schema):
        """Add specifically requested fields."""
        from template_schema import Section, SectionType, DetailConfig
        from template_generator import _field_to_def
        
        field_defs = []
        for path in include_fields:
            for field in schema.fields:
                if field.path.lower() == path.lower():
                    field_defs.append(_field_to_def(field))
                    break
        
        if field_defs:
            template.add_section(Section(
                type=SectionType.DETAIL,
                title="Additional Fields",
                order=len(template.sections),
                detail_config=DetailConfig(fields=field_defs, columns=2),
            ))
        
        return template


# ============================================================================
# Agent Implementation
# ============================================================================

class TemplateDesignAgent:
    """SOTA agent for template design with structured reasoning."""
    
    def __init__(self):
        from schema_introspector import get_available_schemas
        
        self.schemas = get_available_schemas()
        self.design_system = DesignSystem()
        self.tools = AgentTools(self.schemas, self.design_system)
        self.state = ConversationState()
        
        # LLM configuration
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_KEY")
        self.deployment = os.getenv("AZURE_DEPLOYMENT", "claude-sonnet-4-5")
        self.api_version = os.getenv("API_VERSION", "2025-01-01-preview")
    
    def _get_client(self):
        """Get API client."""
        try:
            import anthropic
            return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            pass
        
        try:
            from openai import AzureOpenAI
            return AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )
        except ImportError:
            return None
    
    def process(self, user_message: str) -> Dict[str, Any]:
        """Process a user message and return response with any template changes.
        
        This is the main entry point. The agent will:
        1. Understand the user's intent
        2. Call appropriate tools
        3. Return a response with reasoning
        """
        # Add user message to history
        self.state.messages.append(AgentMessage(role="user", content=user_message))
        
        # Build messages for LLM
        messages = self._build_messages()
        
        # Get LLM response with tool use
        client = self._get_client()
        if not client:
            return self._fallback_response(user_message)
        
        try:
            response = self._call_llm(client, messages)
            return self._process_llm_response(response)
        except Exception as e:
            return {"error": str(e), "message": "Failed to process request"}
    
    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build message list for LLM."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add context about current state
        if self.state.current_template:
            context = f"\n\nCurrent template: {self.state.current_template.get('name', 'Unnamed')}"
            context += f"\nEntity type: {self.state.current_entity_type}"
            context += f"\nArchetype: {self.state.current_archetype.value if self.state.current_archetype else 'Not set'}"
            messages[0]["content"] += context
        
        # Add conversation history
        for msg in self.state.messages[-10:]:  # Last 10 messages
            messages.append({
                "role": msg.role if msg.role != "tool_result" else "user",
                "content": msg.content,
            })
        
        return messages
    
    def _call_llm(self, client, messages) -> Any:
        """Call the LLM with tools."""
        tools = self.tools.get_tool_definitions()
        
        # Handle different client types
        if hasattr(client, 'messages'):  # Anthropic
            return client.messages.create(
                model=self.deployment,
                max_tokens=4096,
                system=messages[0]["content"],
                messages=messages[1:],
                tools=tools,
            )
        else:  # Azure OpenAI
            return client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=[{"type": "function", "function": t} for t in tools],
            )
    
    def _process_llm_response(self, response) -> Dict[str, Any]:
        """Process LLM response, executing any tool calls."""
        result = {
            "message": "",
            "tool_calls": [],
            "template": None,
            "preview": None,
        }
        
        # Handle Anthropic response
        if hasattr(response, 'content'):
            for block in response.content:
                if hasattr(block, 'text'):
                    result["message"] += block.text
                elif hasattr(block, 'type') and block.type == 'tool_use':
                    tool_result = self._execute_tool(block.name, block.input)
                    result["tool_calls"].append({
                        "tool": block.name,
                        "args": block.input,
                        "result": tool_result,
                    })
        
        # Handle OpenAI response
        elif hasattr(response, 'choices'):
            choice = response.choices[0]
            if choice.message.content:
                result["message"] = choice.message.content
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    args = json.loads(tc.function.arguments)
                    tool_result = self._execute_tool(tc.function.name, args)
                    result["tool_calls"].append({
                        "tool": tc.function.name,
                        "args": args,
                        "result": tool_result,
                    })
        
        # Add current template to response
        if self.state.current_template:
            result["template"] = self.state.current_template
        
        # Add assistant message to history
        self.state.messages.append(AgentMessage(
            role="assistant",
            content=result["message"],
            tool_calls=result["tool_calls"],
        ))
        
        return result
    
    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and update state."""
        result, self.state = self.tools.execute(tool_name, args, self.state)
        
        # Add tool result to history
        self.state.messages.append(AgentMessage(
            role="tool_result",
            content=json.dumps(result, default=str),
        ))
        
        return result
    
    def _fallback_response(self, user_message: str) -> Dict[str, Any]:
        """Provide response when LLM is unavailable."""
        user_lower = user_message.lower()
        
        # Simple intent detection
        if any(kw in user_lower for kw in ["create", "make", "generate", "new"]):
            # Try to detect entity type
            for entity_type in self.schemas.keys():
                if entity_type in user_lower:
                    result, self.state = self.tools.execute(
                        "create_template",
                        {"entity_type": entity_type, "archetype": "formal_document"},
                        self.state,
                    )
                    return {
                        "message": f"Created template for {entity_type}",
                        "template": self.state.current_template,
                        "tool_calls": [{"tool": "create_template", "result": result}],
                    }
        
        if "list" in user_lower or "show" in user_lower and "entit" in user_lower:
            result, self.state = self.tools.execute("list_entity_types", {}, self.state)
            return {
                "message": "Available entity types:",
                "tool_calls": [{"tool": "list_entity_types", "result": result}],
            }
        
        return {
            "message": (
                "I can help you create portable view templates. Try:\n"
                "- 'Create a contract template'\n"
                "- 'List available entity types'\n"
                "- 'Show me contract fields'"
            ),
            "suggested_actions": [
                "Create a contract template",
                "Create an RFI template",
                "List entity types",
            ],
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state for persistence."""
        return {
            "current_template": self.state.current_template,
            "current_entity_type": self.state.current_entity_type,
            "current_archetype": self.state.current_archetype.value if self.state.current_archetype else None,
            "message_count": len(self.state.messages),
        }
    
    def reset(self):
        """Reset agent state."""
        self.state = ConversationState()


# ============================================================================
# Direct Tool Interface (for non-LLM usage)
# ============================================================================

def create_agent() -> TemplateDesignAgent:
    """Create a new agent instance."""
    return TemplateDesignAgent()


def quick_create_template(
    entity_type: str,
    archetype: str = "formal_document",
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick template creation without agent conversation."""
    agent = create_agent()
    result, _ = agent.tools.execute(
        "create_template",
        {"entity_type": entity_type, "archetype": archetype, "name": name},
        agent.state,
    )
    return result
