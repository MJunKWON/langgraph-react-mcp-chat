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

# .env 파일이 있으면 복사하고, 없으면 .env.example에서 생성
RUN if [ -f .env ]; then \
    echo "Using existing .env file"; \
    else \
    if [ -f .env.example ]; then \
        echo "Creating .env from .env.example"; \
        cp .env.example .env; \
    else \
        echo "Warning: No .env or .env.example file found"; \
    fi; \
fi

# 환경 변수 테스트를 위한 디렉토리 생성
RUN mkdir -p temp_test

# 환경 변수 테스트 실행 (디버깅용)
COPY temp_test/docker_env_test.py temp_test/
RUN python temp_test/docker_env_test.py || echo "환경 변수 테스트 실패"

# LangSmith API 연결 검증 스크립트 실행
COPY temp_test/validate_key.py temp_test/
COPY temp_test/langsmith_hello_world.py temp_test/

# Railway는 자동으로 PORT 환경 변수를 제공합니다
# PORT가 설정되지 않았을 경우에만 기본값 사용 (Railway는 8080 포트 사용)
ENV PORT=${PORT:-8080}
ENV HOST=0.0.0.0
# API 변형 설정 - 프로덕션 모드로 실행 (중요: 빌드 시점에 명시적으로 설정)
ENV API_VARIANT=production

# LangSmith 트레이싱 활성화 (API 키 문제 해결됨)
ENV LANGCHAIN_TRACING_V2=true
ENV LANGSMITH_TRACING=true
# LangSmith 프로젝트 설정
ENV LANGSMITH_PROJECT=pr-whispered-mining-89
# 빌드 시점에 새 API 키 설정
ENV LANGSMITH_API_KEY=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
ENV LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# LangSmith 연결 테스트 실행
RUN python temp_test/validate_key.py || echo "LangSmith API 키 검증 실패"
RUN python temp_test/langsmith_hello_world.py || echo "LangSmith Hello World 테스트 실패"

# 포트 노출 - Railway가 제공하는 PORT 사용
EXPOSE ${PORT}

# 서버 실행
CMD langgraph dev --host ${HOST} --port ${PORT} 