"""
LangGraph-based Template Agent - Stateful agent for portable view template creation.

Uses LangGraph for state management and tool orchestration, enabling natural
language template creation with multi-step reasoning.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from schema_introspector import (
    EntitySchema,
    FieldCategory,
    FieldInfo,
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
    FormatOptions,
    HeaderConfig,
    PortableViewTemplate,
    Section,
    SectionType,
    TableColumn,
    TableConfig,
    TextConfig,
)

load_dotenv()


# ============================================================================
# Agent State
# ============================================================================

class AgentState(TypedDict):
    """State maintained across the conversation."""
    messages: Annotated[List[BaseMessage], add_messages]
    current_template: Optional[Dict[str, Any]]
    available_schemas: Dict[str, Dict[str, Any]]
    last_preview: Optional[str]


# ============================================================================
# Tools
# ============================================================================

# Global schema cache
_schemas: Dict[str, EntitySchema] = {}


def _get_schemas() -> Dict[str, EntitySchema]:
    """Get or initialize schema cache."""
    global _schemas
    if not _schemas:
        _schemas = get_available_schemas()
    return _schemas


@tool
def list_available_entities() -> str:
    """List all available entity types that can be used for templates.
    
    Returns a summary of each entity type and its field categories.
    """
    schemas = _get_schemas()
    
    result = []
    for name, schema in schemas.items():
        summary = get_schema_summary(schema)
        result.append({
            "name": name,
            "entity_def": schema.entity_def,
            "total_fields": sum(summary["field_counts"].values()),
            "categories": summary["field_counts"],
        })
    
    return json.dumps(result, indent=2)


@tool
def get_entity_fields(entity_type: str, category: Optional[str] = None) -> str:
    """Get detailed field information for an entity type.
    
    Args:
        entity_type: The entity type (contract, rfi, submittal)
        category: Optional filter by category (identity, financial, contact, text_block, collection, date, status, lookup)
    
    Returns field details including path, label, and format hints.
    """
    schemas = _get_schemas()
    
    if entity_type not in schemas:
        return f"Unknown entity type: {entity_type}. Available: {list(schemas.keys())}"
    
    schema = schemas[entity_type]
    summary = get_schema_summary(schema)
    
    if category:
        if category not in summary["fields_by_category"]:
            return f"No fields in category '{category}'. Available categories: {list(summary['fields_by_category'].keys())}"
        return json.dumps({category: summary["fields_by_category"][category]}, indent=2)
    
    return json.dumps(summary["fields_by_category"], indent=2)


@tool
def create_new_template(
    entity_type: str,
    name: Optional[str] = None,
    style: Literal["full", "minimal"] = "full",
) -> str:
    """Create a new template for an entity type.
    
    Args:
        entity_type: The entity type (contract, rfi, submittal)
        name: Optional custom name for the template
        style: 'full' includes all sections, 'minimal' is just header and key fields
    
    Returns the template JSON and a markdown preview.
    """
    schemas = _get_schemas()
    
    if entity_type not in schemas:
        return f"Unknown entity type: {entity_type}. Available: {list(schemas.keys())}"
    
    schema = schemas[entity_type]
    
    if style == "minimal":
        template = generate_minimal_template(schema)
    else:
        template = generate_template(schema, name=name)
    
    if name:
        template.name = name
    
    # Generate preview
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return json.dumps({
        "template": template.model_dump(),
        "preview": preview,
        "sections": [
            {"index": i, "type": s.type.value, "title": s.title}
            for i, s in enumerate(template.get_sections_ordered())
        ]
    }, indent=2, default=str)


@tool
def add_fields_to_template(
    template_json: str,
    field_paths: List[str],
    section_title: Optional[str] = None,
) -> str:
    """Add fields to the current template.
    
    Args:
        template_json: The current template as JSON string
        field_paths: List of field paths to add (e.g., ["ScopeOfWork", "ContractorCompany.ShortLabel"])
        section_title: Optional title for a new section containing these fields
    
    Returns the updated template JSON and preview.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    # Find schema for this template
    schemas = _get_schemas()
    schema = None
    for s in schemas.values():
        if s.entity_def == template.entity_def:
            schema = s
            break
    
    if not schema:
        return "Could not find schema for template"
    
    # Find matching fields
    matched_fields = []
    for path in field_paths:
        for field in schema.fields:
            if field.path.lower() == path.lower() or field.name.lower() == path.lower():
                matched_fields.append(field)
                break
    
    if not matched_fields:
        return f"No matching fields found. Available fields: {[f.path for f in schema.fields[:20]]}"
    
    # Create field definitions
    from template_generator import _field_to_def
    field_defs = [_field_to_def(f) for f in matched_fields]
    
    # Group text blocks separately
    text_fields = [f for f in matched_fields if f.category == FieldCategory.TEXT_BLOCK]
    other_fields = [f for f in matched_fields if f.category != FieldCategory.TEXT_BLOCK]
    
    # Add text blocks as separate sections
    for field in text_fields:
        section = Section(
            type=SectionType.TEXT,
            title=field.label,
            order=len(template.sections),
            condition=Condition(field=field.path, op=ConditionOperator.NOT_EMPTY),
            text_config=TextConfig(content=f"{{{field.path}}}"),
        )
        template.add_section(section)
    
    # Add other fields as detail section
    if other_fields:
        section = Section(
            type=SectionType.DETAIL,
            title=section_title,
            order=len(template.sections),
            detail_config=DetailConfig(
                fields=[_field_to_def(f) for f in other_fields],
                columns=2 if len(other_fields) > 2 else 1,
            ),
        )
        template.add_section(section)
    
    # Generate preview
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return json.dumps({
        "template": template.model_dump(),
        "preview": preview,
        "added_fields": [f.path for f in matched_fields],
    }, indent=2, default=str)


@tool
def remove_section_from_template(
    template_json: str,
    section_index: Optional[int] = None,
    section_title: Optional[str] = None,
    section_type: Optional[str] = None,
) -> str:
    """Remove a section from the template.
    
    Args:
        template_json: The current template as JSON string
        section_index: Index of section to remove (from sections list)
        section_title: Remove section(s) matching this title
        section_type: Remove section(s) matching this type (header, detail, text, table, divider)
    
    Returns the updated template JSON and preview.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    removed = []
    
    if section_index is not None:
        if 0 <= section_index < len(template.sections):
            removed.append(template.sections[section_index].title or template.sections[section_index].type.value)
            template.sections.pop(section_index)
    elif section_title:
        original_len = len(template.sections)
        template.sections = [
            s for s in template.sections
            if not s.title or section_title.lower() not in s.title.lower()
        ]
        removed = [f"Sections matching '{section_title}'"] if len(template.sections) < original_len else []
    elif section_type:
        original_len = len(template.sections)
        template.sections = [
            s for s in template.sections
            if section_type.lower() not in s.type.value.lower()
        ]
        removed = [f"Sections of type '{section_type}'"] if len(template.sections) < original_len else []
    
    if not removed:
        return json.dumps({
            "error": "No sections removed",
            "available_sections": [
                {"index": i, "type": s.type.value, "title": s.title}
                for i, s in enumerate(template.sections)
            ]
        }, indent=2)
    
    # Reorder
    for i, s in enumerate(template.sections):
        s.order = i
    
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return json.dumps({
        "template": template.model_dump(),
        "preview": preview,
        "removed": removed,
    }, indent=2, default=str)


@tool
def reorder_template_sections(
    template_json: str,
    section_index: int,
    new_position: int,
) -> str:
    """Move a section to a new position in the template.
    
    Args:
        template_json: The current template as JSON string
        section_index: Current index of the section to move
        new_position: New index position (0 = top)
    
    Returns the updated template JSON and preview.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    if section_index < 0 or section_index >= len(template.sections):
        return f"Invalid section_index. Valid range: 0-{len(template.sections)-1}"
    
    section = template.sections.pop(section_index)
    new_position = max(0, min(new_position, len(template.sections)))
    template.sections.insert(new_position, section)
    
    # Update order numbers
    for i, s in enumerate(template.sections):
        s.order = i
    
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return json.dumps({
        "template": template.model_dump(),
        "preview": preview,
        "moved": f"'{section.title or section.type.value}' to position {new_position}",
        "sections": [
            {"index": i, "type": s.type.value, "title": s.title}
            for i, s in enumerate(template.sections)
        ]
    }, indent=2, default=str)


@tool
def modify_section_style(
    template_json: str,
    section_index: int,
    new_title: Optional[str] = None,
    columns: Optional[int] = None,
) -> str:
    """Modify a section's properties.
    
    Args:
        template_json: The current template as JSON string
        section_index: Index of the section to modify
        new_title: New title for the section
        columns: Number of columns for detail sections (1-4)
    
    Returns the updated template JSON and preview.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    if section_index < 0 or section_index >= len(template.sections):
        return f"Invalid section_index. Valid range: 0-{len(template.sections)-1}"
    
    section = template.sections[section_index]
    
    if new_title is not None:
        section.title = new_title if new_title else None
    
    if columns is not None and section.detail_config:
        section.detail_config.columns = max(1, min(4, columns))
    
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return json.dumps({
        "template": template.model_dump(),
        "preview": preview,
    }, indent=2, default=str)


@tool
def preview_template(template_json: str) -> str:
    """Generate a markdown preview of the template with sample data.
    
    Args:
        template_json: The template as JSON string
    
    Returns markdown preview.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return preview


# Base directory for template storage
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATES_DIR = BASE_DIR / "pv_templates" / "saved"


@tool
def save_template(
    template_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save the template to disk.
    
    Args:
        template_json: The template as JSON string
        filename: Optional custom filename (without extension)
    
    Returns the path where the template was saved.
    """
    try:
        template_data = json.loads(template_json)
        template = PortableViewTemplate(**template_data)
    except Exception as e:
        return f"Error parsing template: {e}"
    
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    if filename:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in filename)
        output_path = TEMPLATES_DIR / f"{safe_name}.json"
    else:
        output_path = TEMPLATES_DIR / f"{template.id}.json"
    
    with open(output_path, "w") as f:
        json.dump(template.model_dump(), f, indent=2, default=str)
    
    return f"Saved template to: {output_path}"


# ============================================================================
# Tool list
# ============================================================================

TOOLS = [
    list_available_entities,
    get_entity_fields,
    create_new_template,
    add_fields_to_template,
    remove_section_from_template,
    reorder_template_sections,
    modify_section_style,
    preview_template,
    save_template,
]


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a template design assistant helping users create portable view templates for Kahua construction management data.

Your role is to help users create professional, well-organized report templates by:
1. Understanding what kind of report they need
2. Selecting appropriate fields from the entity schema
3. Organizing content into logical sections
4. Making refinements based on feedback

WORKFLOW:
1. When a user wants to create a template, first use create_new_template with the appropriate entity type
2. The template JSON will be in the tool response - always pass this to subsequent tools
3. After modifications, show the user what changed and offer suggestions

AVAILABLE ENTITY TYPES:
- contract: Expense contracts with financials, line items, contractor info
- rfi: Requests for Information with questions, responses, workflow
- submittal: Submittal items with review process

TEMPLATE STRUCTURE:
Templates have sections in order: header → summary details → divider → financials → text blocks → tables → footer
Each section has a type: header, detail (key-value grid), text (long content), table (collections), divider

IMPORTANT:
- Always maintain the current template state in tool calls
- After each modification, briefly describe what changed
- Suggest logical next steps
- Keep responses concise but helpful
- When the user is happy, remind them to save the template

Do not make up field names - use get_entity_fields to see what's available."""


# ============================================================================
# Graph Construction
# ============================================================================

def create_agent():
    """Create the LangGraph agent."""
    
    # Azure AI Foundry uses a specific endpoint format for Anthropic models
    # The endpoint format is: {endpoint}/models/{deployment}
    from langchain_core.language_models import BaseChatModel
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.callbacks import CallbackManagerForLLMRun
    import httpx
    
    class AzureAnthropicChat(BaseChatModel):
        """Custom chat model for Azure AI Foundry hosted Anthropic models."""
        
        endpoint: str
        api_key: str
        deployment: str
        api_version: str = "2025-01-01-preview"
        max_tokens: int = 4096
        
        @property
        def _llm_type(self) -> str:
            return "azure-anthropic"
        
        def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs,
        ) -> ChatResult:
            # Convert messages to API format - system message goes in messages array for OpenAI API
            api_messages = []
            
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    api_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    api_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        # Include tool calls in assistant message
                        api_messages.append({
                            "role": "assistant",
                            "content": msg.content or None,
                            "tool_calls": [
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(tc["args"]),
                                    }
                                }
                                for tc in msg.tool_calls
                            ]
                        })
                    else:
                        api_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, ToolMessage):
                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    })
            
            # Build request payload
            payload = {
                "messages": api_messages,
                "max_tokens": self.max_tokens,
            }
            
            if stop:
                payload["stop"] = stop
            
            # Add tools if bound
            if hasattr(self, "_tools") and self._tools:
                payload["tools"] = self._tools
            
            # Make API request - Azure AI uses OpenAI-compatible endpoint format
            url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": self.api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse response
            choice = data["choices"][0]
            message = choice["message"]
            
            # Extract tool calls if present
            tool_calls = []
            if "tool_calls" in message and message["tool_calls"]:
                for tc in message["tool_calls"]:
                    tool_calls.append({
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "args": json.loads(tc["function"]["arguments"]),
                    })
            
            ai_message = AIMessage(
                content=message.get("content") or "",
                tool_calls=tool_calls,
            )
            
            return ChatResult(generations=[ChatGeneration(message=ai_message)])
        
        def bind_tools(self, tools: List):
            """Bind tools to the model."""
            from langchain_core.utils.function_calling import convert_to_openai_function
            
            # Create a copy with tools
            bound = AzureAnthropicChat(
                endpoint=self.endpoint,
                api_key=self.api_key,
                deployment=self.deployment,
                api_version=self.api_version,
                max_tokens=self.max_tokens,
            )
            bound._tools = [
                {"type": "function", "function": convert_to_openai_function(t)}
                for t in tools
            ]
            return bound
    
    llm = AzureAnthropicChat(
        endpoint=os.getenv("AZURE_ENDPOINT"),
        api_key=os.getenv("AZURE_KEY"),
        deployment="gpt-4o",  # Using gpt-4o until Claude is deployed
        api_version=os.getenv("API_VERSION", "2025-01-01-preview"),
        max_tokens=4096,
    )
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(TOOLS)
    
    # Create tool node
    tool_node = ToolNode(TOOLS)
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine whether to call tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "end"
    
    def call_model(state: AgentState) -> Dict[str, Any]:
        """Call the LLM."""
        messages = state["messages"]
        
        # Add system message if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


# ============================================================================
# CLI Interface
# ============================================================================

def run_interactive():
    """Run the agent interactively."""
    print("\n" + "="*60)
    print("Portable View Template Generator (LangGraph Agent)")
    print("="*60)
    print("\nExamples:")
    print("  - Create a contract report")
    print("  - Show me the available fields for RFI")
    print("  - Remove the custom text sections")
    print("  - Move financials above the scope section")
    print("  - Save the template as 'Contract Summary'")
    print("\nType 'quit' to exit")
    print("-"*60)
    
    agent = create_agent()
    state: AgentState = {
        "messages": [],
        "current_template": None,
        "available_schemas": {},
        "last_preview": None,
    }
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        # Add user message
        state["messages"].append(HumanMessage(content=user_input))
        
        try:
            # Run agent
            result = agent.invoke(state)
            state = result
            
            # Get last AI message
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    print(f"\nAssistant: {msg.content}")
                    break
        
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


def run_single_request(request: str) -> str:
    """Run a single request and return the response."""
    agent = create_agent()
    
    state: AgentState = {
        "messages": [HumanMessage(content=request)],
        "current_template": None,
        "available_schemas": {},
        "last_preview": None,
    }
    
    result = agent.invoke(state)
    
    # Get last AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Single request mode
        request = " ".join(sys.argv[1:])
        print(run_single_request(request))
    else:
        # Interactive mode
        run_interactive()
