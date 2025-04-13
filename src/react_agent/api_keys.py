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


def get_langsmith_project() -> str:
    """LangSmith 프로젝트 이름을 가져옵니다."""
    # 환경 변수에서 프로젝트 이름 가져오기
    project = os.environ.get("LANGSMITH_PROJECT")
    if project:
        return project
    
    # 기본 프로젝트 이름
    return "langgraph-react-mcp-chat"


def setup_langsmith():
    """LangSmith 관련 설정을 진행합니다."""
    # LangSmith API 키 가져오기
    langsmith_key = get_api_key("LANGSMITH_API_KEY")
    
    # 키가 없거나 자리 표시자면 트레이싱 비활성화
    if not langsmith_key or langsmith_key.startswith("lsv2-placeholder"):
        print("⚠️ 유효한 LangSmith API 키가 없어 트레이싱이 비활성화됩니다.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    
    # 환경 변수 설정
    os.environ["LANGSMITH_API_KEY"] = langsmith_key
    os.environ["LANGSMITH_ENDPOINT"] = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    os.environ["LANGSMITH_PROJECT"] = get_langsmith_project()
    
    # 트레이싱 활성화 설정
    tracing_enabled = (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true" or
        os.environ.get("LANGSMITH_TRACING", "").lower() == "true"
    )
    
    if tracing_enabled:
        print(f"✅ LangSmith 트레이싱 활성화: {os.environ.get('LANGSMITH_PROJECT')}")
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_TRACING"] = "true"
        return True
    else:
        print("⚠️ LangSmith 트레이싱이 설정에서 비활성화되어 있습니다.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False


def test_langsmith_connection() -> bool:
    """LangSmith 연결을 테스트합니다."""
    if not setup_langsmith():
        return False
        
    try:
        from langsmith import Client
        import requests
        from requests.adapters import HTTPAdapter, Retry
        
        # 연결 타임아웃 설정
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # LangSmith 클라이언트 생성
        client = Client(
            api_key=get_api_key("LANGSMITH_API_KEY"),
            api_url=os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
            timeout_ms=30000,  # 30초 타임아웃
        )
        
        # 프로젝트 리스트 조회 시도
        try:
            projects = list(client.list_projects())
            print(f"✅ LangSmith 연결 성공! 프로젝트 {len(projects)}개 조회됨")
            return True
        except Exception as e:
            print(f"⚠️ LangSmith 프로젝트 조회 실패: {e}")
            
        # 다른 API 호출 시도 (테넌트 정보)
        try:
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_api_key('LANGSMITH_API_KEY')}"
            }
            response = session.get(
                f"{os.environ.get('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')}/tenants/pending",
                headers=headers
            )
            print(f"테넌트 정보 조회: {response.status_code} {response.reason}")
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"⚠️ LangSmith 테넌트 정보 조회 실패: {e}")
            
        # 모든 시도 실패
        print("⚠️ LangSmith 연결 테스트 실패. 트레이싱이 비활성화됩니다.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    except ImportError:
        print("⚠️ LangSmith 라이브러리가 설치되지 않았습니다. 트레이싱이 비활성화됩니다.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    except Exception as e:
        print(f"⚠️ LangSmith 연결 테스트 중 오류 발생: {e}")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False 