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


