"""
LangSmith Hello World 테스트

이 스크립트는 LangSmith에 Hello World 예제를 실행합니다.
"""

import os
from dotenv import load_dotenv
import sys

# 환경 변수 로드
load_dotenv()

# 환경 변수 설정
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["LANGSMITH_PROJECT"] = "pr-whispered-mining-89"
os.environ["LANGSMITH_TRACING"] = "true"

print("=== 환경 변수 설정 ===")
print(f"LANGSMITH_API_KEY: {os.environ.get('LANGSMITH_API_KEY')[:8]}...")
print(f"LANGSMITH_PROJECT: {os.environ.get('LANGSMITH_PROJECT')}")
print(f"LANGSMITH_TRACING: {os.environ.get('LANGSMITH_TRACING')}")
print("=====================")

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
except ImportError:
    print("필요한 라이브러리가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install langchain langchain-openai")
    sys.exit(1)

print("\n간단한 Hello World 테스트를 실행합니다...\n")

# 모델 초기화
try:
    llm = ChatOpenAI(temperature=0)
    
    # LLM 호출
    messages = [HumanMessage(content="Hello, world!")]
    response = llm.invoke(messages)
    
    print(f"AI 응답: {response.content}\n")
    print("✅ 테스트가 성공적으로 완료되었습니다!")
    print(f"✅ LangSmith 프로젝트 '{os.environ.get('LANGSMITH_PROJECT')}'에서 추적을 확인할 수 있습니다.")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}") 