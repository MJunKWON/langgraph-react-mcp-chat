"""
LangSmith 연결 테스트 스크립트

이 스크립트는 LangSmith에 연결하고 'Hello, world!' 메시지를 보내 추적을 생성합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수 확인
print("===== LangSmith 환경 변수 =====")
print(f"LANGSMITH_API_KEY: {'설정됨' if os.environ.get('LANGSMITH_API_KEY') else '설정되지 않음'}")
print(f"LANGSMITH_ENDPOINT: {os.environ.get('LANGSMITH_ENDPOINT', '없음')}")
print(f"LANGSMITH_PROJECT: {os.environ.get('LANGSMITH_PROJECT', '없음')}")
print(f"LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING', '없음')}")
print("=============================")

# LangSmith 작동 테스트
try:
    # LangChain과 LangSmith 관련 라이브러리 가져오기
    from langchain_openai import ChatOpenAI
    
    # API 키가 설정되어 있는지 확인
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("OpenAI API 키가 설정되어 있지 않습니다.")
        exit(1)
    
    # 모델 초기화
    llm = ChatOpenAI()
    
    # 간단한 호출로 LangSmith에 추적 보내기
    print("\n테스트 실행 중...")
    result = llm.invoke("Hello, world!")
    
    print(f"\n결과: {result.content}")
    print("\nLangSmith 추적이 생성되었습니다!")
    print(f"LangSmith 프로젝트 '{os.environ.get('LANGSMITH_PROJECT')}' 대시보드에서 확인하세요.")
    
except ImportError as e:
    print(f"\n오류: 필요한 라이브러리가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치할 수 있습니다:")
    print("pip install langchain langchain-openai")
    
except Exception as e:
    print(f"\n오류 발생: {e}")
    
print("\n테스트가 완료되었습니다.") 