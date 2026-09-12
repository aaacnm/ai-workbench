# AI Workbench

面向个人学习与作品展示的 AI Agent 工作台，按“工具调用 -> RAG -> 多 Agent -> 工作流”渐进迭代。

## 当前状态

阶段 1 已完成核心 MVP：单 Agent 工具调用、SQLite 会话持久化、模型适配层、前后端联调和执行步骤展示。

已实现工具：当前时间、数学计算、Mock 搜索、工作目录文件读取、默认关闭的受限代码执行。

## 本地运行

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

另开终端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

访问前端 http://localhost:5173，API 文档位于 http://127.0.0.1:8000/docs。

## 阶段 1 验收

```powershell
cd backend
python -m pytest tests -q --basetemp .pytest-temp -p no:cacheprovider
```

预期所有测试通过。浏览器中分别测试：`请计算 2 + 3 * 4`、`查询北京时间`、`搜索 FastAPI`，确认回答和工具步骤出现。会话和消息保存于 `backend/ai_workbench.db`。

## 配置

复制 `backend/.env.example` 为 `.env`。默认使用离线 Mock/规则型 Agent，不需要 API Key。真实 OpenAI 兼容模型需要配置 `MODEL_PROVIDER`、`MODEL_NAME`、`OPENAI_API_KEY` 和可选的 `OPENAI_BASE_URL`。

代码工具默认关闭；仅本地演示时显式设置 `ENABLE_CODE_TOOL=true`，不适合生产环境。

## 设计文档

- [架构设计](docs/architecture.md)
- [API 契约](docs/api.md)
- [开发路线图](docs/roadmap.md)
