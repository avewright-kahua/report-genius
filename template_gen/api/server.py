"""
FastAPI server exposing the template agent as a chat API.

Integrates with LangGraph agent for natural language template customization.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema_introspector import get_available_schemas, get_schema_summary
from template_generator import generate_template
from template_renderer import generate_sample_data, render_to_markdown
from template_schema import SectionType
from docx_renderer import DocxRenderer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import the agent (may fail if no API key configured)
_agent = None
_agent_available = False

def _get_agent():
    """Lazily initialize the LangGraph agent."""
    global _agent, _agent_available
    if _agent is None and not _agent_available:
        try:
            from graph_agent import create_agent
            _agent = create_agent()
            _agent_available = True
            logger.info("LangGraph agent initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize LangGraph agent: {e}")
            _agent_available = False
    return _agent

app = FastAPI(title="Template Generator API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (replace with Redis for production)
sessions: Dict[str, Dict[str, Any]] = {}


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    preview: Optional[Dict[str, Any]] = None


class EntityInfo(BaseModel):
    name: str
    entity_def: str
    field_counts: Dict[str, int]


@app.get("/api/entities")
async def list_entities() -> List[EntityInfo]:
    """List available entity types."""
    schemas = get_available_schemas()
    result = []
    for name, schema in schemas.items():
        summary = get_schema_summary(schema)
        result.append(EntityInfo(
            name=name,
            entity_def=schema.entity_def,
            field_counts=summary["field_counts"],
        ))
    return result


@app.get("/api/entities/{entity_type}/fields")
async def get_entity_fields(entity_type: str, category: Optional[str] = None):
    """Get fields for an entity type."""
    schemas = get_available_schemas()
    if entity_type not in schemas:
        raise HTTPException(404, f"Unknown entity: {entity_type}")
    
    schema = schemas[entity_type]
    summary = get_schema_summary(schema)
    
    if category:
        if category not in summary["fields_by_category"]:
            raise HTTPException(404, f"Unknown category: {category}")
        return {category: summary["fields_by_category"][category]}
    
    return summary["fields_by_category"]


@app.post("/api/templates/generate/{entity_type}")
async def generate_template_endpoint(entity_type: str):
    """Generate a new template for an entity type."""
    schemas = get_available_schemas()
    if entity_type not in schemas:
        raise HTTPException(404, f"Unknown entity: {entity_type}")
    
    schema = schemas[entity_type]
    template = generate_template(schema)
    
    # Generate preview
    sample = generate_sample_data(template)
    preview = render_to_markdown(template, sample)
    
    return {
        "template": template.model_dump(),
        "preview": preview,
        "sections": [
            {"index": i, "type": s.type.value, "title": s.title}
            for i, s in enumerate(template.get_sections_ordered())
        ],
    }


class ExportRequest(BaseModel):
    entity_type: str
    session_id: Optional[str] = None


@app.post("/api/templates/export")
async def export_template(request: ExportRequest):
    """Export template to Word document."""
    from template_schema import PortableViewTemplate
    
    # Try to get template from session or generate new one
    template_data = None
    if request.session_id and request.session_id in sessions:
        template_data = sessions[request.session_id].get("template")
    
    if not template_data:
        # Generate fresh template
        schemas = get_available_schemas()
        if request.entity_type not in schemas:
            raise HTTPException(404, f"Unknown entity: {request.entity_type}")
        schema = schemas[request.entity_type]
        template = generate_template(schema)
    else:
        template = PortableViewTemplate(**template_data)
    
    renderer = DocxRenderer(template)
    
    # Save to temp file
    output_dir = Path(__file__).parent.parent / "pv_templates" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{template.id}.docx"
    
    renderer.render_to_file(output_path)
    
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{template.name.replace(' ', '_')}.docx",
    )


# ============================================================================
# Template Customization Parser
# ============================================================================

class TemplateOptions(BaseModel):
    """Parsed customization options from user request."""
    entity_type: Optional[str] = None
    include_logo: bool = True
    include_financials: bool = True
    include_tables: bool = True
    include_text_blocks: bool = True
    style: str = "full"  # full, minimal, compact
    specific_fields: Optional[List[str]] = None  # If user only wants certain fields
    exclude_fields: Optional[List[str]] = None
    sections_to_remove: Optional[List[str]] = None


def parse_template_request(message: str, available_entities: List[str]) -> TemplateOptions:
    """Parse a natural language request into template options.
    
    Examples:
    - "create RFI template with logo" -> include_logo=True
    - "minimal submittal report" -> style=minimal
    - "contract template without financials" -> include_financials=False
    - "RFI with only status and dates" -> specific_fields=[status, dates]
    """
    msg = message.lower()
    opts = TemplateOptions()
    
    # Find entity type
    for entity in available_entities:
        if entity.lower() in msg:
            opts.entity_type = entity
            break
    
    # Parse style
    if "minimal" in msg or "simple" in msg or "basic" in msg:
        opts.style = "minimal"
    elif "compact" in msg or "brief" in msg:
        opts.style = "compact"
    
    # Parse logo preference
    if "no logo" in msg or "without logo" in msg:
        opts.include_logo = False
    elif "with logo" in msg or "include logo" in msg or "company logo" in msg:
        opts.include_logo = True
    
    # Parse section exclusions
    if "without financial" in msg or "no financial" in msg or "skip financial" in msg:
        opts.include_financials = False
    
    if "without table" in msg or "no table" in msg:
        opts.include_tables = False
    
    # Parse specific field requests
    if "only" in msg:
        # Try to extract field names after "only"
        # e.g., "only status and dates" or "only include number, subject"
        parts = msg.split("only")
        if len(parts) > 1:
            field_part = parts[1].strip()
            # Simple extraction - split on "and", ","
            field_part = field_part.replace(" and ", ",")
            potential_fields = [f.strip() for f in field_part.split(",") if f.strip()]
            if potential_fields and len(potential_fields) < 10:
                opts.specific_fields = potential_fields
    
    return opts


@app.post("/api/chat")
async def chat(request: ChatMessage) -> ChatResponse:
    """Chat with the template agent.
    
    Supports natural language customization of templates:
    - "create RFI template with company logo"
    - "minimal submittal report without financials"
    - "show me fields for ExpenseContract"
    """
    import uuid
    
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [],
            "template": None,
            "agent_state": None,
        }
    
    session = sessions[session_id]
    msg = request.message.lower().strip()
    response_text = ""
    preview = None
    
    schemas = get_available_schemas()
    entity_names = list(schemas.keys())
    
    # Check if we should try the LangGraph agent
    agent = _get_agent()
    if agent and not any(kw in msg for kw in ["list", "help", "?"]):
        # Try agent-powered response for complex requests
        try:
            from langchain_core.messages import HumanMessage, AIMessage
            
            # Restore or initialize agent state
            if session.get("agent_state") is None:
                session["agent_state"] = {
                    "messages": [],
                    "current_template": session.get("template"),
                    "available_schemas": {},
                    "last_preview": None,
                }
            
            state = session["agent_state"]
            state["messages"].append(HumanMessage(content=request.message))
            
            # Invoke agent
            result = agent.invoke(state)
            session["agent_state"] = result
            
            # Extract response
            for msg_item in reversed(result["messages"]):
                if isinstance(msg_item, AIMessage):
                    response_text = msg_item.content
                    break
            
            # Try to extract template and preview from agent output
            if result.get("current_template"):
                session["template"] = result["current_template"]
                from template_schema import PortableViewTemplate
                template = PortableViewTemplate(**result["current_template"])
                sample = generate_sample_data(template)
                markdown = render_to_markdown(template, sample)
                preview = {
                    "entity_type": template.entity_type,
                    "markdown": markdown,
                    "sections": [
                        {"type": s.type.value, "title": s.title}
                        for s in template.get_sections_ordered()
                    ],
                }
            
            # Store messages
            session["messages"].append({"role": "user", "content": request.message})
            session["messages"].append({"role": "assistant", "content": response_text})
            
            return ChatResponse(
                response=response_text,
                session_id=session_id,
                preview=preview,
            )
        except Exception as e:
            logger.warning(f"Agent failed, falling back to rule-based: {e}")
    
    # Fallback: Rule-based handling with customization parsing
    if "list" in msg and ("entities" in msg or "types" in msg):
        response_text = f"Available entity types: {', '.join(entity_names)}"
    
    elif "create" in msg or "generate" in msg or "make" in msg:
        # Parse customization options
        opts = parse_template_request(request.message, entity_names)
        
        if opts.entity_type:
            from template_generator import generate_template, generate_minimal_template
            
            schema = schemas[opts.entity_type]
            
            # Generate template with options
            if opts.style == "minimal":
                template = generate_minimal_template(schema)
            else:
                template = generate_template(
                    schema,
                    include_financials=opts.include_financials,
                    include_text_blocks=opts.include_text_blocks,
                    include_tables=opts.include_tables,
                )
            
            # Apply logo setting
            header_section = next(
                (s for s in template.sections if s.type == SectionType.HEADER),
                None
            )
            if header_section and header_section.header_config:
                header_section.header_config.show_logo = opts.include_logo
            
            session["template"] = template.model_dump()
            
            sample = generate_sample_data(template)
            markdown = render_to_markdown(template, sample)
            sections = [
                {"type": s.type.value, "title": s.title}
                for s in template.get_sections_ordered()
            ]
            
            preview = {
                "entity_type": opts.entity_type,
                "markdown": markdown,
                "sections": sections,
            }
            
            # Build descriptive response
            customizations = []
            if opts.include_logo:
                customizations.append("company logo")
            if not opts.include_financials:
                customizations.append("no financials")
            if opts.style == "minimal":
                customizations.append("minimal style")
            
            desc = f" with {', '.join(customizations)}" if customizations else ""
            response_text = f"Created {opts.entity_type} template{desc}. {len(sections)} sections included."
        else:
            response_text = f"Please specify an entity type. Available: {', '.join(entity_names)}"
    
    elif "remove" in msg or "delete" in msg:
        # Handle section removal
        if session.get("template"):
            from template_schema import PortableViewTemplate
            template = PortableViewTemplate(**session["template"])
            
            removed = []
            if "financial" in msg:
                template.sections = [s for s in template.sections if s.title != "Financials"]
                removed.append("Financials")
            if "table" in msg:
                original_count = len(template.sections)
                template.sections = [s for s in template.sections if s.type != SectionType.TABLE]
                if len(template.sections) < original_count:
                    removed.append("table sections")
            if "logo" in msg:
                for s in template.sections:
                    if s.type == SectionType.HEADER and s.header_config:
                        s.header_config.show_logo = False
                        removed.append("logo")
            
            # Reorder
            for i, s in enumerate(template.sections):
                s.order = i
            
            session["template"] = template.model_dump()
            
            sample = generate_sample_data(template)
            markdown = render_to_markdown(template, sample)
            preview = {
                "entity_type": template.entity_type,
                "markdown": markdown,
                "sections": [
                    {"type": s.type.value, "title": s.title}
                    for s in template.get_sections_ordered()
                ],
            }
            
            if removed:
                response_text = f"Removed: {', '.join(removed)}. Template updated."
            else:
                response_text = "Couldn't identify what to remove. Try: 'remove financials' or 'remove tables'"
        else:
            response_text = "No template to modify. Create one first."
    
    elif "add" in msg:
        if session.get("template"):
            from template_schema import PortableViewTemplate
            template = PortableViewTemplate(**session["template"])
            
            added = []
            if "logo" in msg:
                for s in template.sections:
                    if s.type == SectionType.HEADER and s.header_config:
                        s.header_config.show_logo = True
                        added.append("company logo")
            
            session["template"] = template.model_dump()
            
            sample = generate_sample_data(template)
            markdown = render_to_markdown(template, sample)
            preview = {
                "entity_type": template.entity_type,
                "markdown": markdown,
                "sections": [
                    {"type": s.type.value, "title": s.title}
                    for s in template.get_sections_ordered()
                ],
            }
            
            if added:
                response_text = f"Added: {', '.join(added)}. Template updated."
            else:
                response_text = "Couldn't identify what to add. Try: 'add logo'"
        else:
            response_text = "No template to modify. Create one first."
    
    elif "fields" in msg:
        entity_type = None
        for name in entity_names:
            if name.lower() in msg:
                entity_type = name
                break
        
        if entity_type:
            schema = schemas[entity_type]
            summary = get_schema_summary(schema)
            counts = summary["field_counts"]
            response_text = f"**{entity_type} Fields:**\n"
            for cat, count in counts.items():
                response_text += f"- {cat}: {count} fields\n"
            
            # Show some example fields
            response_text += "\n**Examples:**\n"
            for cat, fields in list(summary["fields_by_category"].items())[:3]:
                field_names = [f["label"] for f in fields[:3]]
                response_text += f"- {cat}: {', '.join(field_names)}\n"
        else:
            response_text = "Please specify an entity type to see its fields."
    
    elif "export" in msg or "download" in msg:
        if session["template"]:
            response_text = "Click the **Export to Word** button to download your template."
        else:
            response_text = "No template to export. Create one first."
    
    elif "preview" in msg or "show" in msg:
        if session["template"]:
            from template_schema import PortableViewTemplate
            template = PortableViewTemplate(**session["template"])
            sample = generate_sample_data(template)
            markdown = render_to_markdown(template, sample)
            preview = {
                "entity_type": template.entity_type,
                "markdown": markdown,
                "sections": [
                    {"type": s.type.value, "title": s.title}
                    for s in template.get_sections_ordered()
                ],
            }
            response_text = "Here's your current template."
        else:
            response_text = "No template yet. Try: 'create RFI template with logo'"
    
    else:
        response_text = (
            "I can help you create and customize portable view templates.\n\n"
            "**Create a template:**\n"
            "- `create RFI template with company logo`\n"
            "- `minimal submittal report`\n"
            "- `contract template without financials`\n\n"
            "**Modify existing template:**\n"
            "- `remove the financials section`\n"
            "- `add company logo`\n"
            "- `remove all tables`\n\n"
            "**Explore:**\n"
            "- `list entity types`\n"
            "- `show fields for RFI`"
        )
    
    # Store message history
    session["messages"].append({"role": "user", "content": request.message})
    session["messages"].append({"role": "assistant", "content": response_text})
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        preview=preview,
    )


@app.get("/api/sessions/{session_id}/template")
async def get_session_template(session_id: str):
    """Get the current template for a session."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    template = sessions[session_id].get("template")
    if not template:
        raise HTTPException(404, "No template in session")
    
    return template


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)