# 合同审查审批系统

基于《项目实战》2.4 的合同审批审查系统 demo，技术栈：
Python 3.12 + FastAPI + LangGraph + SQLAlchemy + MySQL 8 + uv。

## 启动步骤

1. 启动 MySQL（需 Docker Desktop）：

   ```powershell
   docker compose up -d
   ```

2. 准备环境变量：

   ```powershell
   Copy-Item .env.example .env
   # 编辑 .env：填写 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL、DB_PASSWORD 等
   ```

3. 安装依赖：

   ```powershell
   uv sync
   ```

4. 初始化数据库（自动建 9 张表 + 种子管理员）：

   ```powershell
   uv run python -c "from app.db import init_db; init_db()"
   ```

5. 启动服务：

   ```powershell
   uv run uvicorn main:app --reload
   ```

   - OpenAPI 文档：http://127.0.0.1:8000/docs
   - 健康检查：http://127.0.0.1:8000/api/health

6. 一键演示（拉取 → 下载 → 解析 → 审查 → 回写）：

   ```powershell
   uv run python scripts/demo.py
   ```

## 常用接口

- `POST /api/auth/register`、`POST /api/auth/login`、`GET /api/auth/me`
- `POST /api/tasks/trigger`、`GET /api/tasks`、`GET /api/tasks/{id}`
- `POST /api/tasks/{id}/retry`（admin）
- `GET/POST/PUT/DELETE /api/rules`（维护规则，写操作需 admin）
- `GET /api/hits`、`GET /api/logs`（admin）

## 测试

```powershell
uv run pytest tests -q
```
