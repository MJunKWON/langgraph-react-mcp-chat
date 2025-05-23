FROM python:3.13-slim

WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    openssl && \
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

# HTTPS 연결 관련 패키지 설치
RUN pip install --no-cache-dir httpx==0.27.0 urllib3==2.0.7 requests==2.31.0

# WebSocket 테스트를 위한 패키지 설치
RUN pip install --no-cache-dir websockets==12.0

# 프로젝트 소스 코드 복사
COPY . .

# 현재 프로젝트를 개발 모드(-e)로 설치하여 모듈 import 문제 해결
RUN pip install -e .

# 환경 변수 파일 확인
RUN echo "🔍 환경 변수 파일 확인 중..."
RUN if [ -f .env ]; then \
    echo "✅ 기존 .env 파일을 사용합니다."; \
elif [ -f .env.example ]; then \
    echo "📝 .env.example에서 .env 파일을 생성합니다."; \
    cp .env.example .env; \
else \
    echo "⚠️ .env 또는 .env.example 파일이 없습니다! 기본 환경 변수를 생성합니다."; \
    echo "OPENAI_API_KEY=YOUR_OPENAI_API_KEY\nANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY" > .env; \
fi

# 환경 변수 설정
RUN echo "🔧 환경 변수를 로드합니다..."
# 환경 변수 테스트를 위한 디렉토리 생성
RUN mkdir -p temp_test

# 환경 변수 테스트 실행 (디버깅용)
COPY temp_test/docker_env_test.py temp_test/
RUN python temp_test/docker_env_test.py || echo "환경 변수 테스트 실패"

# LangSmith API 연결 검증 스크립트 실행
COPY temp_test/validate_key.py temp_test/
COPY temp_test/langsmith_hello_world.py temp_test/
COPY temp_test/https_connection_test.py temp_test/
COPY temp_test/websocket_test.py temp_test/

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
ENV LANGSMITH_API_KEY=${LANGSMITH_API_KEY:-"YOUR_LANGSMITH_API_KEY"}
ENV LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# API 키 설정
ENV OPENAI_API_KEY=${OPENAI_API_KEY:-"YOUR_OPENAI_API_KEY"}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-"YOUR_ANTHROPIC_API_KEY"}

# 네트워크 타임아웃 설정 증가
ENV REQUESTS_TIMEOUT=60
ENV OPENAI_TIMEOUT=60
ENV ANTHROPIC_TIMEOUT=60
ENV LANGSMITH_REQUEST_TIMEOUT=60

# LangSmith 연결 테스트 실행
RUN python temp_test/validate_key.py || echo "LangSmith API 키 검증 실패"
RUN python temp_test/https_connection_test.py || echo "HTTPS 연결 테스트 실패"
RUN python -m temp_test.websocket_test || echo "WebSocket 연결 테스트 실패"
RUN python temp_test/langsmith_hello_world.py || echo "LangSmith Hello World 테스트 실패"

# SSL/TLS 설정
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_DIR=/etc/ssl/certs
ENV PYTHONHTTPSVERIFY=1

# 네트워크 연결 문제 해결을 위한 DNS 설정
ENV GODEBUG=netdns=go
ENV DNS_TIMEOUT=30
ENV TCP_KEEP_ALIVE=true
ENV TCP_KEEP_ALIVE_INTERVAL=30

# WebSocket 연결 안정성 향상을 위한 설정
ENV LANGGRAPH_WEBSOCKET_MAX_RECONNECT_ATTEMPTS=5
ENV LANGGRAPH_WEBSOCKET_RECONNECT_INTERVAL=5000
ENV LANGGRAPH_WEBSOCKET_PING_INTERVAL=30000
ENV LANGGRAPH_WEBSOCKET_PING_TIMEOUT=10000
ENV LANGGRAPH_KEEP_ALIVE=true

# HTTP/2 프로토콜 문제 해결을 위한 설정
ENV LANGSMITH_HTTP2_ENABLED=false
ENV HTTP2_ENABLED=false
ENV CURL_HTTP_VERSION=HTTP/1.1

# 포트 노출 - Railway가 제공하는 PORT 사용
EXPOSE ${PORT}

# 서버 실행
CMD langgraph dev --host ${HOST} --port ${PORT} 