# AI Workbench 架构设计

## 目标与边界

AI Workbench 是个人学习和作品展示项目。阶段 1 只实现单 Agent、工具调用和会话记录；不包含登录、多用户隔离、生产级代码沙箱或 RAG。

## 分层

```text
React/Vite UI
    -> REST API (FastAPI)
    -> application services
    -> Agent + model adapters + tool registry
    -> repositories (SQLAlchemy)
    -> SQLite (MVP) / PostgreSQL (later)
```

- `api`：路由、鉴权前置、请求/响应 schema。
- `services`：会话和消息用例，协调 Agent 与持久化。
- `agent`：提示词、Agent 状态和执行步骤摘要，不输出隐式思维链。
- `models`：统一 `chat(messages, tools, options)` 接口及 OpenAI 兼容/Ollama 适配器。
- `tools`：Pydantic 输入模型、执行器、超时和安全策略。
- `repositories`/`db`：SQLAlchemy 模型、会话管理和迁移边界。
- `core`：配置、日志、异常和响应封装。

## 一次消息流程

1. API 校验 `content`、`model_id` 和选项。
2. 会话服务创建用户消息并读取历史。
3. Agent 请求模型决定直接回答或调用工具。
4. 工具注册中心校验参数、执行并记录状态、输出和耗时。
5. Agent 使用工具结果生成最终答案。
6. 服务保存助手消息和结构化 `steps`，API 返回统一响应。

## 数据关系

`sessions 1--N messages 1--N tool_calls`。工具输入输出保存为 JSON；敏感信息、密钥和完整思考过程永不持久化。

## 演进策略

SQLite 与 PostgreSQL 通过 SQLAlchemy URL 切换；API 和 service 层不感知数据库类型。阶段 3 增加 pgvector，阶段 4 在 Agent service 外围引入 LangGraph 状态图。
