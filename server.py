import os
import json
import asyncio
import time
from pathlib import Path
from typing import Any, Dict, Callable, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
try:
    from openai.types.responses import ResponseTextDeltaEvent
except Exception:
    ResponseTextDeltaEvent = None  # type: ignore
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Reports directory - create if doesn't exist
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Load .env BEFORE importing modules that read env at import time
load_dotenv()

from agents_superagent import get_super_agent
from agents import Runner, SQLiteSession
import logging


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


@app.on_event("startup")
async def _startup() -> None:
    # Warm up the sole agent on startup
    app.state.super_agent = get_super_agent()
    logging.getLogger("uvicorn.error").info("SuperAgent loaded: %s", app.state.super_agent.name)

    # TTL session store to persist conversation state between requests with eviction
    class SessionStore:
        def __init__(self, ttl_seconds: int = 60 * 60, max_sessions: int = 200) -> None:
            self._ttl = ttl_seconds
            self._max = max_sessions
            self._sessions: Dict[str, Tuple[SQLiteSession, float]] = {}
            self._lock = asyncio.Lock()
            self._janitor_task: Optional[asyncio.Task] = None

        async def start(self) -> None:
            if self._janitor_task is None:
                self._janitor_task = asyncio.create_task(self._janitor())

        async def stop(self) -> None:
            if self._janitor_task is not None:
                self._janitor_task.cancel()
                try:
                    await self._janitor_task
                except Exception:
                    pass
                self._janitor_task = None
            async with self._lock:
                self._sessions.clear()

        async def get_or_create(self, key: str, factory: Callable[[], SQLiteSession]) -> SQLiteSession:
            now = time.time()
            async with self._lock:
                entry = self._sessions.get(key)
                if entry is not None:
                    sess, _ = entry
                    self._sessions[key] = (sess, now)
                    return sess
                # Evict if over capacity (LRU based on last used)
                if len(self._sessions) >= self._max:
                    # sort by last_used asc
                    oldest_key = min(self._sessions.items(), key=lambda kv: kv[1][1])[0]
                    self._sessions.pop(oldest_key, None)
                sess = factory()
                self._sessions[key] = (sess, now)
                return sess

        async def _janitor(self) -> None:
            try:
                while True:
                    await asyncio.sleep(60)
                    cutoff = time.time() - self._ttl
                    async with self._lock:
                        to_delete = [k for k, (_, ts) in self._sessions.items() if ts < cutoff]
                        for k in to_delete:
                            self._sessions.pop(k, None)
            except asyncio.CancelledError:
                return

    store = SessionStore()
    app.state.session_store = store
    await store.start()


@app.on_event("shutdown")
async def _shutdown() -> None:
    store = getattr(app.state, "session_store", None)
    if store is not None:
        try:
            await store.stop()
        except Exception:
            pass

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}

@app.get("/agent")
async def agent_info() -> Dict[str, Any]:
    ag = getattr(app.state, "super_agent", None)
    if ag is None:
        ag = get_super_agent()
        app.state.super_agent = ag
    # Try to show a short preview of instructions
    preview = ""
    try:
        text = getattr(ag, "instructions", "") or ""
        preview = text[:240]
    except Exception:
        preview = ""
    return {"name": getattr(ag, "name", ""), "instructions_preview": preview}


@app.get("/reports/{filename}")
async def get_report(filename: str):
    """Serve a generated report (Word doc) for download."""
    # Security: no path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Support both .docx and .pdf for backwards compatibility
    if not (filename.endswith(".docx") or filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are supported")
    
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
            "Content-Disposition": f"attachment; filename=\"{filename}\"",  # attachment for download
        }
    )


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
    return {
        "templates": [t.to_dict() for t in templates],
        "count": len(templates)
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

@app.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    agent = getattr(app.state, "super_agent", get_super_agent())

    session_id = (req.session_id or "web").strip()
    store = getattr(app.state, "session_store", None)
    if store is None:
        # Fallback to direct session creation if store not initialized for any reason
        session = SQLiteSession(session_id)
    else:
        session = await store.get_or_create(session_id, lambda: SQLiteSession(session_id))

    try:
        logging.getLogger("uvicorn.error").info("/api/chat using agent=SuperAgent session=%s", session_id)
        result = await Runner.run(agent, req.message.strip(), session=session)
    except KeyError as e:
        # Common when missing required env variables
        raise HTTPException(status_code=500, detail=f"Missing environment variable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "final_output": result.final_output,
    }


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    agent = getattr(app.state, "super_agent", get_super_agent())

    session_id = (req.session_id or "web").strip()
    store = getattr(app.state, "session_store", None)
    if store is None:
        session = SQLiteSession(session_id)
    else:
        session = await store.get_or_create(session_id, lambda: SQLiteSession(session_id))

    async def event_stream():
        # announce start
        yield f"data: {json.dumps({"type": "start", "session_id": session_id})}\n\n"
        try:
            # use true streaming from the agents Runner
            streamed = Runner.run_streamed(
                agent,
                input=req.message.strip(),
                session=session,
            )

            last_event_time = asyncio.get_event_loop().time()
            async for ev in streamed.stream_events():
                # Raw response deltas → token text
                if getattr(ev, "type", None) == "raw_response_event":
                    data = getattr(ev, "data", None)
                    if ResponseTextDeltaEvent is not None and isinstance(data, ResponseTextDeltaEvent):
                        delta = getattr(data, "delta", None)
                        if isinstance(delta, str) and delta:
                            yield f"data: {json.dumps({"type": "delta", "content": delta})}\n\n"
                    # Ignore all other raw delta event types (e.g., tool call argument deltas)
                # Agent updates (handoffs)
                elif getattr(ev, "type", None) == "agent_updated_stream_event":
                    new_agent = getattr(ev, "new_agent", None)
                    name = getattr(new_agent, "name", "") if new_agent is not None else ""
                    yield f"data: {json.dumps({"type": "agent", "name": name})}\n\n"
                # Run item events (tool calls, messages)
                elif getattr(ev, "type", None) == "run_item_stream_event":
                    item = getattr(ev, "item", None)
                    item_type = getattr(item, "type", "")
                    if item_type:
                        yield f"data: {json.dumps({"type": "item", "item_type": item_type})}\n\n"

                # occasional heartbeat to keep connections warm
                now = asyncio.get_event_loop().time()
                if now - last_event_time > 1.0:
                    yield "data: {\"type\": \"ping\"}\n\n"
                    last_event_time = now

            # done
            yield "data: {\"type\": \"done\"}\n\n"
        except KeyError as e:
            err = {"type": "error", "message": f"Missing environment variable: {e}"}
            yield f"data: {json.dumps(err)}\n\n"
        except Exception as e:
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)


