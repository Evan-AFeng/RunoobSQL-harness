---
last_updated: 2026-06-03 16:18:18 +08:00
status: active
owner: @Evan-AFeng
---

# 编码规范

本项目遵循轻量、清晰、可测试的编码原则。

## 通用规范

- 单文件不超过 500 行。
- 单行不超过 120 字符。
- 命名应表达业务含义，避免无意义缩写。
- 优先保持函数短小，复杂逻辑拆到私有函数或 service。
- 新增配置项需要提供默认值或说明必填原因。
- 修改行为时同步更新相关文档和测试。

## Python 后端

- 使用 Flask 原生路由和标准 JSON 响应。
- route 层只做 HTTP 适配，不承载核心业务逻辑。
- service 层返回结构化结果，避免返回 Flask response 对象。
- 异常应转换为统一错误响应，错误码参考 `docs/reference/error-codes.md`。
- 新增后端功能必须补充单元测试。
- 后端日志使用 `logging`，不直接使用 `print`。

## 代码检查

- Python 代码检查配置统一放在根目录 `pyproject.toml`。
- 默认使用 `ruff` 做 lint、import 排序和格式检查。
- 默认使用 `mypy` 做静态类型检查。
- 统一入口为 `python tools/run_linters.py`。
- 自定义 linter 命令追加到 `pyproject.toml` 的 `tool.runoobsql.lint.custom_commands`。
- 自定义 linter 输出应包含 `❌ [什么错了]`、`✅ FIX: [怎么改，给出代码片段]`、`📖 See: [哪个文档有详细说明]`。
- 自定义 linter 规则源头统一维护在 `docs/conventions/linters.md`。
- 已启用 `tools/custom_linters/max_file_lines.py`，用于检查单文件不超过 500 行。
- 已启用 `tools/custom_linters/max_line_width.py`，用于检查单行不超过 120 字符。
- 已启用 `tools/custom_linters/no_print_in_backend.py`，用于检查后端禁止直接 `print`。

## Vue 前端

- API 请求统一放在 `frontend/src/api/`。
- 页面级组件放在 `views/`，通用组件放在 `components/`。
- 组件 props 和事件命名保持直观。
- 避免在模板中写复杂表达式，复杂逻辑放入计算属性或函数。
- 样式尽量局部化，公共样式放入 `assets/`。

## 提交信息

- `feat:` 新功能
- `fix:` 修复
- `refactor:` 重构
- `docs:` 文档
- `test:` 测试
