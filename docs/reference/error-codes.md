---
last_updated: 2026-06-03 15:33:51 +08:00
status: active
owner: @Evan-AFeng
---

# 错误码

后端错误响应统一使用如下结构：

```json
{
  "code": "INVALID_REQUEST",
  "message": "question is required",
  "detail": {}
}
```

## 通用错误码

| 错误码 | HTTP 状态码 | 说明 |
| --- | --- | --- |
| `INVALID_REQUEST` | 400 | 请求参数缺失或格式错误 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | HTTP 方法不允许 |
| `INTERNAL_ERROR` | 500 | 未预期的服务端错误 |

## 查询错误码

| 错误码 | HTTP 状态码 | 说明 |
| --- | --- | --- |
| `NL2SQL_FAILED` | 422 | 自然语言转 SQL 失败 |
| `SQL_VALIDATE_FAILED` | 422 | SQL 校验失败 |
| `SQL_EXECUTE_FAILED` | 500 | SQL 执行失败 |
| `DATABASE_UNAVAILABLE` | 503 | 数据库不可用 |
| `DATABASE_IMPORT_FAILED` | 422 | SQLite 数据库导入失败 |

## 使用约定

- `message` 面向前端展示，应简短明确。
- `detail` 用于调试上下文，不应包含敏感信息。
- 新增错误码时需要同步更新 API 文档和相关测试。
