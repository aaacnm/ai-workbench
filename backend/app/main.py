from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from uuid import uuid4

app = FastAPI(title="AI Workbench API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

sessions: dict[str, list[dict]] = {}

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
    return ok([{"id": "mock", "name": "Mock Model", "provider": "local", "available": True}])

@app.get("/api/v1/tools")
def tools():
    return ok([
        {"id": "time", "name": "当前时间", "status": "planned"},
        {"id": "calculator", "name": "数学计算", "status": "planned"},
        {"id": "search", "name": "网络搜索", "status": "planned"},
        {"id": "file", "name": "文件读取", "status": "planned"},
        {"id": "code", "name": "受限代码执行", "status": "planned"},
    ])

@app.get("/api/v1/sessions")
def list_sessions():
    return ok([{"id": sid, "title": msgs[0].get("title", "新会话") if msgs else "新会话", "message_count": len(msgs)} for sid, msgs in sessions.items()])

@app.post("/api/v1/sessions")
def create_session(payload: SessionCreate):
    sid = str(uuid4())
    sessions[sid] = [{"title": payload.title}]
    return ok({"id": sid, "title": payload.title, "messages": []})

@app.get("/api/v1/sessions/{session_id}")
def get_session(session_id: str):
    messages = sessions.get(session_id, [])
    return ok({"id": session_id, "messages": [m for m in messages if "role" in m]})

@app.post("/api/v1/sessions/{session_id}/messages")
def send_message(session_id: str, payload: MessageCreate):
    if session_id not in sessions:
        sessions[session_id] = [{"title": "新会话"}]
    answer = "这是初始化阶段的演示回复。下一步将接入 Agent 和工具调用。"
    sessions[session_id].extend([{"role": "user", "content": payload.content}, {"role": "assistant", "content": answer, "steps": []}])
    return ok({"session_id": session_id, "answer": answer, "model": payload.model, "steps": []})
