# 开发路线图

## 阶段 0：初始化设计

目标：完成架构、API 契约、配置和可启动前后端骨架。验收：健康接口、Swagger、前端页面和文档均可访问。

## 阶段 1：工具调用 MVP

目标：接入一个真实或本地模型，实现时间、计算、Mock 搜索、受限文件读取和默认关闭的代码工具。验收：工具结果影响答案，步骤和会话可刷新查看，安全测试通过。

## 阶段 2：模型配置中心

目标：供应商适配器、模型参数和环境变量配置。验收：无需改业务代码即可切换 OpenAI 兼容供应商或 Ollama。

当前完成：前端配置面板、模型下拉选择、运行时切换、API Key Fernet 加密持久化、请求重试、模型状态接口、真实 OpenAI 兼容中转站联调。

## 阶段 3：知识库/RAG

目标：文档解析、切分、向量化、pgvector 检索和来源引用。验收：上传文档后可检索并回答，结果带来源。

## 阶段 4：多 Agent/工作流

目标：使用 LangGraph 编排规划、执行、审查节点。验收：状态流转可追踪，失败节点可重试。

## 阶段 5：工程化部署

目标：Docker Compose、PostgreSQL、结构化日志、监控、性能和成本优化。验收：全新环境按 README 一条路径启动并通过测试。

每阶段拆成可独立验收的小功能，完成后再进入下一阶段。
### Deferred Engineering Allocation

Stage 4: real embedding providers, VectorStore abstraction, retrieval token budgets, atomic runtime model state, concurrency tests, and stronger multi-turn context management.

Stage 5: Alembic migrations, PostgreSQL/pgvector, SQLite WAL/foreign keys, standard multipart uploads and PDF parsing, HTTP error status normalization, authentication/document ownership, streaming, monitoring, Docker deployment, and performance/cost optimization.
## Next Session Start Point

Begin Stage 4 with retrieval quality: connect the embedding provider boundary, introduce a VectorStore interface, and add relevance-quality tests before changing storage infrastructure.
