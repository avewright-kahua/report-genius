import os
import json
import asyncio
import time
from pathlib import Path
from typing import Any, Dict, Callable, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Reports directory - create if doesn't exist
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Load .env BEFORE importing modules that read env at import time
load_dotenv()

# Use LangGraph agent (Claude via Anthropic SDK)
from langgraph_agent import chat as langgraph_chat, get_agent, reset_session
import logging

# Template builder API router
from template_builder_api import router as template_builder_router


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


app = FastAPI(title="Kahua Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include template builder API routes
app.include_router(template_builder_router)


@app.on_event("startup")
async def _startup() -> None:
    # Warm up the LangGraph agent on startup
    app.state.agent = get_agent()
    logging.getLogger("uvicorn.error").info("LangGraph Agent loaded (Claude)")


@app.on_event("shutdown")
async def _shutdown() -> None:
    pass  # No cleanup needed for LangGraph


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/agent")
async def agent_info() -> Dict[str, Any]:
    return {
        "name": "Kahua Construction Analyst",
        "model": "Claude (via LangGraph)",
        "status": "ready"
    }


@app.get("/reports/{filename}")
async def get_report(filename: str):
    """Serve a generated report (Word doc) for download."""
    # Security: no path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Auto-append .docx if no extension provided
    if not (filename.endswith(".docx") or filename.endswith(".pdf")):
        # Try to find the file with .docx extension
        docx_path = REPORTS_DIR / f"{filename}.docx"
        if docx_path.exists():
            filename = f"{filename}.docx"
        else:
            # Try .pdf
            pdf_path = REPORTS_DIR / f"{filename}.pdf"
            if pdf_path.exists():
                filename = f"{filename}.pdf"
            else:
                raise HTTPException(status_code=404, detail="Report not found")
    
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Set correct media type
    if filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/pdf"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
        }
    )


# ============== Portable View Template API ==============

PV_TEMPLATES_DIR = Path(__file__).parent / "pv_templates" / "saved"

@app.get("/api/pv-templates")
async def list_pv_templates() -> Dict[str, Any]:
    """List available portable view templates."""
    templates = []
    if PV_TEMPLATES_DIR.exists():
        for f in PV_TEMPLATES_DIR.glob("*.json"):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    templates.append({
                        "id": data.get("id", f.stem),
                        "name": data.get("name", "Untitled"),
                        "description": data.get("description", "")[:200],
                        "target_entity_def": data.get("target_entity_def", ""),
                        "created_at": data.get("created_at"),
                    })
            except Exception:
                pass
    return {"templates": templates, "count": len(templates)}


@app.get("/api/pv-templates/{template_id}")
async def get_pv_template(template_id: str) -> Dict[str, Any]:
    """Get a portable view template by ID."""
    # Security check
    if ".." in template_id or "/" in template_id or "\\" in template_id:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    # Try with and without .json extension
    file_path = PV_TEMPLATES_DIR / f"{template_id}.json"
    if not file_path.exists():
        file_path = PV_TEMPLATES_DIR / template_id
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")
    
    with open(file_path, 'r') as f:
        return json.load(f)


@app.get("/api/pv-templates/{template_id}/download")
async def download_pv_template(template_id: str):
    """Download a portable view template as JSON."""
    # Security check
    if ".." in template_id or "/" in template_id or "\\" in template_id:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    file_path = PV_TEMPLATES_DIR / f"{template_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=f"{template_id}.json",
        headers={"Content-Disposition": f"attachment; filename=\"{template_id}.json\""}
    )


class RenderPVTemplateRequest(BaseModel):
    entity_data: dict  # The entity data to render


@app.post("/api/pv-templates/{template_id}/render")
async def render_pv_template(template_id: str, req: RenderPVTemplateRequest) -> Dict[str, Any]:
    """Render a portable view template with entity data to a Word document."""
    from pv_template_schema import PortableTemplate
    from pv_template_renderer import TemplateRenderer
    
    # Security check
    if ".." in template_id or "/" in template_id or "\\" in template_id:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    file_path = PV_TEMPLATES_DIR / f"{template_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Load template
    with open(file_path, 'r') as f:
        template = PortableTemplate.from_json(f.read())
    
    # Extract entity data from wrapped formats
    entity_data = req.entity_data
    if isinstance(entity_data, dict):
        if "entities" in entity_data and isinstance(entity_data["entities"], list):
            if entity_data["entities"]:
                entity_data = entity_data["entities"][0]
            else:
                raise HTTPException(status_code=400, detail="No entities in data")
        elif "sets" in entity_data and isinstance(entity_data["sets"], list):
            for s in entity_data["sets"]:
                if isinstance(s.get("entities"), list) and s["entities"]:
                    entity_data = s["entities"][0]
                    break
    
    # Render to document
    renderer = TemplateRenderer(output_dir=REPORTS_DIR)
    output_path, doc_bytes = renderer.render(template, entity_data)
    
    return {
        "status": "ok",
        "filename": output_path.name,
        "download_url": f"/reports/{output_path.name}",
        "size_bytes": len(doc_bytes)
    }


@app.get("/reports")
async def list_reports() -> Dict[str, Any]:
    """List all available reports."""
    reports = []
    # Support both .docx and .pdf
    for ext in ["*.docx", "*.pdf"]:
        for f in REPORTS_DIR.glob(ext):
            reports.append({
                "filename": f.name,
                "url": f"/reports/{f.name}",
                "size_bytes": f.stat().st_size,
                "created": f.stat().st_ctime,
            })
    # Sort by creation time, newest first
    reports.sort(key=lambda r: r["created"], reverse=True)
    return {"reports": reports}


# ============== File Upload API ==============

from fastapi import UploadFile, File as FastAPIFile

UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...)) -> Dict[str, Any]:
    """
    Upload a file (image, docx, pdf) for use in reports.
    Returns the file path that can be used in templates.
    """
    try:
        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", 
                            ".pdf", ".docx", ".doc", ".xlsx", ".xls"}
        suffix = Path(file.filename).suffix.lower()
        if suffix not in allowed_extensions:
            return {"status": "error", "error": f"File type {suffix} not allowed"}
        
        # Save file
        dest_path = UPLOADS_DIR / file.filename
        content = await file.read()
        dest_path.write_bytes(content)
        
        # Determine file type
        file_type = "unknown"
        if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            file_type = "image"
        elif suffix == ".pdf":
            file_type = "pdf"
        elif suffix in [".docx", ".doc"]:
            file_type = "word"
        elif suffix in [".xlsx", ".xls"]:
            file_type = "excel"
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        
        return {
            "status": "ok",
            "filename": file.filename,
            "path": str(dest_path),
            "type": file_type,
            "size_bytes": len(content),
            "url": f"{base_url}/uploads/{file.filename}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Serve an uploaded file."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".bmp": "image/bmp", ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel"
    }
    
    return FileResponse(path=file_path, media_type=media_types.get(suffix, "application/octet-stream"))


@app.get("/uploads")
async def list_uploads() -> Dict[str, Any]:
    """List all uploaded files."""
    files = []
    for f in UPLOADS_DIR.iterdir():
        if f.is_file():
            suffix = f.suffix.lower()
            file_type = "image" if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"] else "document"
            files.append({
                "filename": f.name,
                "type": file_type,
                "size_bytes": f.stat().st_size,
                "url": f"/uploads/{f.name}"
            })
    return {"files": files, "count": len(files)}


# ============== Template Management API ==============

from templates import get_template_store, ReportTemplate, SectionTemplate, ChartTemplate

class TemplateCreateRequest(BaseModel):
    name: str
    description: str
    category: str  # "cost", "field", "executive", "custom"
    title_template: str
    subtitle_template: str | None = None
    sections: list[dict] = []
    default_params: dict = {}
    header_color: str = "#1a365d"
    accent_color: str = "#3182ce"
    tags: list[str] = []
    is_public: bool = False


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    title_template: str | None = None
    subtitle_template: str | None = None
    sections: list[dict] | None = None
    default_params: dict | None = None
    header_color: str | None = None
    accent_color: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None


class SavedQueryRequest(BaseModel):
    name: str
    query_text: str
    description: str | None = None
    entity_def: str | None = None
    conditions: list[dict] | None = None


@app.get("/api/templates")
async def list_templates(
    category: str | None = None,
    search: str | None = None
) -> Dict[str, Any]:
    """List all report templates with optional filtering."""
    store = get_template_store()
    templates = store.list_templates(category=category, search=search)
    result_templates = [t.to_dict() for t in templates]
    
    # Also include custom templates from pv_template_generator
    try:
        from pv_template_generator import list_saved_templates
        custom_result = list_saved_templates()
        for ct in custom_result.get("templates", []):
            # Convert to same format as ReportTemplate
            custom_template = {
                "id": ct["id"],
                "name": ct["name"],
                "description": ct.get("description", ""),
                "category": "portable-view",  # Special category for PV templates
                "entity_def": ct.get("entity_def"),
                "created_at": ct.get("created_at"),
                "is_custom": True,  # Flag to identify agent-created templates
            }
            # Apply filters if provided
            if category and category != "portable-view":
                continue
            if search and search.lower() not in ct["name"].lower():
                continue
            result_templates.append(custom_template)
    except ImportError:
        pass  # pv_template_generator not available
    
    return {
        "templates": result_templates,
        "count": len(result_templates)
    }


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str) -> Dict[str, Any]:
    """Get a single template by ID."""
    store = get_template_store()
    template = store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template.to_dict()


@app.post("/api/templates")
async def create_template(req: TemplateCreateRequest) -> Dict[str, Any]:
    """Create a new report template."""
    store = get_template_store()
    
    # Convert sections from dict to SectionTemplate objects
    sections = []
    for i, s in enumerate(req.sections):
        chart = None
        if s.get("chart"):
            chart = ChartTemplate(**s["chart"])
        sections.append(SectionTemplate(
            title=s.get("title", f"Section {i+1}"),
            section_type=s.get("section_type", "text"),
            content=s.get("content"),
            entity_def=s.get("entity_def"),
            fields=s.get("fields"),
            conditions=s.get("conditions"),
            chart=chart,
            order=s.get("order", i)
        ))
    
    template = ReportTemplate(
        id="",  # Will be generated
        name=req.name,
        description=req.description,
        category=req.category,
        created_at="",  # Will be set
        updated_at="",
        title_template=req.title_template,
        subtitle_template=req.subtitle_template,
        sections=sections,
        default_params=req.default_params,
        header_color=req.header_color,
        accent_color=req.accent_color,
        tags=req.tags,
        is_public=req.is_public
    )
    
    created = store.create_template(template)
    return {"status": "ok", "template": created.to_dict()}


@app.put("/api/templates/{template_id}")
async def update_template(template_id: str, req: TemplateUpdateRequest) -> Dict[str, Any]:
    """Update an existing template."""
    store = get_template_store()
    existing = store.get_template(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update fields that were provided
    if req.name is not None:
        existing.name = req.name
    if req.description is not None:
        existing.description = req.description
    if req.category is not None:
        existing.category = req.category
    if req.title_template is not None:
        existing.title_template = req.title_template
    if req.subtitle_template is not None:
        existing.subtitle_template = req.subtitle_template
    if req.default_params is not None:
        existing.default_params = req.default_params
    if req.header_color is not None:
        existing.header_color = req.header_color
    if req.accent_color is not None:
        existing.accent_color = req.accent_color
    if req.tags is not None:
        existing.tags = req.tags
    if req.is_public is not None:
        existing.is_public = req.is_public
    
    # Handle sections update
    if req.sections is not None:
        sections = []
        for i, s in enumerate(req.sections):
            chart = None
            if s.get("chart"):
                chart = ChartTemplate(**s["chart"])
            sections.append(SectionTemplate(
                title=s.get("title", f"Section {i+1}"),
                section_type=s.get("section_type", "text"),
                content=s.get("content"),
                entity_def=s.get("entity_def"),
                fields=s.get("fields"),
                conditions=s.get("conditions"),
                chart=chart,
                order=s.get("order", i)
            ))
        existing.sections = sections
    
    updated = store.update_template(existing)
    return {"status": "ok", "template": updated.to_dict()}


@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str) -> Dict[str, Any]:
    """Delete a template."""
    store = get_template_store()
    
    # Prevent deletion of built-in templates
    if template_id.startswith("builtin-"):
        raise HTTPException(status_code=403, detail="Cannot delete built-in templates")
    
    success = store.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "ok", "deleted": template_id}


# ============== Saved Queries API ==============

@app.get("/api/queries")
async def list_saved_queries(search: str | None = None) -> Dict[str, Any]:
    """List all saved queries."""
    store = get_template_store()
    queries = store.get_saved_queries(search=search)
    return {"queries": queries, "count": len(queries)}


@app.post("/api/queries")
async def save_query(req: SavedQueryRequest) -> Dict[str, Any]:
    """Save a query for reuse."""
    store = get_template_store()
    query_id = store.save_query(
        name=req.name,
        query_text=req.query_text,
        description=req.description,
        entity_def=req.entity_def,
        conditions=req.conditions
    )
    return {"status": "ok", "query_id": query_id}


@app.delete("/api/queries/{query_id}")
async def delete_query(query_id: str) -> Dict[str, Any]:
    """Delete a saved query."""
    store = get_template_store()
    success = store.delete_saved_query(query_id)
    if not success:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"status": "ok", "deleted": query_id}


# ============== Chat API ==============


@app.post("/api/chat/reset")
async def reset_chat_session(req: ChatRequest = None) -> Dict[str, Any]:
    """Reset a chat session if it gets corrupted (e.g., pending tool calls)."""
    session_id = (req.session_id if req else None) or "web"
    reset_session(session_id)
    return {"status": "ok", "message": f"Session {session_id} reset"}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    log = logging.getLogger("uvicorn.error")
    
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    session_id = (req.session_id or "web").strip()
    
    try:
        log.info("/api/chat session=%s message=%s", session_id, req.message[:50])
        response = await langgraph_chat(req.message.strip(), session_id=session_id)
        log.info("Got response, length=%d", len(response))
    except Exception as e:
        log.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "final_output": response,
    }

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Streaming endpoint - falls back to non-streaming for now with LangGraph."""
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    session_id = (req.session_id or "web").strip()

    async def event_stream():
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        try:
            # LangGraph doesn't have built-in streaming yet, so get full response
            response = await langgraph_chat(req.message.strip(), session_id=session_id)
            
            # Emit as a single delta for now
            yield f"data: {json.dumps({'type': 'delta', 'content': response})}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


# ============== Unified Template API (SOTA Agent) ==============

from unified_templates import get_unified_system

class SmartComposeRequest(BaseModel):
    """Request to create a template using SOTA agent."""
    entity_type: str
    archetype: str | None = None
    user_intent: str | None = None
    name: str | None = None


class AgentToolRequest(BaseModel):
    """Request to execute an agent tool."""
    tool_name: str
    args: Dict[str, Any]


@app.get("/api/unified/archetypes")
async def list_archetypes() -> Dict[str, Any]:
    """List available template archetypes."""
    system = get_unified_system()
    return {"archetypes": system.get_archetypes()}


@app.get("/api/unified/entities")
async def list_tg_entities() -> Dict[str, Any]:
    """List entity types available in template_gen."""
    system = get_unified_system()
    entities = []
    for name, schema in system.tg_schemas.items():
        entities.append({
            "id": name,
            "name": schema.name,
            "entity_def": schema.entity_def,
            "field_count": len(schema.fields),
        })
    return {"entities": entities}


@app.post("/api/unified/compose")
async def smart_compose_template(req: SmartComposeRequest) -> Dict[str, Any]:
    """Create a template using SOTA agent composer."""
    try:
        system = get_unified_system()
        template = system.compose_smart(
            entity_type=req.entity_type,
            archetype=req.archetype,
            user_intent=req.user_intent,
            name=req.name,
        )
        
        # Save template
        output_dir = Path(__file__).parent / "pv_templates" / "saved"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = output_dir / f"{template.id}.json"
        json_path.write_text(template.model_dump_json(indent=2))
        
        return {
            "status": "ok",
            "template": template.model_dump(),
            "saved_path": str(json_path),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/unified/render-docx/{template_id}")
async def render_unified_template(template_id: str) -> Dict[str, Any]:
    """Render a unified template to DOCX with Kahua syntax."""
    from unified_templates import get_unified_system
    from template_gen.template_schema import PortableViewTemplate
    
    # Security check
    if ".." in template_id or "/" in template_id or "\\" in template_id:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    # Find template
    saved_dir = Path(__file__).parent / "pv_templates" / "saved"
    json_path = saved_dir / f"{template_id}.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Load and render
    template = PortableViewTemplate.model_validate_json(json_path.read_text())
    system = get_unified_system()
    
    docx_path = REPORTS_DIR / f"{template_id}.docx"
    system.render_to_docx(template, docx_path)
    
    return {
        "status": "ok",
        "filename": docx_path.name,
        "download_url": f"/reports/{docx_path.name}",
    }


# Agent session storage (simple in-memory for now)
_agent_sessions: Dict[str, Any] = {}

@app.post("/api/unified/agent/session")
async def create_agent_session() -> Dict[str, Any]:
    """Create a new agent session for conversational template creation."""
    import uuid
    session_id = f"agent-{uuid.uuid4().hex[:8]}"
    
    system = get_unified_system()
    session = system.create_agent_session()
    _agent_sessions[session_id] = session
    
    return {
        "session_id": session_id,
        "tools": session.available_tools,
    }


@app.post("/api/unified/agent/{session_id}/execute")
async def execute_agent_tool(session_id: str, req: AgentToolRequest) -> Dict[str, Any]:
    """Execute a tool in an agent session."""
    if session_id not in _agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _agent_sessions[session_id]
    result = session.execute_tool(req.tool_name, req.args)
    
    # Include current template if one exists
    current = None
    if session.current_template:
        current = session.current_template.model_dump()
    
    return {
        "result": result,
        "current_template": current,
    }


@app.get("/api/unified/agent/{session_id}/template")
async def get_agent_session_template(session_id: str) -> Dict[str, Any]:
    """Get the current template from an agent session."""
    if session_id not in _agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _agent_sessions[session_id]
    if not session.current_template:
        return {"template": None}
    
    return {"template": session.current_template.model_dump()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
