"""
LangSmith API 키 유효성 검증 스크립트

이 스크립트는 LangSmith API 키의 유효성을 검증합니다.
"""

import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 필요한 패키지 확인
try:
    import requests
    from langsmith import Client
except ImportError:
    print("필요한 패키지가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install requests langsmith python-dotenv")
    sys.exit(1)

# API 키 직접 확인
api_key = os.environ.get("LANGSMITH_API_KEY")
endpoint = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

if not api_key:
    print("❌ LANGSMITH_API_KEY가 환경 변수에 설정되지 않았습니다.")
    sys.exit(1)

print(f"✅ API 키 발견: {api_key[:8]}...{api_key[-4:]}")
print(f"✅ 엔드포인트: {endpoint}")

# 직접 API 호출로 검증
print("\n직접 API 요청으로 키 검증 중...")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 세션 API 호출 (기본적인 인증 테스트)
try:
    response = requests.get(f"{endpoint}/sessions", headers=headers)
    if response.status_code == 200:
        print(f"✅ API 인증 성공 (상태 코드: {response.status_code})")
    elif response.status_code == 403:
        print(f"❌ API 인증 실패: 권한 없음 (상태 코드: {response.status_code})")
        print("→ 이 API 키에는 필요한 권한이 없거나 만료되었습니다.")
        print("→ LangSmith 대시보드에서 새 API 키를 생성하세요.")
    elif response.status_code == 401:
        print(f"❌ API 인증 실패: 인증되지 않음 (상태 코드: {response.status_code})")
        print("→ API 키가 잘못되었습니다.")
    else:
        print(f"❌ API 요청 실패 (상태 코드: {response.status_code})")
        print(f"→ 응답: {response.text}")
except Exception as e:
    print(f"❌ API 요청 오류: {e}")

# LangSmith 클라이언트로 검증
print("\nLangSmith 클라이언트로 키 검증 중...")
try:
    client = Client(api_key=api_key, api_url=endpoint)
    projects = list(client.list_projects())
    print(f"✅ LangSmith 클라이언트 인증 성공")
    print(f"✅ 프로젝트 {len(projects)}개 검색됨")
    for project in projects:
        print(f"  - {project.name}")
except Exception as e:
    print(f"❌ LangSmith 클라이언트 오류: {e}")

# 프로젝트 생성 테스트
project_name = os.environ.get("LANGSMITH_PROJECT", "test-project")
print(f"\n프로젝트 '{project_name}' 확인 중...")
try:
    client = Client(api_key=api_key, api_url=endpoint)
    # 프로젝트가 있는지 확인
    found = False
    for project in client.list_projects():
        if project.name == project_name:
            print(f"✅ 프로젝트 '{project_name}'가 이미 존재합니다.")
            found = True
            break
    
    if not found:
        # 프로젝트 생성 시도
        try:
            client.create_project(project_name=project_name)
            print(f"✅ 프로젝트 '{project_name}'를 성공적으로 생성했습니다.")
        except Exception as e:
            print(f"❌ 프로젝트 생성 실패: {e}")
except Exception as e:
    print(f"❌ 프로젝트 확인 중 오류 발생: {e}")

print("\n검증이 완료되었습니다.") 