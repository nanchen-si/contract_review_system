"""FastAPI 应用入口。"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, hits, logs, rules, tasks
from app.config import get_settings
from app.core.security import ensure_admin_seed
from app.db import init_db
from app.workers.queue import worker_loop

BASE_DIR = Path(__file__).resolve().parent


def _error_response(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": status, "message": message, "data": None})


def create_app(with_startup: bool = True) -> FastAPI:
    """组装 FastAPI：CORS、路由、异常处理、统一响应。"""
    @asynccontextmanager
    async def lifespan(app):
        if with_startup:
            init_db()
            ensure_admin_seed()
            worker = asyncio.create_task(worker_loop())
            yield
            worker.cancel()
        else:
            yield

    app = FastAPI(title="合同审查审批系统", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (auth.router, tasks.router, rules.router, hits.router, logs.router):
        app.include_router(router)

    frontend_dir = BASE_DIR / "frontend"
    if frontend_dir.is_dir():
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

        @app.get("/", include_in_schema=False)
        def index():
            """前端入口页。"""
            return FileResponse(frontend_dir / "index.html")

    @app.get("/api/health")
    def health():
        """健康检查。"""
        return {"status": "ok"}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return _error_response(400, "参数校验失败")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
