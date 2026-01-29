"""
LangGraph-based Kahua Construction Analyst Agent

Uses Claude via Azure with LangChain/LangGraph for native Anthropic support.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Annotated, TypedDict
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load environment before imports that need it
load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Report generation
from report_generator import create_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("langgraph_agent")

# ============== Configuration ==============

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.environ.get("AZURE_KEY", "")
MODEL_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "claude-sonnet-4-5")

# Kahua API
QUERY_URL_TEMPLATE = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"
KAHUA_BASIC_AUTH = os.getenv("KAHUA_BASIC_AUTH")

def _auth_header_value() -> str:
    if not KAHUA_BASIC_AUTH:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return KAHUA_BASIC_AUTH if KAHUA_BASIC_AUTH.strip().lower().startswith("basic ") \
           else f"Basic {KAHUA_BASIC_AUTH}"

HEADERS_JSON = lambda: {"Content-Type": "application/json", "Authorization": _auth_header_value()}

# Entity aliases
ENTITY_ALIASES: Dict[str, str] = {
    "project": "kahua_Project.Project",
    "projects": "kahua_Project.Project",
    "rfi": "kahua_AEC_RFI.RFI",
    "rfis": "kahua_AEC_RFI.RFI",
    "submittal": "kahua_AEC_Submittal.Submittal",
    "submittals": "kahua_AEC_Submittal.Submittal",
    "change order": "kahua_AEC_ChangeOrder.ChangeOrder",
    "change orders": "kahua_AEC_ChangeOrder.ChangeOrder",
    "punchlist": "kahua_AEC_PunchList.PunchListItem",
    "punch list": "kahua_AEC_PunchList.PunchListItem",
    "contract": "kahua_Contract.Contract",
    "contracts": "kahua_Contract.Contract",
    "invoice": "kahua_ContractInvoice.ContractInvoice",
    "invoices": "kahua_ContractInvoice.ContractInvoice",
    "daily report": "kahua_AEC_DailyReport.DailyReport",
    "meeting": "kahua_Meeting.Meeting",
}

def resolve_entity_def(name_or_def: str) -> str:
    key = (name_or_def or "").strip().lower()
    return ENTITY_ALIASES.get(key, name_or_def)


# ============== Tools ==============

@tool
def find_project(search_term: str) -> dict:
    """
    Find a project by name or partial match. ALWAYS use this when a user mentions a project by name.
    
    Args:
        search_term: Project name or partial name to search for (case-insensitive)
    
    Returns:
        Dict with matching projects including their IDs, names, and key details.
    """
    query_url = QUERY_URL_TEMPLATE.format(project_id=0)
    qpayload = {"PropertyName": "Query", "EntityDef": "kahua_Project.Project"}
    
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": "Failed to query projects"}
        body = resp.json()
    
    projects = []
    for key in ("entities", "results", "items"):
        if isinstance(body.get(key), list):
            projects = body[key]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list) and s["entities"]:
            projects = s["entities"]
            break
    
    search_lower = search_term.lower()
    matches = []
    for proj in projects:
        name = proj.get("Name", proj.get("name", ""))
        if search_lower in name.lower():
            matches.append({
                "id": proj.get("Id", proj.get("id", proj.get("ProjectId"))),
                "name": name,
                "status": proj.get("Status", proj.get("status", "")),
            })
    
    if not matches:
        return {
            "status": "no_match",
            "search_term": search_term,
            "all_projects": [{"id": p.get("Id", p.get("id")), "name": p.get("Name", p.get("name", ""))} for p in projects[:20]]
        }
    
    return {"status": "ok", "matches": matches, "best_match": matches[0] if len(matches) == 1 else None}


@tool
def count_entities(entity_def: str, project_id: int = 0, scope: str = "Any") -> dict:
    """
    FAST count of a single entity type.
    
    Args:
        entity_def: Entity type - alias ("project", "rfi", "contract") or full name.
        project_id: Project context. Use 0 for domain-wide (default).
        scope: "Any" for all records across projects (default).
    
    Returns:
        Dict with count and entity info.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": "1"}
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}"}
        body = resp.json()
    
    count = body.get("count", 0)
    return {"status": "ok", "entity_def": ent, "count": count, "project_id": project_id}


@tool
def query_entities(
    entity_def: str, 
    project_id: int = 0, 
    limit: int = 50,
    conditions_json: str = None,
    sort_by: str = None,
    sort_direction: str = "Ascending",
    scope: str = "Any"
) -> dict:
    """
    Query entities with filtering and sorting.
    
    Args:
        entity_def: Entity type alias or full name.
        project_id: Project ID. Use 0 for domain queries.
        limit: Max results (default 50).
        conditions_json: JSON string for filtering. Example: '[{"path": "Status", "type": "EqualTo", "value": "Open"}]'
        sort_by: Field to sort by.
        sort_direction: "Ascending" or "Descending".
        scope: Query scope ("Any" for cross-project).
    
    Returns:
        Dict with entities list and count.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    
    qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": str(limit)}
    
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    if conditions_json:
        try:
            conditions = json.loads(conditions_json)
            kahua_conditions = []
            for cond in conditions:
                kahua_conditions.append({
                    "PropertyName": "Data",
                    "Path": cond["path"],
                    "Type": cond["type"],
                    "Value": cond.get("value", "")
                })
            if kahua_conditions:
                qpayload["Condition"] = kahua_conditions
        except json.JSONDecodeError:
            pass
    
    if sort_by:
        qpayload["Sorts"] = [{"PropertyName": "Data", "Path": sort_by, "Direction": sort_direction}]
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        body = resp.json() if resp.status_code < 400 else {}
    
    entities = []
    count = body.get("count", 0)
    for k in ("entities", "results", "items"):
        if isinstance(body.get(k), list):
            entities = body[k]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list):
            entities = s["entities"]
            break
    
    return {"status": "ok", "entity_def": ent, "count": count, "returned": len(entities), "entities": entities}


@tool
def get_entity_schema(entity_def: str, project_id: int = 0) -> dict:
    """
    Get the field schema for an entity type by sampling a record.
    
    Args:
        entity_def: The entity type to inspect.
        project_id: Project context.
    
    Returns:
        Dict with field names and sample values.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload = {"PropertyName": "Query", "EntityDef": ent, "Take": "1", "Partition": {"Scope": "Any"}}
    
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}"}
        body = resp.json()
    
    sample = None
    for key in ("entities", "results", "items"):
        if isinstance(body.get(key), list) and body[key]:
            sample = body[key][0]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list) and s["entities"]:
            sample = s["entities"][0]
            break
    
    if not sample:
        return {"status": "ok", "entity_def": ent, "fields": [], "message": "No records found"}
    
    fields = [{"name": k, "type": type(v).__name__, "sample": str(v)[:100]} for k, v in sample.items()]
    return {"status": "ok", "entity_def": ent, "fields": sorted(fields, key=lambda x: x["name"])}


@tool
def generate_report(
    title: str,
    markdown_content: str,
    subtitle: str = None,
    charts_json: str = None
) -> dict:
    """
    Generate a professional Word document report.
    
    Args:
        title: Report title.
        markdown_content: Body content in markdown format.
        subtitle: Optional subtitle.
        charts_json: JSON array of chart specs.
    
    Returns:
        Dict with filename and download URL.
    """
    try:
        charts = json.loads(charts_json) if charts_json else None
        result = create_report(title=title, markdown_content=markdown_content, charts=charts, subtitle=subtitle)
        filename = result["filename"]
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        return {"status": "ok", "filename": filename, "download_url": f"{base_url}/reports/{filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Portable view tools - Static templates
try:
    from pv_md_renderer import preview_portable_view, finalize_portable_view, list_md_templates
    
    @tool
    def preview_md_portable_view(template_id: str, entity_data_json: str) -> dict:
        """
        Preview a portable view using an EXISTING template as rendered markdown.
        For creating NEW custom templates, use create_entity_template instead.
        
        Args:
            template_id: Template name (e.g., "contract", "rfi", "punchlist")
            entity_data_json: JSON string of entity data from query_entities
        
        Returns:
            Dict with preview_id and rendered markdown to display in chat.
        """
        try:
            entity_data = json.loads(entity_data_json)
            return preview_portable_view(template_id, entity_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def finalize_md_portable_view(preview_id: str) -> dict:
        """
        Finalize a previewed portable view and generate the DOCX.
        Only call AFTER user approves the preview.
        
        Args:
            preview_id: The preview_id from preview_md_portable_view
        
        Returns:
            Dict with download URL for the generated document.
        """
        return finalize_portable_view(preview_id)
    
    @tool
    def list_md_templates_tool() -> dict:
        """List available markdown portable view templates."""
        return list_md_templates()
    
    pv_tools = [preview_md_portable_view, finalize_md_portable_view, list_md_templates_tool]
    log.info("Portable view tools loaded")
except ImportError:
    pv_tools = []
    log.warning("Portable view tools not available")


# Dynamic Template Creation Tools
try:
    from pv_template_generator import (
        create_entity_template,
        preview_template,
        finalize_preview,
        save_template,
        load_template,
        list_saved_templates,
        update_template_markdown,
    )
    
    @tool
    def create_template_for_entity(
        entity_def: str,
        entity_display_name: str,
        schema_fields_json: str,
        style: str = "professional"
    ) -> dict:
        """
        Create a NEW reusable template for any entity type.
        Use this when user wants a custom portable view for an entity.
        
        WORKFLOW:
        1. Call get_entity_schema to get field info
        2. Call this tool to generate template
        3. Call preview_custom_template to show preview with real data
        4. Iterate based on feedback
        5. Call save_custom_template when approved
        
        Args:
            entity_def: Full entity definition (e.g., "kahua_AEC_RFI.RFI")
            entity_display_name: Human-readable name (e.g., "RFI", "Contract")
            schema_fields_json: JSON string of fields from get_entity_schema
            style: "professional", "simple", or "detailed"
        
        Returns:
            Dict with template_id and markdown content
        """
        try:
            schema_fields = json.loads(schema_fields_json)
            return create_entity_template(
                entity_def=entity_def,
                entity_display_name=entity_display_name,
                schema_fields=schema_fields,
                style=style,
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def preview_custom_template(
        template_id: str,
        template_markdown: str,
        entity_data_json: str
    ) -> dict:
        """
        Preview a custom template with actual entity data.
        Display the rendered markdown to the user for feedback.
        
        Args:
            template_id: Template identifier from create_template_for_entity
            template_markdown: The markdown template content
            entity_data_json: JSON string of entity data to render
        
        Returns:
            Dict with preview_id and rendered markdown
        """
        try:
            entity_data = json.loads(entity_data_json)
            return preview_template(template_id, template_markdown, entity_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def finalize_custom_template(preview_id: str, output_name: str = None) -> dict:
        """
        Generate DOCX from a previewed custom template.
        Call after user approves the preview.
        
        Args:
            preview_id: Preview ID from preview_custom_template
            output_name: Optional custom filename (without extension)
        
        Returns:
            Dict with download URL
        """
        return finalize_preview(preview_id, output_name)
    
    @tool
    def save_custom_template(
        template_id: str,
        name: str,
        entity_def: str,
        markdown: str,
        description: str = ""
    ) -> dict:
        """
        Save a custom template for future reuse.
        Call after user approves the template design.
        
        Args:
            template_id: Template identifier
            name: Human-readable template name
            entity_def: Target entity definition
            markdown: The markdown template content
            description: Optional description
        
        Returns:
            Dict with save status
        """
        return save_template(template_id, name, entity_def, markdown, description)
    
    @tool
    def list_custom_templates(entity_def: str = None) -> dict:
        """
        List saved custom templates.
        
        Args:
            entity_def: Optional filter by entity type
        
        Returns:
            Dict with list of saved templates
        """
        return list_saved_templates(entity_def)
    
    @tool
    def modify_template(template_id: str, new_markdown: str) -> dict:
        """
        Update the markdown content of a template based on user feedback.
        
        Args:
            template_id: Template or preview ID to update
            new_markdown: Updated markdown content
        
        Returns:
            Dict with updated preview
        """
        return update_template_markdown(template_id, new_markdown)
    
    template_gen_tools = [
        create_template_for_entity,
        preview_custom_template,
        finalize_custom_template,
        save_custom_template,
        list_custom_templates,
        modify_template,
    ]
    log.info("Template generation tools loaded")
except ImportError as e:
    template_gen_tools = []
    log.warning(f"Template generation tools not available: {e}")


# ============== Agent State ==============

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ============== LLM Setup ==============

def create_llm():
    """Create Claude LLM configured for Azure."""
    # Azure Anthropic endpoint format
    base_url = f"{AZURE_ENDPOINT}/anthropic"
    
    return ChatAnthropic(
        model=MODEL_DEPLOYMENT,
        api_key=AZURE_KEY,
        base_url=base_url,
        max_tokens=8192,
    )


# ============== System Prompt ==============

SYSTEM_PROMPT = """You are an expert Construction Project Analyst for Kahua. You create professional, data-driven reports and custom document templates.

## CORE PRINCIPLE: ACT, DON'T ASK

You have access to real data. Never ask permission - just do it.

**NEVER SAY:**
- "Would you like me to..."
- "Should I proceed with..."
- "Let me know if you'd like me to..."

**INSTEAD:** Just execute and present results directly.

## TOOLS

### Data Access
- **find_project(search_term)**: Find project by name. REQUIRED when user mentions a project name.
- **count_entities(entity_def)**: Fast count. Use for "how many X?" questions.
- **query_entities(entity_def, ...)**: Get entity data with filtering/sorting.
- **get_entity_schema(entity_def)**: See available fields for an entity type.
- **generate_report(title, markdown_content)**: Create Word document reports.

### Existing Templates (Pre-built)
- **list_md_templates_tool()**: See available pre-built templates
- **preview_md_portable_view(template_id, entity_data_json)**: Preview with existing template
- **finalize_md_portable_view(preview_id)**: Generate DOCX after approval

### Custom Template Creation (Dynamic - PREFERRED)
- **create_template_for_entity(entity_def, display_name, schema_fields_json)**: Create a NEW custom template
- **preview_custom_template(template_id, markdown, entity_data_json)**: Preview the custom template
- **modify_template(template_id, new_markdown)**: Update template based on feedback  
- **save_custom_template(template_id, name, entity_def, markdown)**: Save for reuse
- **finalize_custom_template(preview_id)**: Generate DOCX
- **list_custom_templates()**: List saved custom templates

## CUSTOM TEMPLATE WORKFLOW (CRITICAL!)

When user wants a "portable view", "template", or "document" for an entity type:

**STEP 1: Understand the Entity**
- Call `get_entity_schema(entity_def)` to see all available fields
- Note which fields are most relevant for the document

**STEP 2: Create the Template**
- Call `create_template_for_entity()` with the schema
- This generates a markdown template with Jinja2 syntax

**STEP 3: Get Real Data**
- Call `query_entities()` to get a sample record
- Use this for realistic preview

**STEP 4: Preview & Iterate**
- Call `preview_custom_template()` with template and data
- DISPLAY the rendered markdown in chat
- Say: "Here's a preview of your [Entity] template:"
- Show the markdown
- Ask: "What would you like to change? You can ask me to:
  - Add/remove fields
  - Change the layout
  - Adjust formatting
  - Or say 'looks good' to save"

**STEP 5: Handle Feedback**
- If user wants changes, modify the markdown and call `preview_custom_template()` again
- Show the updated preview
- Repeat until satisfied

**STEP 6: Save When Ready**
- When user approves, call `save_custom_template()` to save for reuse
- Optionally call `finalize_custom_template()` to generate a DOCX

## Entity Aliases
- "rfi" → kahua_AEC_RFI.RFI
- "contract" → kahua_Contract.Contract
- "punch list" → kahua_AEC_PunchList.PunchListItem
- "submittal" → kahua_AEC_Submittal.Submittal
- "change order" → kahua_AEC_ChangeOrder.ChangeOrder

## OUTPUT FORMAT
- Lead with key numbers
- Use markdown tables for lists
- Bold important values: **$2.4M**, **15 open**
- Status icons: ✅ Complete, ⚠️ At Risk, ❌ Blocked
- When showing template previews, use code blocks for clarity
"""


# ============== Graph Definition ==============

def create_agent():
    """Create the LangGraph agent."""
    
    # All tools
    all_tools = [find_project, count_entities, query_entities, get_entity_schema, generate_report] + pv_tools + template_gen_tools
    
    # Create LLM with tools bound
    llm = create_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Agent node - calls LLM
    def agent_node(state: AgentState):
        messages = state["messages"]
        
        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Tool node - executes tools
    tool_node = ToolNode(all_tools)
    
    # Router - decide next step
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ============== Main Interface ==============

_agent = None

def get_agent():
    """Get or create the agent singleton."""
    global _agent
    if _agent is None:
        log.info(f"Creating LangGraph agent with model: {MODEL_DEPLOYMENT}")
        _agent = create_agent()
    return _agent


async def chat(message: str, session_id: str = "default") -> str:
    """
    Send a message to the agent and get a response.
    
    Args:
        message: User message
        session_id: Session ID for conversation memory
    
    Returns:
        Agent response text
    """
    agent = get_agent()
    
    config = {"configurable": {"thread_id": session_id}}
    
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    # Get the last AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated."


def chat_sync(message: str, session_id: str = "default") -> str:
    """Synchronous version of chat."""
    agent = get_agent()
    
    config = {"configurable": {"thread_id": session_id}}
    
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated."


# ============== Test ==============

if __name__ == "__main__":
    print("Testing LangGraph agent...")
    response = chat_sync("Hello! What model are you?")
    print(f"\nResponse:\n{response}")
