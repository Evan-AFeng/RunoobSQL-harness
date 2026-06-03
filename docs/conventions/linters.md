---
last_updated: 2026-06-03 16:18:18 +08:00
status: active
owner: @Evan-AFeng
---

# 自定义 Linter 规则

本文是项目自定义 linter 的维护入口。

你只需要在这里新增规则说明。agent 看到新增规则后，应生成对应检查脚本，并注册到 `pyproject.toml` 的 `tool.runoobsql.lint.custom_commands`。

## 规则编写格式

每条规则必须包含以下三段：

```text
❌ [什么错了]
✅ FIX: [怎么改，给出代码片段]
📖 See: [哪个文档有详细说明]
```

建议同时提供规则元信息，方便 agent 生成脚本：

```text
### rule_id

- status: draft | active | deprecated
- type: max_file_lines | regex | ast | custom
- target: 要检查的文件或目录
- script: 期望生成或已生成的脚本路径

❌ [什么错了]
✅ FIX: [怎么改，给出代码片段]
📖 See: [哪个文档有详细说明]
```

## Agent 落地要求

当本文件新增 `status: draft` 的规则时，agent 应：

- 在 `tools/custom_linters/` 下生成对应脚本。
- 将脚本注册到 `pyproject.toml` 的 `custom_commands`。
- 让脚本违规输出严格包含 `❌`、`✅ FIX:`、`📖 See:`。
- 脚本通过时返回退出码 `0`，发现违规时返回非 `0`。
- 运行脚本语法检查。
- 运行新 linter，确认当前项目是否通过。
- 规则落地后，将状态改为 `active`。

## 已启用规则

### max_file_lines

- status: active
- type: max_file_lines
- target: repository text files
- script: `tools/custom_linters/max_file_lines.py`

````text
❌ 单文件超过 500 行。
✅ FIX: 拆分文件，把路由、业务逻辑、组件或配置移到更小的模块，例如：
```python
from app.services.query_service import run_query


@query_bp.post('/api/query')
def query():
    return run_query(request.get_json())
```
📖 See: docs/conventions/linters.md
````

### no_print_in_backend

- status: active
- type: ast
- target: backend/**/*.py
- script: `tools/custom_linters/no_print_in_backend.py`

````text
❌ 后端代码禁止直接使用 print。
✅ FIX: 使用 logging 输出日志，例如：
```python
import logging

logger = logging.getLogger(__name__)
logger.info("message")
```
📖 See: docs/conventions/logging.md
````

### max_line_width

- status: active
- type: regex
- target: repository text files
- script: `tools/custom_linters/max_line_width.py`

````text
❌ 行宽超过 120 字符。
✅ FIX: 拆分长行，优先使用括号、局部变量或多行结构，例如：
```python
result = service.run_query(
    question=question,
    limit=limit,
)
```
📖 See: docs/conventions/linters.md
````

## 待生成规则

在这里追加 `status: draft` 的新规则。agent 会根据规则说明生成脚本并注册到 linter 配置。
