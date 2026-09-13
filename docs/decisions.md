# 架构决策记录

## ADR-001：前端使用 React + TypeScript + Vite

适合作品展示，前后端边界清晰，便于后续扩展知识库和工作流界面。

## ADR-002：阶段 1 使用 SQLite

本地启动简单，测试成本低；通过 SQLAlchemy 保留迁移 PostgreSQL 的边界。

## ADR-003：阶段 1 使用 LangChain 前的轻量 Agent 骨架

先验证工具注册、执行步骤和消息协议，再引入外部 Agent 编排依赖，降低早期复杂度。

## ADR-004：API Key 使用 Fernet 加密

API Key 不明文写入数据库、前端或日志。加密主密钥通过环境变量提供。

## ADR-005：模型供应商统一采用 ChatModel 接口

OpenAI 兼容供应商复用 HTTP 适配器，Ollama 保持同一调用契约，业务层不感知供应商差异。

## ADR-006：工具执行统一经过 ToolRegistry

集中处理工具发现、Pydantic 输入校验和统一输出，Agent 不直接依赖具体工具函数。

## ADR-007：前端不展示隐式思维链

只展示执行步骤摘要、工具输入输出、状态和最终答案，避免暴露模型内部推理过程。
