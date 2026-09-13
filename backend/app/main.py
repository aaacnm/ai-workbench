from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from uuid import uuid4
from app.tools import build_registry
from app.tools.calculator import CalculatorInput
from app.tools.time_tool import TimeInput
from app.tools.file_tool import FileInput
from app.tools.search_tool import SearchInput
from app.tools.code_tool import CodeInput
from app.tools.weather_tool import WeatherInput
from app.agent.service import AgentService
from app.models.factory import create_model
from app.models.openai_compatible import OpenAICompatibleModel
from app.models.registry import ModelRegistry, RegisteredModel
from app.core.config import load_model_configs
from app.models.runtime_config import RuntimeModelUpdate, runtime_model_state, update_runtime_model
from app.db.database import Base, SessionLocal, engine
from app.db.models import SessionModel, MessageModel, DocumentModel
from app.knowledge import create_document, search_documents, vector_search_documents, retrieve_relevant_documents
from app.db.config_store import StoredModelConfig, load_config, save_config, clear_config, list_configs
from pathlib import Path
import re
from app.core.logging import request_logging_middleware


def ensure_schema():
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        from sqlalchemy import inspect, text
        if not inspect(engine).has_table("document_chunks"):
            return
        columns = {column["name"] for column in inspect(engine).get_columns("document_chunks")}
        additions = {"embedding": "JSON", "embedding_model": "VARCHAR(80) DEFAULT 'local-hash-v2'", "embedding_dim": "INTEGER DEFAULT 32"}
        with engine.begin() as connection:
            for name, definition in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE document_chunks ADD COLUMN {name} {definition}"))

@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema()
    yield

app = FastAPI(title="AI Workbench API", version="0.1.0", lifespan=lifespan)
ensure_schema()
try:
    persisted_config = load_config()
except RuntimeError:
    persisted_config = None
if persisted_config:
    update_runtime_model(RuntimeModelUpdate(**persisted_config))
app.middleware("http")(request_logging_middleware)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

workspace_root = Path(__file__).resolve().parents[3] / "data" / "workspace"
tool_registry = build_registry(workspace_root)
model_name, chat_model = create_model()
model_registry = ModelRegistry()
if runtime_model_state.provider != "mock":
    model_name = runtime_model_state.provider
    chat_model = OpenAICompatibleModel(runtime_model_state.model_name, runtime_model_state.base_url, None if runtime_model_state.provider == "ollama" else "OPENAI_API_KEY", runtime_model_state.timeout_seconds, runtime_model_state.temperature, runtime_model_state.max_tokens)
    model_registry = ModelRegistry([RegisteredModel(load_model_configs()[0], chat_model)])
agent_service = AgentService(tool_registry, chat_model, model_name)

class SessionCreate(BaseModel):
    title: str = "新会话"

class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    model: str = "mock"
    model_id: str | None = None

class DocumentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=200_000)

def ok(data):
    return {"success": True, "data": data, "error": None}

@app.get("/api/v1/health")
def health():
    return ok({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.post("/api/v1/documents")
def create_document_endpoint(payload: DocumentCreate):
    with SessionLocal() as db:
        try:
            document = create_document(db, payload.filename, payload.content)
        except ValueError as exc:
            return {"success": False, "data": None, "error": {"code": "DOCUMENT_INVALID", "message": str(exc)}}
        return ok({"id": document.id, "filename": document.filename, "chunk_count": len(document.chunks)})

@app.post("/api/v1/documents/upload")
async def upload_document_endpoint(request: Request, filename: str = Query(min_length=1, max_length=255)):
    if Path(filename).suffix.lower() not in {".txt", ".md"}:
        return {"success": False, "data": None, "error": {"code": "DOCUMENT_TYPE_UNSUPPORTED", "message": "only .txt and .md files are supported"}}
    raw = await request.body()
    if len(raw) > 1_000_000:
        return {"success": False, "data": None, "error": {"code": "DOCUMENT_TOO_LARGE", "message": "file exceeds 1 MB"}}
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return {"success": False, "data": None, "error": {"code": "DOCUMENT_ENCODING_INVALID", "message": "file must be UTF-8"}}
    with SessionLocal() as db:
        if not content.strip():
            return {"success": False, "data": None, "error": {"code": "DOCUMENT_INVALID", "message": "file content is empty"}}
        document = create_document(db, filename, content)
        return ok({"id": document.id, "filename": document.filename, "chunk_count": len(document.chunks)})

@app.get("/api/v1/documents")
def list_documents():
    with SessionLocal() as db:
        rows = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
        return ok([{"id": row.id, "filename": row.filename, "chunk_count": len(row.chunks), "created_at": row.created_at.isoformat()} for row in rows])

@app.get("/api/v1/documents/search")
def search_documents_endpoint(q: str = Query(min_length=1, max_length=500), limit: int = Query(default=5, ge=1, le=50), mode: Literal["keyword", "vector"] = "keyword"):
    with SessionLocal() as db:
        try:
            if mode == "keyword":
                results = search_documents(db, q, limit)
            elif mode == "vector":
                results = vector_search_documents(db, q, limit)
            else:
                raise ValueError("mode must be keyword or vector")
            return ok(results)
        except ValueError as exc:
            return {"success": False, "data": None, "error": {"code": "DOCUMENT_SEARCH_INVALID", "message": str(exc)}}

@app.get("/api/v1/documents/{document_id}")
def get_document(document_id: str):
    with SessionLocal() as db:
        row = db.get(DocumentModel, document_id)
        if row is None:
            return {"success": False, "data": None, "error": {"code": "DOCUMENT_NOT_FOUND", "message": "document not found"}}
        return ok({"id": row.id, "filename": row.filename, "chunks": [{"index": chunk.chunk_index, "content": chunk.content, "metadata": chunk.metadata_json or {}, "embedding_model": chunk.embedding_model, "embedding_dimensions": chunk.embedding_dim} for chunk in row.chunks]})

@app.delete("/api/v1/documents/{document_id}")
def delete_document(document_id: str):
    with SessionLocal() as db:
        row = db.get(DocumentModel, document_id)
        if row is None:
            return {"success": False, "data": None, "error": {"code": "DOCUMENT_NOT_FOUND", "message": "document not found"}}
        db.delete(row)
        db.commit()
        return ok({"deleted": True, "id": document_id})

@app.get("/api/v1/models")
def models():
    return ok([{"id": entry.config.id, "name": entry.config.model_name, "provider": entry.config.provider, "available": True, "supports_tools": entry.config.supports_tools, "local": entry.config.local} for entry in model_registry.list()])

@app.get("/api/v1/models/{model_id}/status")
def model_status(model_id: str):
    try:
        return ok(model_registry.status(model_id))
    except KeyError:
        return {"success": False, "data": None, "error": {"code": "MODEL_NOT_FOUND", "message": f"模型不存在: {model_id}"}}

@app.get("/api/v1/config/model")
def get_model_config():
    return ok(runtime_model_state.summary())

@app.get("/api/v1/config/models")
def get_model_configs():
    return ok(list_configs())

@app.get("/api/v1/config/models/{provider}/{model_name}")
def get_saved_model_config(provider: str, model_name: str):
    config = load_config(provider, model_name)
    if config is None:
        return {"success": False, "data": None, "error": {"code": "CONFIG_NOT_FOUND", "message": "模型配置不存在"}}
    config.pop("api_key", None)
    config["api_key_configured"] = bool(load_config(provider, model_name) and load_config(provider, model_name).get("api_key"))
    return ok(config)

@app.delete("/api/v1/config/models/{provider}/{model_name}")
def delete_saved_model_config(provider: str, model_name: str):
    from app.db.config_store import delete_config
    delete_config(provider, model_name)
    return ok({"deleted": True, "provider": provider, "model_name": model_name})

@app.post("/api/v1/config/model")
def set_model_config(payload: RuntimeModelUpdate):
    global model_registry, model_name, chat_model, agent_service
    summary = update_runtime_model(payload)
    try:
        if payload.api_key:
            save_config({**payload.model_dump(), "api_key": runtime_model_state.api_key})
    except RuntimeError as exc:
        return {"success": False, "data": None, "error": {"code": "CONFIG_ENCRYPTION_ERROR", "message": str(exc)}}
    model_name, chat_model = create_model()
    model_registry = ModelRegistry()
    agent_service = AgentService(tool_registry, chat_model, model_name)
    return ok(summary)

@app.delete("/api/v1/config/model")
def delete_model_config():
    global model_registry, model_name, chat_model, agent_service
    clear_config(runtime_model_state.provider, runtime_model_state.model_name)
    runtime_model_state.provider = "mock"
    runtime_model_state.model_name = "mock"
    runtime_model_state.base_url = None
    runtime_model_state.api_key = None
    for key in ("MODEL_PROVIDER", "MODEL_NAME", "MODEL_BASE_URL", "OPENAI_API_KEY"):
        import os
        os.environ.pop(key, None)
    model_name, chat_model = create_model()
    model_registry = ModelRegistry()
    agent_service = AgentService(tool_registry, chat_model, model_name)
    return ok({"cleared": True, "provider": "mock"})

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

@app.post("/api/v1/tools/weather")
def weather_tool(payload: WeatherInput):
    try:
        return ok(tool_registry.execute("weather", payload.model_dump()))
    except ValueError as exc:
        return {"success": False, "data": None, "error": {"code": "WEATHER_TOOL_ERROR", "message": str(exc)}}

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
        selected_model_id = payload.model_id or payload.model
        try:
            selected = model_registry.get(selected_model_id)
        except KeyError:
            return {"success": False, "data": None, "error": {"code": "MODEL_NOT_FOUND", "message": f"模型不存在: {selected_model_id}"}}
        session = db.get(SessionModel, session_id)
        if session is None:
            return {"success": False, "data": None, "error": {"code": "SESSION_NOT_FOUND", "message": "session not found"}}
        selected_chat_model = selected.model
        # Deterministic tool intents should not be polluted by unrelated knowledge chunks.
        arithmetic_intent = bool(re.search(r"(?<![\w-])\d+(?:\s*[+\-*/%]\s*\d+)+(?![\w-])", payload.content))
        utility_intent = arithmetic_intent or any(word in payload.content for word in ("时间", "几点", "日期", "天气", "气温", "温度"))
        knowledge_hits = [] if utility_intent else retrieve_relevant_documents(db, payload.content, 3)
        knowledge_context = "\n\n".join(f"[{hit['filename']}#{hit['chunk_index']}] {hit['content']}" for hit in knowledge_hits)
        agent_prompt = payload.content
        if knowledge_context and selected.config.provider != "mock":
            agent_prompt = f"[KNOWLEDGE_CONTEXT]\n{knowledge_context}\n[QUESTION]\n{payload.content}"
        selected_agent = AgentService(tool_registry, selected_chat_model, selected.config.id)
        try:
            if utility_intent:
                deterministic = selected_agent.run(payload.content)
                if selected.config.provider != "mock" and selected_chat_model is not None:
                    history = db.query(MessageModel).filter(MessageModel.session_id == session_id).order_by(MessageModel.created_at.desc()).limit(6).all()
                    messages = [{"role": "system", "content": "Rewrite the supplied tool result into a concise, accurate answer. Do not change numeric or factual values."}]
                    messages.extend({"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in reversed(history))
                    messages.append({"role": "user", "content": f"Question: {payload.content}\nTool result: {deterministic.answer}"})
                    model_response = selected_chat_model.chat(messages, [])
                    agent_response = type(deterministic)(model_response.content or deterministic.answer, deterministic.steps, selected.config.id)
                else:
                    agent_response = deterministic
            elif selected.config.provider != "mock":
                history_rows = db.query(MessageModel).filter(MessageModel.session_id == session_id).order_by(MessageModel.created_at.desc()).limit(6).all()
                history = [{"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in reversed(history_rows)]
                if knowledge_context:
                    agent_response = selected_agent.run_with_model(agent_prompt)
                else:
                    agent_response = selected_agent.run_with_model(agent_prompt, history=history)
            elif knowledge_hits:
                top = knowledge_hits[0]
                agent_response = selected_agent.run(payload.content)
                agent_response.answer = f"根据知识库，{top['content']}（来源：{top['filename']}）"
            else:
                agent_response = selected_agent.run(payload.content)
        except RuntimeError as exc:
            return {"success": False, "data": None, "error": {"code": "MODEL_REQUEST_ERROR", "message": str(exc)}}
        if knowledge_hits:
            agent_response.steps.insert(0, {"type": "knowledge_retrieval", "query": payload.content, "results": [{"filename": hit["filename"], "chunk_index": hit["chunk_index"], "score": hit["score"]} for hit in knowledge_hits]})
        elif utility_intent:
            reason = "arithmetic_intent" if arithmetic_intent else "utility_tool_intent"
            agent_response.steps.insert(0, {"type": "retrieval_skipped", "query": payload.content, "reason": reason})
        db.add(MessageModel(session_id=session_id, role="user", content=payload.content))
        assistant = MessageModel(session_id=session_id, role="assistant", content=agent_response.answer, steps=agent_response.steps)
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return ok({"session_id": session_id, "message_id": assistant.id, "answer": agent_response.answer, "model": agent_response.model, "steps": agent_response.steps})
