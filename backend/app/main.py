from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from uuid import uuid4
from app.tools import build_registry
from app.tools.calculator import CalculatorInput
from app.tools.time_tool import TimeInput
from app.tools.file_tool import FileInput
from app.tools.search_tool import SearchInput
from app.tools.code_tool import CodeInput
from app.agent.service import AgentService
from app.models.factory import create_model
from app.db.database import Base, SessionLocal, engine
from app.db.models import SessionModel, MessageModel
from pathlib import Path
from app.core.logging import request_logging_middleware

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="AI Workbench API", version="0.1.0", lifespan=lifespan)
app.middleware("http")(request_logging_middleware)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

workspace_root = Path(__file__).resolve().parents[3] / "data" / "workspace"
tool_registry = build_registry(workspace_root)
model_name, chat_model = create_model()
agent_service = AgentService(tool_registry, chat_model, model_name)

class SessionCreate(BaseModel):
    title: str = "新会话"

class MessageCreate(BaseModel):
    content: str
    model: str = "mock"

def ok(data):
    return {"success": True, "data": data, "error": None}

@app.get("/api/v1/health")
def health():
    return ok({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.get("/api/v1/models")
def models():
    return ok([{"id": model_name, "name": model_name, "provider": model_name, "available": True}])

@app.get("/api/v1/tools")
def tools():
    return ok([
        {"id": "time", "name": "当前时间", "status": "available"},
        {"id": "calculator", "name": "数学计算", "status": "available"},
        {"id": "search", "name": "网络搜索（Mock）", "status": "available"},
        {"id": "file", "name": "文件读取", "status": "available"},
        {"id": "code", "name": "受限代码执行（默认关闭）", "status": "available"},
    ])

@app.post("/api/v1/tools/calculator")
def calculator(payload: CalculatorInput):
    try:
        result = tool_registry.execute("calculator", payload.model_dump())
    except ValueError as exc:
        return {"success": False, "data": None, "error": {"code": "CALCULATOR_ERROR", "message": str(exc)}}
    return ok(result)

@app.post("/api/v1/tools/time")
def time_tool(payload: TimeInput):
    try:
        result = tool_registry.execute("time", payload.model_dump())
    except ValueError as exc:
        return {"success": False, "data": None, "error": {"code": "TIME_TOOL_ERROR", "message": str(exc)}}
    return ok(result)

@app.post("/api/v1/tools/file")
def file_tool(payload: FileInput):
    try:
        result = tool_registry.execute("file", payload.model_dump())
    except ValueError as exc:
        return {"success": False, "data": None, "error": {"code": "FILE_TOOL_ERROR", "message": str(exc)}}
    return ok(result)

@app.post("/api/v1/tools/search")
def search_tool(payload: SearchInput):
    result = tool_registry.execute("search", payload.model_dump())
    result["provider"] = "mock"
    return ok(result)

@app.post("/api/v1/tools/code")
def code_tool(payload: CodeInput):
    try:
        result = tool_registry.execute("code", payload)
    except ValueError as exc:
        return {"success": False, "data": None, "error": {"code": "CODE_TOOL_ERROR", "message": str(exc)}}
    return ok(result)

@app.get("/api/v1/sessions")
def list_sessions():
    with SessionLocal() as db:
        rows = db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()
        return ok([{"id": row.id, "title": row.title, "message_count": len(row.messages)} for row in rows])

@app.post("/api/v1/sessions")
def create_session(payload: SessionCreate):
    with SessionLocal() as db:
        row = SessionModel(title=payload.title, model_id=model_name)
        db.add(row)
        db.commit()
        db.refresh(row)
        return ok({"id": row.id, "title": row.title, "messages": []})

@app.get("/api/v1/sessions/{session_id}")
def get_session(session_id: str):
    with SessionLocal() as db:
        row = db.get(SessionModel, session_id)
        if row is None:
            return {"success": False, "data": None, "error": {"code": "SESSION_NOT_FOUND", "message": "会话不存在"}}
        return ok({"id": row.id, "messages": [{"id": m.id, "role": m.role, "content": m.content, "steps": m.steps or []} for m in row.messages]})

@app.post("/api/v1/sessions/{session_id}/messages")
def send_message(session_id: str, payload: MessageCreate):
    with SessionLocal() as db:
        session = db.get(SessionModel, session_id)
        if session is None:
            session = SessionModel(id=session_id, title="新会话", model_id=model_name)
            db.add(session)
        agent_response = agent_service.run_with_model(payload.content) if model_name != "mock" else agent_service.run(payload.content)
        db.add(MessageModel(session_id=session_id, role="user", content=payload.content))
        assistant = MessageModel(session_id=session_id, role="assistant", content=agent_response.answer, steps=agent_response.steps)
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return ok({"session_id": session_id, "message_id": assistant.id, "answer": agent_response.answer, "model": agent_response.model, "steps": agent_response.steps})
