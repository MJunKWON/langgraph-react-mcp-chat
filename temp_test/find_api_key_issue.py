"""
LangSmith API 연결 테스트 스크립트

이 스크립트는 다양한 방법으로 LangSmith API 연결을 테스트합니다.
"""

import os
from dotenv import load_dotenv
import sys
import re

# .env 파일 로드 시도
load_dotenv()

def test_with_key(api_key, endpoint=None):
    """주어진 API 키로 LangSmith 연결을 테스트합니다."""
    if not api_key:
        return False, "API 키가 제공되지 않았습니다."
    
    # 환경 변수에 API 키 설정
    os.environ["LANGSMITH_API_KEY"] = api_key
    if endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
    
    try:
        from langsmith import Client
        
        # 클라이언트 초기화 및 연결 테스트
        client = Client()
        projects = list(client.list_projects())
        return True, f"성공! 프로젝트 {len(projects)}개 조회됨"
    except Exception as e:
        return False, f"연결 실패: {e}"

def mask_key(key):
    """API 키를 마스킹하여 출력합니다."""
    if key and len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    else:
        return "키 없음"

# 기본 테스트 (현재 환경 변수)
print("\n===== 현재 환경 변수로 테스트 =====")
env_key = os.environ.get("LANGSMITH_API_KEY")
env_endpoint = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
print(f"LANGSMITH_API_KEY: {mask_key(env_key)}")
print(f"LANGSMITH_ENDPOINT: {env_endpoint}")
success, message = test_with_key(env_key, env_endpoint)
print(f"결과: {'✅' if success else '❌'} {message}")
print("============================\n")

# .env 파일에서 직접 읽기
try:
    print("===== .env 파일에서 직접 읽기 =====")
    with open(".env", "r") as f:
        content = f.read()
        # API 키 추출 시도
        match = re.search(r'LANGSMITH_API_KEY="?([^"\n]+)"?', content)
        if match:
            env_file_key = match.group(1)
            print(f"발견된 API 키: {mask_key(env_file_key)}")
            success, message = test_with_key(env_file_key)
            print(f"결과: {'✅' if success else '❌'} {message}")
        else:
            print("❌ .env 파일에서 API 키를 찾을 수 없습니다.")
except Exception as e:
    print(f"❌ .env 파일 읽기 실패: {e}")
print("============================\n")

# 하드코딩된 API 키로 테스트
API_KEYS = [
    "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",  # env.example에서 가져온 값
]

print("===== 새로운 API 키로 테스트 =====")
for idx, key in enumerate(API_KEYS, 1):
    print(f"\n테스트 {idx}: API 키 {mask_key(key)}")
    success, message = test_with_key(key)
    print(f"결과: {'✅' if success else '❌'} {message}")
print("============================\n")

# 권한 문제 확인
print("===== 권한 문제 확인 =====")
if "Forbidden" in message:
    print("❗ 403 Forbidden 오류는 API 키가 유효하지만 권한이 없음을 의미합니다.")
    print("가능한 원인:")
    print("1. API 키가 만료되었습니다.")
    print("2. API 키에 필요한 권한이 없습니다.")
    print("3. 계정에 활성화된 구독이 없습니다.")
    print("4. IP 주소가 차단되었습니다.")
    print("\n해결 방법:")
    print("1. LangSmith 대시보드에서 새 API 키를 생성하세요.")
    print("2. LangSmith 팀에 문의하여 계정 상태를 확인하세요.")
print("============================\n")

print("API 키 확인 프로세스가 완료되었습니다.") 