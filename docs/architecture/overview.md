---
last_updated: 2026-06-03 15:33:51 +08:00
status: active
owner: @Evan-AFeng
---

# 系统架构

RunoobSQL-harness 是一个轻量的 NL2SQL 问数平台，采用 Flask + Vue 3 + SQLite 的组合。

## 技术栈

- 后端：Flask
- 前端：Vue 3 + Vite
- 数据库：SQLite
- 通信：HTTP JSON API

## 分层结构

```text
RunoobSQL-harness/
├── backend/                    # Flask 后端
│   ├── app/
│   │   ├── __init__.py          # 创建 Flask app
│   │   ├── configs/             # 配置相关
│   │   ├── routes/              # 接口路由
│   │   ├── services/            # 业务逻辑
│   │   ├── models/              # 数据模型，可先不用
│   │   └── config.py            # Flask 配置
│   ├── run.py                   # 后端启动入口
│   └── requirements.txt         # Python 依赖
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # 封装请求
│   │   ├── assets/              # 图片、CSS 等静态资源
│   │   ├── components/          # 通用组件
│   │   ├── views/               # 页面
│   │   ├── router/              # 前端路由
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/                        # 项目文档
├── README.md
└── .gitignore
```

## 设计原则

- 保持轻量，优先使用框架原生能力。
- 后端路由只处理 HTTP 入参、出参和状态码。
- 业务逻辑放在 service 层，避免散落在 route 中。
- SQLite 仅作为本地轻量存储，避免引入复杂部署依赖。
- 前端 API 调用统一放在 `frontend/src/api/`，页面不直接拼接请求。
- 前端、后端都需要启动入口。