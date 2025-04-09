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

# 프로젝트 소스 코드 복사
COPY . .

# 현재 프로젝트를 개발 모드(-e)로 설치하여 모듈 import 문제 해결
RUN pip install -e .

# mcp_config.json 파일이 있는지 확인 (디버깅용)
RUN ls -la /app/src/react_agent/ && \
    cat /app/src/react_agent/mcp_config.json || echo "mcp_config.json file not found"

# .env.example 파일이 있으면 .env로 복사 (없으면 무시)
RUN if [ -f .env.example ]; then cp .env.example .env; fi

# Railway는 자동으로 PORT 환경 변수를 제공합니다
# PORT가 설정되지 않았을 경우에만 기본값 사용 (Railway는 8080 포트 사용)
ENV PORT=${PORT:-8080}
ENV HOST=0.0.0.0

# 포트 노출 - Railway가 제공하는 PORT 사용
EXPOSE ${PORT}

# 서버 실행
CMD langgraph dev --host ${HOST} --port ${PORT} 