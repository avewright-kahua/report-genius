"""
Template Generator - Unified Entry Point

This module provides a unified API for the template generation system,
combining the SOTA agent with direct composition capabilities.

Usage:
    # Agent-based (conversational)
    from template_gen import TemplateAgent
    agent = TemplateAgent()
    result = agent.chat("Create a contract template for executive review")
    
    # Direct composition
    from template_gen import compose, auto_compose
    template = compose("contract", archetype="financial_report")
    template = auto_compose("rfi", intent="quick status overview")
    
    # Schema introspection
    from template_gen import get_schemas, get_schema
    schemas = get_schemas()
    rfi_schema = get_schema("rfi")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure parent is in path
sys.path.insert(0, str(Path(__file__).parent))

# Import schema tools
from schema_introspector import (
    get_available_schemas,
    get_schema_summary,
    EntitySchema,
    FieldCategory,
    FieldInfo,
)

# Import template models
from template_schema import (
    PortableViewTemplate,
    Section,
    SectionType,
    FieldDef,
    FieldFormat,
    Condition,
    ConditionOperator,
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableConfig,
    TableColumn,
    LayoutConfig,
    StyleConfig,
)

# Import core module
from core import (
    # Design System
    DesignSystem,
    DesignGuidelines,
    TemplateArchetype,
    InformationDensity,
    VisualTone,
    # Agent
    TemplateDesignAgent,
    create_agent,
    quick_create_template,
    # Composer  
    CreativeComposer,
    SectionPurpose,
    compose_template,
    auto_compose_template,
)

# Import renderers
from template_renderer import render_to_markdown, generate_sample_data
from docx_renderer import render_template_to_docx


# ============================================================================
# Convenience API
# ============================================================================

class TemplateAgent:
    """High-level agent interface for template creation.
    
    Example:
        agent = TemplateAgent()
        
        # Create a template
        result = agent.chat("Create a contract template")
        print(result.template)
        print(result.preview)
        
        # Modify it
        result = agent.chat("Remove the financials section")
        
        # Export
        agent.export_docx("my_template.docx")
    """
    
    def __init__(self):
        self._agent = create_agent()
    
    def chat(self, message: str) -> "AgentResult":
        """Send a message to the agent and get a response."""
        result = self._agent.process(message)
        return AgentResult(
            message=result.get("message", ""),
            template=result.get("template"),
            tool_calls=result.get("tool_calls", []),
        )
    
    @property
    def current_template(self) -> Optional[PortableViewTemplate]:
        """Get the current template."""
        data = self._agent.state.current_template
        if data:
            return PortableViewTemplate(**data)
        return None
    
    def preview_markdown(self) -> Optional[str]:
        """Generate markdown preview of current template."""
        template = self.current_template
        if not template:
            return None
        sample = generate_sample_data(template)
        return render_to_markdown(template, sample)
    
    def export_docx(self, path: str) -> str:
        """Export current template to Word document."""
        template = self.current_template
        if not template:
            raise ValueError("No template to export")
        
        entity_prefix = template.entity_def.split(".")[-1] if template.entity_def else None
        doc_bytes = render_template_to_docx(template, entity_prefix=entity_prefix)
        
        Path(path).write_bytes(doc_bytes)
        return path
    
    def export_json(self, path: str) -> str:
        """Export current template to JSON."""
        template = self.current_template
        if not template:
            raise ValueError("No template to export")
        
        Path(path).write_text(template.model_dump_json(indent=2))
        return path
    
    def reset(self):
        """Reset the agent state."""
        self._agent.reset()


class AgentResult:
    """Result from an agent interaction."""
    
    def __init__(
        self,
        message: str,
        template: Optional[Dict[str, Any]] = None,
        tool_calls: List[Dict[str, Any]] = None,
    ):
        self.message = message
        self._template_data = template
        self.tool_calls = tool_calls or []
    
    @property
    def template(self) -> Optional[PortableViewTemplate]:
        """Get the template as a model."""
        if self._template_data:
            return PortableViewTemplate(**self._template_data)
        return None
    
    @property
    def preview(self) -> Optional[str]:
        """Get markdown preview."""
        template = self.template
        if template:
            sample = generate_sample_data(template)
            return render_to_markdown(template, sample)
        return None
    
    def __repr__(self):
        has_template = "✓" if self._template_data else "✗"
        return f"AgentResult(template={has_template}, tools={len(self.tool_calls)})"


def get_schemas() -> Dict[str, EntitySchema]:
    """Get all available entity schemas."""
    return get_available_schemas()


def get_schema(entity_type: str) -> Optional[EntitySchema]:
    """Get a specific entity schema."""
    schemas = get_available_schemas()
    return schemas.get(entity_type.lower())


def list_entity_types() -> List[str]:
    """List available entity type names."""
    return list(get_available_schemas().keys())


def compose(
    entity_type: str,
    archetype: str = "formal_document",
    name: Optional[str] = None,
    **preferences,
) -> PortableViewTemplate:
    """Compose a template directly (no agent).
    
    Args:
        entity_type: Entity type name (contract, rfi, submittal, etc.)
        archetype: Template archetype (formal_document, executive_summary, etc.)
        name: Optional template name
        **preferences: Additional preferences (include_fields, exclude_fields, etc.)
    
    Returns:
        PortableViewTemplate
        
    Example:
        template = compose("contract", archetype="financial_report")
        template = compose("rfi", archetype="correspondence", name="RFI Summary")
    """
    schemas = get_available_schemas()
    
    if entity_type.lower() not in schemas:
        available = ", ".join(schemas.keys())
        raise ValueError(f"Unknown entity type: {entity_type}. Available: {available}")
    
    schema = schemas[entity_type.lower()]
    arch = TemplateArchetype(archetype)
    
    if name:
        preferences["name"] = name
    
    composer = CreativeComposer()
    return composer.compose(schema, arch, preferences)


def auto_compose(entity_type: str, intent: str = "") -> PortableViewTemplate:
    """Auto-compose a template with inferred archetype.
    
    Args:
        entity_type: Entity type name
        intent: Optional description of what you want (e.g., "quick status overview")
    
    Returns:
        PortableViewTemplate with automatically chosen archetype
        
    Example:
        template = auto_compose("contract", intent="executive summary for leadership")
        template = auto_compose("rfi")  # Uses default archetype for RFI
    """
    schemas = get_available_schemas()
    
    if entity_type.lower() not in schemas:
        available = ", ".join(schemas.keys())
        raise ValueError(f"Unknown entity type: {entity_type}. Available: {available}")
    
    schema = schemas[entity_type.lower()]
    return auto_compose_template(schema, intent)


def preview(template: PortableViewTemplate) -> str:
    """Generate markdown preview of a template."""
    sample = generate_sample_data(template)
    return render_to_markdown(template, sample)


def export_docx(template: PortableViewTemplate, path: str) -> str:
    """Export a template to Word document.
    
    Args:
        template: The template to export
        path: Output file path
    
    Returns:
        The output path
    """
    entity_prefix = template.entity_def.split(".")[-1] if template.entity_def else None
    doc_bytes = render_template_to_docx(template, entity_prefix=entity_prefix)
    Path(path).write_bytes(doc_bytes)
    return path


def export_json(template: PortableViewTemplate, path: str) -> str:
    """Export a template to JSON.
    
    Args:
        template: The template to export
        path: Output file path
    
    Returns:
        The output path
    """
    Path(path).write_text(template.model_dump_json(indent=2))
    return path


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # High-level API
    "TemplateAgent",
    "AgentResult",
    "compose",
    "auto_compose",
    "preview",
    "export_docx",
    "export_json",
    "get_schemas",
    "get_schema",
    "list_entity_types",
    # Core classes
    "DesignSystem",
    "TemplateArchetype",
    "CreativeComposer",
    "TemplateDesignAgent",
    # Template models
    "PortableViewTemplate",
    "Section",
    "SectionType",
    "FieldDef",
    "FieldFormat",
    # Schema models
    "EntitySchema",
    "FieldCategory",
    "FieldInfo",
]


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Template Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List entity types")
    
    # Compose command
    compose_parser = subparsers.add_parser("compose", help="Compose a template")
    compose_parser.add_argument("entity", help="Entity type")
    compose_parser.add_argument("-a", "--archetype", default="formal_document", help="Template archetype")
    compose_parser.add_argument("-n", "--name", help="Template name")
    compose_parser.add_argument("-o", "--output", help="Output file (json or docx)")
    compose_parser.add_argument("--preview", action="store_true", help="Show markdown preview")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    
    args = parser.parse_args()
    
    if args.command == "list":
        entities = list_entity_types()
        print("Available entity types:")
        for e in entities:
            print(f"  - {e}")
    
    elif args.command == "compose":
        template = compose(args.entity, archetype=args.archetype, name=args.name)
        
        if args.preview:
            print(preview(template))
            print()
        
        if args.output:
            if args.output.endswith(".docx"):
                export_docx(template, args.output)
                print(f"Exported to: {args.output}")
            else:
                export_json(template, args.output)
                print(f"Exported to: {args.output}")
        else:
            print(f"Template: {template.name}")
            print(f"Sections: {len(template.sections)}")
            for s in template.get_sections_ordered():
                print(f"  - {s.type.value}: {s.title or '(untitled)'}")
    
    elif args.command == "chat":
        agent = TemplateAgent()
        print("Template Generator Chat (type 'exit' to quit)")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ("exit", "quit", "q"):
                    break
                
                result = agent.chat(user_input)
                print(f"\nAssistant: {result.message}")
                
                if result.template:
                    print(f"\n[Template: {result.template.name}, {len(result.template.sections)} sections]")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nGoodbye!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
