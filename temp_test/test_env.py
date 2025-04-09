"""
환경 변수 로드 테스트 스크립트

이 스크립트는 환경 변수가 제대로 로드되는지 테스트합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드 시도
load_dotenv()

# 테스트를 위해 환경 변수를 직접 설정
# 실제 API 키는 .env 파일 확인
test_langsmith_api_key = "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"
os.environ["LANGSMITH_API_KEY"] = test_langsmith_api_key
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"

def mask_key(key):
    """API 키를 마스킹하여 출력합니다."""
    if key and len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    elif key:
        return "짧은 키"
    else:
        return "없음"

# 주요 환경 변수 확인
print("\n===== 환경 변수 확인 =====")
print(f"LANGSMITH_API_KEY: {mask_key(os.environ.get('LANGSMITH_API_KEY'))}")
print(f"LANGSMITH_ENDPOINT: {os.environ.get('LANGSMITH_ENDPOINT', '없음')}")
print(f"LANGSMITH_PROJECT: {os.environ.get('LANGSMITH_PROJECT', '없음')}")
print(f"LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING', '없음')}")
print(f"ANTHROPIC_API_KEY: {mask_key(os.environ.get('ANTHROPIC_API_KEY'))}")
print(f"OPENAI_API_KEY: {mask_key(os.environ.get('OPENAI_API_KEY'))}")
print("======================\n")

# process.env 값 직접 확인
print("Docker 또는 Railway와 같은 환경에서 제공될 수 있는 환경 변수:")
print(f"PORT: {os.environ.get('PORT', '없음')}")
print(f"HOST: {os.environ.get('HOST', '없음')}")
print(f"API_VARIANT: {os.environ.get('API_VARIANT', '없음')}")
print("======================\n")

# 시스템 정보
import sys
import platform
print("시스템 정보:")
print(f"Python 버전: {sys.version}")
print(f"플랫폼: {platform.platform()}")
print("======================\n")

# 현재 작업 디렉터리 확인
print(f"현재 작업 디렉터리: {os.getcwd()}")

# 선택사항: LangSmith API 연결 테스트
try:
    from langsmith import Client
    print("\nLangSmith API 연결 테스트 중...")
    client = Client()
    projects = list(client.list_projects())
    print(f"LangSmith 연결 성공! 프로젝트 {len(projects)}개 조회됨")
    if projects:
        for project in projects:
            print(f"  - {project.name}")
except ImportError:
    print("\nLangsmith 패키지가 설치되지 않았습니다.")
except Exception as e:
    print(f"\nLangSmith 연결 실패: {e}")
    
# .env 파일의 내용 읽기
try:
    print("\n.env 파일 내용 확인:")
    with open(".env", "r") as env_file:
        env_content = env_file.read()
        # API 키는 마스킹 처리
        import re
        masked_content = re.sub(r'(API_KEY=")([^"]{8})([^"]+)([^"]{4})(")', r'\1\2...\4\5', env_content)
        print(masked_content)
except Exception as e:
    print(f".env 파일을 읽을 수 없습니다: {e}") 