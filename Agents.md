# AGENTS.md

## 项目简介
这是一个轻量的NL2SQL问数平台，基于Flask（后端）+Vue3（前端）+SQLite（数据库）。

## 快速导航
| 你想做什么 | 去哪里看 |
|-----------|---------|
| 了解系统架构 | docs/architecture/overview.md |
| 了解模块边界和依赖规则 | docs/architecture/boundaries.md |
| 了解编码规范 | docs/conventions/README.md |
| 维护自定义 linter 规则 | docs/conventions/linters.md |
| 了解当前迭代任务 | docs/plans/current-sprint.md |
| 了解 API 规范 | docs/reference/api-spec.yaml |
| 了解错误码 | docs/reference/error-codes.md |
| 了解测试规范 | docs/conventions/testing.md |

## 硬性规则（必须遵守，CI 会验证）
1. 新增后端代码必须有对应单元测试，覆盖率>60%
2. 任何修改必须通过所有单元测试
3. 修改后需要运行相关测试以及自定义linter，确保符合要求
4. 前端代码可以先不关注上述要求
5. 每个功能需要同时关注前后端，如涉及前端，在开发完成后调用内置Browser插件进行验证。注意验证完后关闭前后端服务。

## 自定义 linter 工作流
自定义规则统一维护在 `docs/conventions/linters.md`。
当该文档新增规则时，agent 应负责：
1. 在 `tools/custom_linters/` 生成或更新对应检查脚本
2. 在 `pyproject.toml` 的 `tool.runoobsql.lint.custom_commands` 注册脚本
3. 保证违规输出包含 `❌`、`✅ FIX:`、`📖 See:` 三段
4. 运行脚本语法检查和对应 linter 验证

## 提交规范
- feat: 新功能
- fix: 修复
- refactor: 重构
- docs: 文档
- test: 测试
