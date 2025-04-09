FROM python:3.13-slim

WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Node.js와 npm 설치 (MCP 서버 실행에 필요)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# 필요한 파일 복사 - 의존성만 먼저 설치하기 위해 파일 분리
COPY requirements.txt .
COPY pyproject.toml .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 그 외 필요한 파일 복사
COPY src/ ./src/
COPY .env .env
COPY langgraph.json .

# 환경 변수 설정
ENV PORT=2024
ENV HOST=0.0.0.0

# 포트 노출
EXPOSE ${PORT}

# 서버 실행
CMD langgraph dev --host ${HOST} --port ${PORT} 