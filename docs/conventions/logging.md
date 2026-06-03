---
last_updated: 2026-06-03 16:18:18 +08:00
status: active
owner: @Evan-AFeng
---

# 日志规范

后端代码应使用 `logging` 输出日志，不直接使用 `print`。

## 推荐写法

```python
import logging

logger = logging.getLogger(__name__)


def run_task() -> None:
    logger.info("task started")
```

## 原则

- 普通流程信息使用 `logger.info`。
- 调试信息使用 `logger.debug`。
- 可恢复异常使用 `logger.warning`。
- 需要排查的异常使用 `logger.exception` 或 `logger.error`。
- 不在日志中输出密钥、密码、Token 或完整用户敏感数据。
