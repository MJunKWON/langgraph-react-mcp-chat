"""API 키 관리 모듈

이 모듈은 API 키를 관리하고 검증하는 기능을 제공합니다.
민감한 API 키를 직접 코드에 포함하지 않고, 환경 변수나 외부 파일에서 로드합니다.
"""

import os
import json
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# API 키 안전한 자리 표시자 (실제 키가 아님)
API_KEY_PLACEHOLDER = {
    "openai": "sk-placeholder-openai-key",
    "anthropic": "sk-ant-placeholder-anthropic-key",
    "langsmith": "lsv2-placeholder-langsmith-key"
}

# 외부 키 파일 경로
API_KEYS_FILE = ".api_keys.json"


def load_api_keys_from_file() -> Dict[str, str]:
    """외부 JSON 파일에서 API 키를 로드합니다."""
    try:
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"API 키 파일 로드 실패: {e}")
    return {}


def get_api_key(key_name: str) -> str:
    """
    환경 변수나 외부 파일에서 API 키를 가져옵니다.
    
    Args:
        key_name: API 키 이름 (예: "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    
    Returns:
        API 키 문자열 또는 None
    """
    # 1. 환경 변수에서 먼저 검색
    env_key = os.environ.get(key_name)
    if env_key and not env_key.startswith("your_") and env_key != "None":
        return env_key
    
    # 2. 외부 파일에서 검색
    file_keys = load_api_keys_from_file()
    if key_name.lower() in file_keys and file_keys[key_name.lower()]:
        return file_keys[key_name.lower()]
    
    # 3. 개발용 키가 있으면 반환 (이 부분은 제품 환경에서는 비활성화해야 함)
    if key_name == "OPENAI_API_KEY":
        # 클라우드 환경에서 불러오는 방식으로 대체
        return API_KEY_PLACEHOLDER["openai"]
    elif key_name == "ANTHROPIC_API_KEY":
        return API_KEY_PLACEHOLDER["anthropic"]
    elif key_name == "LANGSMITH_API_KEY":
        return API_KEY_PLACEHOLDER["langsmith"]
    
    # 키를 찾을 수 없음
    return None


def validate_api_keys() -> Dict[str, bool]:
    """API 키의 유효성을 검증합니다."""
    result = {}
    
    # OpenAI API 키 검증
    openai_key = get_api_key("OPENAI_API_KEY")
    result["openai"] = bool(openai_key and not openai_key.startswith("your_") and openai_key != "sk-" and len(openai_key) > 10)
    
    # Anthropic API 키 검증
    anthropic_key = get_api_key("ANTHROPIC_API_KEY")
    result["anthropic"] = bool(anthropic_key and not anthropic_key.startswith("your_") and len(anthropic_key) > 10)
    
    # LangSmith API 키 검증
    langsmith_key = get_api_key("LANGSMITH_API_KEY")
    result["langsmith"] = bool(langsmith_key and not langsmith_key.startswith("your_") and len(langsmith_key) > 10)
    
    return result


def print_api_key_status() -> None:
    """API 키 상태를 콘솔에 출력합니다."""
    keys = {
        "OPENAI_API_KEY": get_api_key("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": get_api_key("ANTHROPIC_API_KEY"),
        "LANGSMITH_API_KEY": get_api_key("LANGSMITH_API_KEY"),
    }
    
    # API 키 마스킹 함수
    def mask_key(key: Optional[str]) -> str:
        if not key:
            return "설정되지 않음"
        if key.startswith("sk-placeholder") or key.startswith("lsv2-placeholder"):
            return "자리 표시자 사용 중"
        if len(key) > 12:
            return f"{key[:4]}...{key[-4:]}"
        return "***"
    
    print("\n===== API 키 상태 =====")
    for name, key in keys.items():
        print(f"{name}: {mask_key(key)}")
    
    validation = validate_api_keys()
    print("\n===== API 키 유효성 =====")
    for name, valid in validation.items():
        status = "✅ 유효함" if valid else "❌ 유효하지 않음"
        print(f"{name.upper()}: {status}")
    
    print("======================\n") 