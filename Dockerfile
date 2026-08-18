# 合同审查审批系统 · 部署镜像
# Python 3.12 与本地一致；安装 OpenCV 完整版所需的 X11 运行库，解决 Railway 容器 libxcb.so.1 缺失。
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libxcb-util1 \
    libxcb-shape0 \
    libxcb-render0 \
    libxcb-xfixes0 \
    libxcb-shm0 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-xkb1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY . .

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
