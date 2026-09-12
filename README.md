# AI Workbench

面向个人学习与作品展示的 AI Agent 工作台，按“工具调用 -> RAG -> 多 Agent -> 工作流”渐进迭代。

## 当前状态

阶段 0 初始化设计：FastAPI 后端、React/Vite 前端、统一响应结构和本地演示会话。Agent、真实模型和工具将在阶段 1 按小功能接入。

## 设计文档

- [架构设计](docs/architecture.md)
- [API 契约](docs/api.md)
- [开发路线图](docs/roadmap.md)

## 项目结构

`backend/app` 按 api、services、agent、tools、models、repositories、db、schemas、core 分层；`frontend/src` 按 api、types、components、pages、hooks 拆分；`data/workspace` 是文件工具允许访问的工作目录。

## 阶段 0 验收

1. 后端 `/api/v1/health` 返回 `success: true`。
2. `/docs` 可打开并显示 API。
3. 前端可启动并展示对话工作台。
4. 配置通过 `.env` 注入，仓库不提交密钥。

## 本地运行

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

另开终端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

打开 http://localhost:5173，API 文档位于 http://127.0.0.1:8000/docs。
