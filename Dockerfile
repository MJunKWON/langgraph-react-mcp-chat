FROM python:3.13-slim

WORKDIR /app

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y build-essential curl

# Node.js와 npm 설치 (MCP 서버 실행에 필요)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# 필요한 파일 복사
COPY requirements.txt .
COPY pyproject.toml .
COPY src/ ./src/
COPY .env .
COPY langgraph.json .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 외부 접근을 위한 설정
ENV HOST=0.0.0.0
ENV PORT=2024

# 포트 노출
EXPOSE 2024

# 서버 실행
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024"] 