# RunoobSQL Harness

轻量级 NL2SQL 问数平台，基于 Flask、Vue 3、SQLite 和 OpenAI-compatible 大模型接口。

当前支持：

- 导入本地 SQLite 数据库文件。
- 根据用户自然语言问题生成只读 SQL。
- 执行 SQL 并返回结果表格。
- 通过 SSE 实时返回模型输出，支持展示模型显式返回的 `<think>...</think>` 内容。

## 目录结构

```text
backend/                 Flask 后端
  app/routes/            HTTP API
  app/services/          业务逻辑
  app/configs/           大模型等配置
  tests/                 后端单元测试
frontend/                Vue 3 + Vite 前端
docs/                    架构、规范、API 文档
tools/custom_linters/    项目自定义 linter
project_demo.db          示例 SQLite 数据库
```

## 环境准备

安装后端依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

安装前端依赖：

```powershell
cd frontend
npm.cmd install
cd ..
```

## 大模型配置

默认使用阿里云百炼 OpenAI-compatible 接口：

```powershell
$env:RUNOOBSQL_LLM_API_KEY="你的百炼 API Key"
```

可选覆盖项：

```powershell
$env:RUNOOBSQL_LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:RUNOOBSQL_LLM_MODEL="qwen-plus"
$env:RUNOOBSQL_LLM_TIMEOUT_SECONDS="30"
```

## 启动

开两个终端。

后端：

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

前端：

```powershell
cd frontend
npm.cmd run dev
```

访问：

```text
http://127.0.0.1:5173/
```

前端会把 `/api` 代理到 `http://127.0.0.1:5000`。

## 后端接口验证

健康检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/api/health
```

导入示例数据库：

```powershell
$response = Invoke-RestMethod `
  -Uri http://127.0.0.1:5000/api/databases/import `
  -Method Post `
  -Form @{ file = Get-Item .\project_demo.db }

$databaseId = $response.database_id
$response
```

普通查询：

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:5000/api/query `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    database_id = $databaseId
    question = "已完成项目"
  } | ConvertTo-Json)
```

SSE 流式查询：

```powershell
curl.exe -N "http://127.0.0.1:5000/api/query/stream?database_id=$databaseId&question=已完成项目"
```

SSE 事件类型：

- `model_delta`：模型流式输出片段，可能包含 `<think>...</think>`。
- `sql`：后端解析出的最终 SQL。
- `result`：SQL 执行结果。
- `error`：错误信息。
- `done`：流式响应结束。

## SQL 安全边界

后端只允许只读查询：

- 允许：`SELECT`、`WITH`
- 拒绝：多语句、`INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`PRAGMA` 等写入或管理操作
- SQLite 使用只读连接执行生成 SQL
