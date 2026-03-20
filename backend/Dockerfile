FROM python:3.11-slim

# Force rebuild - 2025-03-20
WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data /app/backup

# 复制应用代码
COPY backend/app/ ./app/

# 暴露端口
EXPOSE 8000

# 启动命令（使用 shell 形式以支持环境变量）
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
