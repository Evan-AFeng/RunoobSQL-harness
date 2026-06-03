---
last_updated: 2026-06-03 16:30:07 +08:00
status: active
owner: @Evan-AFeng
---

# 测试规范

## 基本要求

- 新增后端代码必须有对应单元测试。
- 后端测试覆盖率应大于 60%。
- 任何修改必须通过所有单元测试。
- GitHub CI 会运行代码检查，并在测试目录存在时运行 pytest。

## 后端测试

- 测试优先覆盖 service 层核心逻辑。
- route 测试应覆盖状态码、响应结构和错误分支。
- 数据库相关测试应使用临时 SQLite 数据库或隔离测试数据。
- 避免测试依赖本机绝对路径、真实外部服务或执行顺序。

## 前端测试

- 当前阶段未强制要求前端测试。
- 关键交互、API 状态处理和错误提示变复杂时，应补充组件或端到端测试。

## 推荐命令

安装开发依赖：

```powershell
pip install -r requirements-dev.txt
```

代码检查：

```powershell
python tools/run_linters.py
```

后端：

```powershell
cd backend
python -m pytest
```

如项目启用覆盖率：

```powershell
cd backend
python -m pytest --cov=app --cov-report=term-missing
```

GitHub Actions：

```text
.github/workflows/ci.yml
```
