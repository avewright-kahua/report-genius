"""
Template Agent - Claude-powered natural language interface for template creation.

This module provides the AI layer that translates user intent into template
operations: creation, modification, field selection, and refinement.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from dotenv import load_dotenv

from schema_introspector import (
    EntitySchema,
    FieldCategory,
    get_available_schemas,
    get_schema_summary,
)
from template_generator import generate_template, generate_minimal_template
from template_renderer import generate_sample_data, render_to_markdown
from template_schema import (
    Alignment,
    Condition,
    ConditionOperator,
    DetailConfig,
    FieldDef,
    FieldFormat,
    PortableViewTemplate,
    Section,
    SectionType,
    TableColumn,
    TableConfig,
)

load_dotenv()


@dataclass
class AgentResponse:
    """Response from the template agent."""
    
    message: str
    template: Optional[PortableViewTemplate] = None
    preview_markdown: Optional[str] = None
    suggested_actions: List[str] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class TemplateAgent:
    """Agent for natural language template creation and modification."""
    
    def __init__(self):
        self.schemas = get_available_schemas()
        self.current_template: Optional[PortableViewTemplate] = None
        self.conversation_history: List[Dict[str, str]] = []
        
        # Azure/Anthropic config
        self.endpoint = os.getenv("AZURE_ENDPOINT")
        self.api_key = os.getenv("AZURE_KEY")
        self.api_version = os.getenv("API_VERSION", "2025-01-01-preview")
        self.deployment = os.getenv("AZURE_DEPLOYMENT", "claude-sonnet-4-5")
        self.provider = os.getenv("MODEL_PROVIDER", "anthropic")
    
    def _get_client(self):
        """Get the appropriate API client."""
        if self.provider == "anthropic":
            try:
                import anthropic
                # For Azure-hosted Anthropic models
                return anthropic.Anthropic(
                    base_url=f"{self.endpoint}/openai/deployments/{self.deployment}",
                    api_key=self.api_key,
                )
            except ImportError:
                pass
        
        # Fallback to OpenAI-compatible client for Azure
        try:
            from openai import AzureOpenAI
            return AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
            )
        except ImportError:
            return None
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with available schemas."""
        schema_info = []
        for name, schema in self.schemas.items():
            summary = get_schema_summary(schema)
            schema_info.append(f"**{name}** ({schema.entity_def}):")
            schema_info.append(f"  Fields by category: {summary['field_counts']}")
        
        return f"""You are a template design assistant helping users create portable view templates for Kahua entity data.

Available entity types:
{chr(10).join(schema_info)}

You help users by:
1. Understanding what kind of report they want
2. Selecting appropriate fields from the entity schema
3. Organizing content into logical sections
4. Making refinements based on feedback

When responding to template requests:
- Identify the entity type (contract, rfi, submittal)
- Suggest a sensible default structure
- Ask clarifying questions if the request is ambiguous
- Explain what fields will be included and why

When responding to modification requests:
- Make targeted changes without disrupting the overall structure
- Confirm what was changed
- Suggest related improvements

Output format for template operations:
- Use JSON code blocks for template modifications
- Provide clear explanations of changes
- Show before/after for significant modifications

Current template: {self.current_template.name if self.current_template else 'None'}
"""
    
    def process_request(self, user_input: str) -> AgentResponse:
        """Process a user request and return an appropriate response.
        
        This is the main entry point that handles all user interactions.
        """
        user_lower = user_input.lower()
        
        # Detect intent
        if any(kw in user_lower for kw in ["create", "make", "generate", "new", "start"]):
            return self._handle_create_request(user_input)
        
        if any(kw in user_lower for kw in ["show", "list", "what", "available"]):
            if "field" in user_lower or "schema" in user_lower:
                return self._handle_schema_query(user_input)
            if "template" in user_lower:
                return self._handle_list_templates()
        
        if any(kw in user_lower for kw in ["add", "include", "insert"]):
            return self._handle_add_request(user_input)
        
        if any(kw in user_lower for kw in ["remove", "delete", "hide", "exclude"]):
            return self._handle_remove_request(user_input)
        
        if any(kw in user_lower for kw in ["move", "reorder", "swap"]):
            return self._handle_reorder_request(user_input)
        
        if any(kw in user_lower for kw in ["change", "modify", "update", "rename", "edit"]):
            return self._handle_modify_request(user_input)
        
        if any(kw in user_lower for kw in ["save", "export"]):
            return self._handle_save_request(user_input)
        
        if any(kw in user_lower for kw in ["load", "open", "use"]):
            return self._handle_load_request(user_input)
        
        if any(kw in user_lower for kw in ["preview", "render", "show"]):
            return self._handle_preview_request()
        
        # Default: try to interpret as a refinement
        if self.current_template:
            return self._handle_modify_request(user_input)
        
        return AgentResponse(
            message="I can help you create and modify portable view templates. Try:\n"
                    "- 'Create a contract report'\n"
                    "- 'Show available fields for RFI'\n"
                    "- 'Add the scope of work section'\n"
                    "- 'Move financials above the table'",
            suggested_actions=[
                "Create a contract report",
                "Create an RFI summary",
                "Show available schemas",
            ]
        )
    
    def _handle_create_request(self, user_input: str) -> AgentResponse:
        """Handle template creation requests."""
        # Detect entity type
        entity_type = None
        for name in self.schemas.keys():
            if name in user_input.lower():
                entity_type = name
                break
        
        if not entity_type:
            # Try to infer from keywords
            if any(kw in user_input.lower() for kw in ["contract", "expense", "cost"]):
                entity_type = "contract"
            elif any(kw in user_input.lower() for kw in ["rfi", "request for information", "question"]):
                entity_type = "rfi"
            elif any(kw in user_input.lower() for kw in ["submittal", "submission"]):
                entity_type = "submittal"
        
        if not entity_type:
            return AgentResponse(
                message="What type of entity would you like to create a template for?\n\n"
                        "Available types:\n"
                        "- **contract** - Expense contracts with line items, financials\n"
                        "- **rfi** - Requests for Information\n"
                        "- **submittal** - Submittal items with review workflow",
                suggested_actions=[
                    "Create a contract report",
                    "Create an RFI summary",
                    "Create a submittal tracker",
                ]
            )
        
        schema = self.schemas[entity_type]
        
        # Check for specific style requests
        minimal = any(kw in user_input.lower() for kw in ["minimal", "simple", "brief", "summary"])
        
        if minimal:
            self.current_template = generate_minimal_template(schema)
        else:
            self.current_template = generate_template(schema)
        
        # Generate preview
        sample = generate_sample_data(self.current_template)
        preview = render_to_markdown(self.current_template, sample)
        
        sections_desc = [
            f"- {s.type.value}: {s.title or '(untitled)'}"
            for s in self.current_template.get_sections_ordered()
        ]
        
        return AgentResponse(
            message=f"Created **{self.current_template.name}** with {len(self.current_template.sections)} sections:\n\n"
                    + "\n".join(sections_desc) + "\n\n"
                    "You can now refine this template:\n"
                    "- 'Add the liquidated damages fields'\n"
                    "- 'Remove the table section'\n"
                    "- 'Move financials to the top'",
            template=self.current_template,
            preview_markdown=preview,
            suggested_actions=[
                "Show preview",
                "Add more fields",
                "Save template",
            ]
        )
    
    def _handle_schema_query(self, user_input: str) -> AgentResponse:
        """Handle requests to view schema/field information."""
        # Find which entity
        entity_type = None
        for name in self.schemas.keys():
            if name in user_input.lower():
                entity_type = name
                break
        
        if not entity_type and self.current_template:
            # Use current template's entity
            for name, schema in self.schemas.items():
                if schema.entity_def == self.current_template.entity_def:
                    entity_type = name
                    break
        
        if not entity_type:
            # Show all schemas
            lines = ["**Available Entity Schemas:**\n"]
            for name, schema in self.schemas.items():
                summary = get_schema_summary(schema)
                lines.append(f"### {name} ({schema.entity_def})")
                lines.append(f"Total fields: {sum(summary['field_counts'].values())}")
                for cat, count in summary['field_counts'].items():
                    lines.append(f"  - {cat}: {count}")
                lines.append("")
            
            return AgentResponse(
                message="\n".join(lines),
                suggested_actions=[
                    "Show contract fields",
                    "Show RFI fields",
                    "Create a contract report",
                ]
            )
        
        schema = self.schemas[entity_type]
        summary = get_schema_summary(schema)
        
        lines = [f"**{schema.name} Fields:**\n"]
        
        for category, fields in summary["fields_by_category"].items():
            lines.append(f"### {category.replace('_', ' ').title()}")
            for f in fields:
                format_str = f" ({f['format']})" if f['format'] else ""
                lines.append(f"- `{f['path']}` - {f['label']}{format_str}")
            lines.append("")
        
        return AgentResponse(
            message="\n".join(lines),
            suggested_actions=[
                f"Create a {entity_type} report",
                "Add specific fields",
            ]
        )
    
    def _handle_add_request(self, user_input: str) -> AgentResponse:
        """Handle requests to add fields or sections."""
        if not self.current_template:
            return AgentResponse(
                message="No template is currently loaded. Create one first.",
                suggested_actions=["Create a contract report", "Load a template"]
            )
        
        # Parse what to add
        user_lower = user_input.lower()
        
        # Find matching fields in schema
        schema = None
        for s in self.schemas.values():
            if s.entity_def == self.current_template.entity_def:
                schema = s
                break
        
        if not schema:
            return AgentResponse(message="Could not find schema for current template.")
        
        # Look for field name patterns
        added_fields = []
        for field in schema.fields:
            # Check if field name or label mentioned
            if field.name.lower() in user_lower or field.label.lower() in user_lower:
                added_fields.append(field)
        
        if not added_fields:
            # Show available fields
            return AgentResponse(
                message="I couldn't identify which fields to add. Here are some options:\n\n"
                        + ", ".join(f.label for f in schema.fields[:20]),
                suggested_actions=[
                    "Add the scope of work",
                    "Add contractor company",
                    "Add all dates",
                ]
            )
        
        # Add fields to appropriate section or create new one
        from template_generator import _field_to_def
        
        # Group by category
        from collections import defaultdict
        by_category = defaultdict(list)
        for f in added_fields:
            by_category[f.category].append(f)
        
        for category, fields in by_category.items():
            if category == FieldCategory.TEXT_BLOCK:
                # Create text sections
                for field in fields:
                    section = Section(
                        type=SectionType.TEXT,
                        title=field.label,
                        order=len(self.current_template.sections),
                        condition=Condition(field=field.path, op=ConditionOperator.NOT_EMPTY),
                        text_config={"content": f"{{{field.path}}}"},
                    )
                    self.current_template.add_section(section)
            else:
                # Add to detail section
                field_defs = [_field_to_def(f) for f in fields]
                section = Section(
                    type=SectionType.DETAIL,
                    title=f"Additional {category.value.replace('_', ' ').title()}",
                    order=len(self.current_template.sections),
                    detail_config=DetailConfig(
                        fields=field_defs,
                        columns=2,
                    ),
                )
                self.current_template.add_section(section)
        
        # Generate updated preview
        sample = generate_sample_data(self.current_template)
        preview = render_to_markdown(self.current_template, sample)
        
        return AgentResponse(
            message=f"Added {len(added_fields)} field(s): {', '.join(f.label for f in added_fields)}",
            template=self.current_template,
            preview_markdown=preview,
            suggested_actions=["Show preview", "Add more fields", "Save template"]
        )
    
    def _handle_remove_request(self, user_input: str) -> AgentResponse:
        """Handle requests to remove fields or sections."""
        if not self.current_template:
            return AgentResponse(
                message="No template is currently loaded.",
                suggested_actions=["Create a contract report", "Load a template"]
            )
        
        user_lower = user_input.lower()
        removed = []
        
        # Check for section type removals
        for section_type in ["table", "financials", "header", "text", "divider"]:
            if section_type in user_lower:
                self.current_template.sections = [
                    s for s in self.current_template.sections
                    if section_type not in s.type.value.lower()
                    and (not s.title or section_type not in s.title.lower())
                ]
                removed.append(section_type)
        
        # Check for specific section title removals
        for section in list(self.current_template.sections):
            if section.title and section.title.lower() in user_lower:
                self.current_template.sections.remove(section)
                removed.append(section.title)
        
        if not removed:
            sections_list = [
                f"- {s.type.value}: {s.title or '(untitled)'}"
                for s in self.current_template.get_sections_ordered()
            ]
            return AgentResponse(
                message="Which section would you like to remove?\n\n" + "\n".join(sections_list),
                suggested_actions=["Remove the table", "Remove financials"]
            )
        
        sample = generate_sample_data(self.current_template)
        preview = render_to_markdown(self.current_template, sample)
        
        return AgentResponse(
            message=f"Removed: {', '.join(removed)}",
            template=self.current_template,
            preview_markdown=preview,
            suggested_actions=["Show preview", "Save template"]
        )
    
    def _handle_reorder_request(self, user_input: str) -> AgentResponse:
        """Handle requests to reorder sections."""
        if not self.current_template:
            return AgentResponse(
                message="No template is currently loaded.",
                suggested_actions=["Create a contract report"]
            )
        
        # Simple reordering logic - find section mentioned and move it
        user_lower = user_input.lower()
        
        target_idx = None
        dest_position = None
        
        for i, section in enumerate(self.current_template.sections):
            title = (section.title or section.type.value).lower()
            if title in user_lower:
                target_idx = i
                break
        
        if target_idx is None:
            return AgentResponse(
                message="Which section would you like to move?",
                suggested_actions=["Move financials to the top"]
            )
        
        # Determine destination
        if "top" in user_lower or "first" in user_lower or "beginning" in user_lower:
            dest_position = 0
        elif "bottom" in user_lower or "last" in user_lower or "end" in user_lower:
            dest_position = len(self.current_template.sections) - 1
        elif "above" in user_lower or "before" in user_lower:
            # Find reference section
            for i, section in enumerate(self.current_template.sections):
                title = (section.title or section.type.value).lower()
                if title in user_lower and i != target_idx:
                    dest_position = i
                    break
        elif "below" in user_lower or "after" in user_lower:
            for i, section in enumerate(self.current_template.sections):
                title = (section.title or section.type.value).lower()
                if title in user_lower and i != target_idx:
                    dest_position = i + 1
                    break
        
        if dest_position is None:
            return AgentResponse(
                message="Where should I move it? (top, bottom, above X, below X)",
                suggested_actions=["Move it to the top", "Move it below the header"]
            )
        
        # Perform the move
        section = self.current_template.sections.pop(target_idx)
        if dest_position > target_idx:
            dest_position -= 1
        self.current_template.sections.insert(dest_position, section)
        
        # Update order numbers
        for i, s in enumerate(self.current_template.sections):
            s.order = i
        
        sample = generate_sample_data(self.current_template)
        preview = render_to_markdown(self.current_template, sample)
        
        return AgentResponse(
            message=f"Moved '{section.title or section.type.value}' to position {dest_position + 1}",
            template=self.current_template,
            preview_markdown=preview,
            suggested_actions=["Show preview", "Save template"]
        )
    
    def _handle_modify_request(self, user_input: str) -> AgentResponse:
        """Handle general modification requests."""
        if not self.current_template:
            return AgentResponse(
                message="No template is currently loaded.",
                suggested_actions=["Create a contract report"]
            )
        
        # This is where we'd use Claude for more complex modifications
        # For now, provide guidance
        
        return AgentResponse(
            message="I can help you modify the template. Try being more specific:\n"
                    "- 'Add the liquidated damages fields'\n"
                    "- 'Remove the items table'\n"
                    "- 'Move financials above scope'\n"
                    "- 'Change the title to include the date'",
            suggested_actions=[
                "Add more fields",
                "Remove a section",
                "Reorder sections",
            ]
        )
    
    def _handle_preview_request(self) -> AgentResponse:
        """Generate and return a preview of the current template."""
        if not self.current_template:
            return AgentResponse(
                message="No template is currently loaded.",
                suggested_actions=["Create a contract report"]
            )
        
        sample = generate_sample_data(self.current_template)
        preview = render_to_markdown(self.current_template, sample)
        
        return AgentResponse(
            message="Here's a preview with sample data:",
            template=self.current_template,
            preview_markdown=preview,
            suggested_actions=["Save template", "Make changes"]
        )
    
    def _handle_save_request(self, user_input: str) -> AgentResponse:
        """Save the current template to disk."""
        if not self.current_template:
            return AgentResponse(
                message="No template to save.",
                suggested_actions=["Create a contract report"]
            )
        
        # Extract custom name if provided
        name_match = re.search(r'(?:as|called|named)\s+["\']?([^"\']+)["\']?', user_input, re.IGNORECASE)
        if name_match:
            self.current_template.name = name_match.group(1).strip()
        
        # Save to file
        output_path = Path("pv_templates/saved") / f"{self.current_template.id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(self.current_template.model_dump(), f, indent=2, default=str)
        
        return AgentResponse(
            message=f"Saved template as **{self.current_template.name}**\n\nFile: `{output_path}`",
            template=self.current_template,
            suggested_actions=["Create another template", "Load a template"]
        )
    
    def _handle_load_request(self, user_input: str) -> AgentResponse:
        """Load a template from disk."""
        saved_dir = Path("pv_templates/saved")
        
        if not saved_dir.exists():
            return AgentResponse(
                message="No saved templates found.",
                suggested_actions=["Create a contract report"]
            )
        
        templates = list(saved_dir.glob("*.json"))
        
        if not templates:
            return AgentResponse(
                message="No saved templates found.",
                suggested_actions=["Create a contract report"]
            )
        
        # Check if specific template mentioned
        user_lower = user_input.lower()
        
        for template_path in templates:
            if template_path.stem.lower() in user_lower:
                with open(template_path) as f:
                    data = json.load(f)
                self.current_template = PortableViewTemplate(**data)
                
                sample = generate_sample_data(self.current_template)
                preview = render_to_markdown(self.current_template, sample)
                
                return AgentResponse(
                    message=f"Loaded **{self.current_template.name}**",
                    template=self.current_template,
                    preview_markdown=preview,
                    suggested_actions=["Show preview", "Make changes", "Save template"]
                )
        
        # List available templates
        template_list = []
        for template_path in templates:
            try:
                with open(template_path) as f:
                    data = json.load(f)
                name = data.get("name", template_path.stem)
                template_list.append(f"- `{template_path.stem}` - {name}")
            except json.JSONDecodeError:
                continue
        
        return AgentResponse(
            message="**Available templates:**\n\n" + "\n".join(template_list) + "\n\nSay 'load <name>' to use one.",
            suggested_actions=[f"Load {templates[0].stem}" if templates else "Create a template"]
        )
    
    def _handle_list_templates(self) -> AgentResponse:
        """List all saved templates."""
        return self._handle_load_request("list")


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Interactive CLI for the template agent."""
    agent = TemplateAgent()
    
    print("\n" + "="*60)
    print("Portable View Template Generator")
    print("="*60)
    print("\nCommands:")
    print("  create <entity> report  - Create a new template")
    print("  show fields for <entity> - View available fields")
    print("  add <field>             - Add fields to current template")
    print("  remove <section>        - Remove a section")
    print("  move <section> to <pos> - Reorder sections")
    print("  preview                 - Show current template preview")
    print("  save                    - Save current template")
    print("  load <name>             - Load a saved template")
    print("  quit                    - Exit")
    print("\n" + "-"*60)
    
    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        response = agent.process_request(user_input)
        
        print("\n" + response.message)
        
        if response.preview_markdown:
            print("\n" + "-"*40 + " PREVIEW " + "-"*40)
            print(response.preview_markdown)
            print("-"*89)
        
        if response.suggested_actions:
            print("\nSuggested: " + " | ".join(response.suggested_actions))


if __name__ == "__main__":
    main()
