# API 契约

基础地址：`http://127.0.0.1:8000/api/v1`。

所有响应格式：

```json
{"success": true, "data": {}, "error": null}
```

错误格式：`error` 包含 `code`、`message`，可选 `details`。

## 端点

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health` | 服务状态 |
| GET | `/models` | 可用模型 |
| GET | `/tools` | 工具目录和状态 |
| GET | `/sessions` | 会话列表 |
| POST | `/sessions` | 创建会话，Body `{title?}` |
| GET | `/sessions/{id}` | 会话消息和步骤 |
| POST | `/sessions/{id}/messages` | 发送消息 |

发送消息 Body：

```json
{"content":"查询当前时间","model_id":"mock","options":{}}
```

响应 `data`：

```json
{"session_id":"...","message_id":"...","answer":"...","model_id":"mock","steps":[{"type":"tool_call","tool_name":"time","input":{},"output":"...","status":"success","duration_ms":12}]}
```

状态码：参数错误 `422`，资源不存在 `404`，工具/模型超时 `504`，未知错误 `500`。
