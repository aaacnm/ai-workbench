# AI Workbench 项目状态

## 当前阶段

阶段 2：模型配置中心已完成，准备进入阶段 3（知识库和 RAG）。

## 已完成

- FastAPI 后端和 React/Vite 前端
- 数学、时间、文件、Mock 搜索、天气工具
- 默认关闭的受限代码工具
- ToolRegistry 工具注册中心
- 规则型 Agent 和模型工具调用循环
- SQLite 会话与消息持久化
- OpenAI 兼容模型适配器
- OpenAI、DeepSeek、通义千问、智谱、Ollama 配置预设
- 前端模型选择和配置面板
- 多供应商/多模型配置 profile
- API Key Fernet 加密持久化
- 模型状态检查、配置清除和重试机制
- 请求 ID、请求耗时和统一响应结构
- 测试环境 Mock 隔离

## 当前验证

- 后端测试：通过（最近一次 45 passed；新增天气功能后需重新运行完整测试）
- 前端生产构建：通过
- 真实 OpenAI 兼容中转站：已验证 `gpt-5.6-sol`
- 当前默认不应提交：`.env`、数据库、pytest 临时目录、`prompt.txt`、`最终方案.txt`

## 配置说明

- 本地配置文件：`backend/.env`
- API Key：仅在后端使用，数据库中以 Fernet 密文保存
- `CONFIG_ENCRYPTION_KEY`：必须保密，丢失后无法解密已保存 API Key
- 测试通过 `tests/conftest.py` 强制使用 Mock，不访问真实模型

## 下一步

1. 重新运行天气工具后的完整测试。
2. 提交阶段 2 收尾代码到 GitHub。
3. 进入阶段 3：文档上传、解析、切分、向量化和检索。

## 已知限制

- 运行时配置目前支持单个当前模型实例，多 profile 已保存但尚未做多模型并行管理。
- 向量数据库、用户认证、生产级代码沙箱和流式响应尚未实现。
