"""
Docker 환경 변수 테스트 스크립트

이 스크립트는 Docker 빌드 과정에서 환경 변수가 어떻게 설정되는지 테스트합니다.
"""

import os
import sys
import json

# 환경 변수 확인 및 출력
env_vars = {
    "기본 환경 변수": {
        "PORT": os.environ.get("PORT", "설정되지 않음"),
        "HOST": os.environ.get("HOST", "설정되지 않음"),
        "API_VARIANT": os.environ.get("API_VARIANT", "설정되지 않음"),
    },
    "LangSmith 관련 환경 변수": {
        "LANGSMITH_API_KEY": "***" if os.environ.get("LANGSMITH_API_KEY") else "설정되지 않음",
        "LANGSMITH_ENDPOINT": os.environ.get("LANGSMITH_ENDPOINT", "설정되지 않음"),
        "LANGSMITH_PROJECT": os.environ.get("LANGSMITH_PROJECT", "설정되지 않음"),
        "LANGCHAIN_TRACING_V2": os.environ.get("LANGCHAIN_TRACING_V2", "설정되지 않음"),
        "LANGSMITH_TRACING": os.environ.get("LANGSMITH_TRACING", "설정되지 않음"),
    },
    "API 키 관련 환경 변수": {
        "ANTHROPIC_API_KEY": "***" if os.environ.get("ANTHROPIC_API_KEY") else "설정되지 않음",
        "OPENAI_API_KEY": "***" if os.environ.get("OPENAI_API_KEY") else "설정되지 않음",
    }
}

# 결과 출력
print("========== 환경 변수 테스트 ==========")
print(f"실행 환경: {'Docker' if os.environ.get('RAILWAY_STATIC_URL') else '로컬'}")
print(f"Python 버전: {sys.version}")
print(f"작업 디렉터리: {os.getcwd()}")
print("\n환경 변수 목록:")
print(json.dumps(env_vars, indent=2, ensure_ascii=False))

# 파일 존재 여부 확인
files_to_check = [".env", ".env.example", "src/react_agent/mcp_config.json"]
print("\n파일 존재 여부 확인:")
for file_path in files_to_check:
    print(f"{file_path}: {'존재함' if os.path.exists(file_path) else '존재하지 않음'}")

# LangSmith 트레이싱 상태 확인
print("\nLangSmith 트레이싱 상태:")
tracing_enabled = (
    os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true" or
    os.environ.get("LANGSMITH_TRACING", "").lower() == "true"
)
print(f"트레이싱 활성화: {'예' if tracing_enabled else '아니오'}")

# 결론
print("\n결론:")
if not tracing_enabled:
    print("LangSmith 트레이싱이 비활성화되어 있어 API 키 관련 오류가 발생하지 않을 것입니다.")
elif not os.environ.get("LANGSMITH_API_KEY"):
    print("LangSmith 트레이싱이 활성화되어 있지만 API 키가 설정되지 않았습니다. 오류가 발생할 수 있습니다.")
else:
    print("LangSmith 트레이싱이 활성화되어 있고 API 키도 설정되어 있습니다.")

print("========== 테스트 완료 ==========")

# 결과를, 나중에 확인할 수 있도록 파일로 저장
try:
    with open("/tmp/docker_env_test_result.txt", "w") as f:
        f.write(f"환경 변수 테스트 결과 ({sys.argv[0]})\n")
        f.write(f"실행 시간: {__import__('datetime').datetime.now()}\n\n")
        f.write(f"환경 변수 목록:\n{json.dumps(env_vars, indent=2, ensure_ascii=False)}\n\n")
        f.write("파일 존재 여부 확인:\n")
        for file_path in files_to_check:
            f.write(f"{file_path}: {'존재함' if os.path.exists(file_path) else '존재하지 않음'}\n")
        f.write(f"\n트레이싱 활성화: {'예' if tracing_enabled else '아니오'}\n")
except Exception as e:
    print(f"결과 파일 저장 실패: {e}") 