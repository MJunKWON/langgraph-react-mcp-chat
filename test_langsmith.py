"""
LangSmith API 키 테스트 스크립트

이 스크립트는 LangSmith API 연결을 테스트하여 API 키가 올바르게 설정되었는지 확인합니다.
"""

import os
import sys
from langsmith import Client

def test_langsmith_connection():
    """LangSmith API 연결을 테스트합니다."""
    api_key = os.environ.get("LANGSMITH_API_KEY")
    
    if not api_key:
        print("경고: LANGSMITH_API_KEY 환경 변수가 설정되지 않았습니다.")
        return False
    
    try:
        # LangSmith 클라이언트 생성
        client = Client()
        
        # API 키 테스트 (프로젝트 목록 조회)
        projects = client.list_projects()
        print(f"LangSmith API 연결 성공! 프로젝트 {len(list(projects))}개 조회됨")
        
        for project in projects:
            print(f"  - {project.name}")
        
        return True
    except Exception as e:
        print(f"LangSmith API 연결 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_langsmith_connection()
    sys.exit(0 if success else 1) 