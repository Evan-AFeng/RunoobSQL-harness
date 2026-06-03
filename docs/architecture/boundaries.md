---
last_updated: 2026-06-03 15:33:51 +08:00
status: active
owner: @Evan-AFeng
---

# 模块边界和依赖规则

本文定义后端、前端和文档之间的职责边界。

## 后端边界

- `routes/`：只负责请求解析、参数校验、调用 service、返回 JSON。
- `services/`：负责业务流程、NL2SQL 编排、查询执行和结果整理。
- `models/`：负责数据结构和持久化模型；项目早期可为空。
- `configs/` 和 `config.py`：负责环境配置、数据库路径、运行参数。

## 前端边界

- `api/`：封装后端接口调用和响应处理。
- `views/`：组织页面级状态和页面布局。
- `components/`：沉淀可复用 UI，不直接依赖具体页面流程。
- `router/`：维护前端路由，不放业务逻辑。
- `assets/`：存放静态资源和全局样式。

## 依赖规则

- route 可以依赖 service，不直接依赖数据库细节。
- service 可以依赖 models、数据库访问封装和配置。
- models 不依赖 route 或 service。
- 前端 view 可以依赖 api 和 components。
- component 应尽量通过 props、events 与外部通信。
- 文档应描述当前实现或明确标注为计划项。

## 禁止事项

- 不在 route 中堆叠复杂业务逻辑。
- 不在前端组件中硬编码后端 URL，统一通过 api 层处理。
- 不把临时脚本、缓存文件、数据库文件提交到仓库。
- 单文件不得超过 500 行。
