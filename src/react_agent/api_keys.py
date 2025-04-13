"""API 키 관리 모듈

이 모듈은 API 키를 관리하고 검증하는 기능을 제공합니다.
민감한 API 키를 직접 코드에 포함하지 않고, 환경 변수나 외부 파일에서 로드합니다.
"""

import os
import json
import re
from typing import Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# API 키 안전한 자리 표시자 (실제 키가 아님)
API_KEY_PLACEHOLDER = {
    "openai": "sk-placeholder-openai-key",
    "anthropic": "sk-ant-placeholder-anthropic-key",
    "langsmith": "lsv2-placeholder-langsmith-key"
}

# 외부 키 파일 경로
API_KEYS_FILE = ".api_keys.json"


def mask_api_key(key: str) -> str:
    """API 키를 마스킹하여 보안을 강화합니다."""
    if not key or len(key) < 12:
        return "***비어있거나 짧은 키***"
    return f"{key[:8]}...{key[-4:]}"


def load_api_keys_from_env() -> Dict[str, str]:
    """환경 변수에서 API 키를 로드합니다."""
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY", ""),
        "LANGSMITH_ENDPOINT": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT", "langgraph-react-mcp-chat"),
        "SSL_VERIFY": os.getenv("SSL_VERIFY", "true").lower() == "true",
        "HTTP2_ENABLED": os.getenv("HTTP2_ENABLED", "false").lower() == "true",
        "REQUESTS_TIMEOUT": int(os.getenv("REQUESTS_TIMEOUT", "30")),
    }
    
    # 키 마스킹하여 로깅
    masked_keys = {k: mask_api_key(v) if "KEY" in k else v for k, v in keys.items()}
    logger.info(f"환경에서 로드된 API 키 및 설정: {masked_keys}")
    
    return keys


def load_api_keys_from_file(file_path: str = ".env.json") -> Dict[str, str]:
    """JSON 파일에서 API 키를 로드합니다."""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                keys = json.load(f)
                masked_keys = {k: mask_api_key(v) if "KEY" in k else v for k, v in keys.items()}
                logger.info(f"파일에서 로드된 API 키 및 설정: {masked_keys}")
                return keys
    except Exception as e:
        logger.error(f"API 키 파일 로드 중 오류 발생: {e}")
    
    return {}


def is_valid_openai_key(key: str) -> bool:
    """OpenAI API 키가 유효한지 확인합니다."""
    if not key:
        return False
    
    # 길이 체크와 sk- 접두사 확인
    if len(key) < 30 or not key.startswith("sk-"):
        logger.warning(f"OpenAI API 키 형식이 올바르지 않습니다: {mask_api_key(key)}")
        return False
        
    # 기본 키 또는 테스트 키 확인
    invalid_patterns = ["없음", "your_", "test_", "demo_", "placeholder"]
    for pattern in invalid_patterns:
        if pattern in key.lower():
            logger.warning(f"OpenAI API 키에 유효하지 않은 패턴이 포함되어 있습니다: {pattern}")
            return False
    
    # 추가 검증: 단순히 "sk-"만 있는지 확인
    if key == "sk-":
        logger.warning("OpenAI API 키가 단순히 'sk-'만 포함되어 있습니다")
        return False
            
    return True


def is_valid_anthropic_key(key: str) -> bool:
    """Anthropic API 키가 유효한지 확인합니다."""
    if not key:
        return False
        
    # Anthropic 키는 sk-ant로 시작해야 함
    if not key.startswith("sk-ant"):
        logger.warning(f"Anthropic API 키 형식이 올바르지 않습니다: {mask_api_key(key)}")
        return False
        
    # 길이 체크
    if len(key) < 30:
        logger.warning("Anthropic API 키가 너무 짧습니다")
        return False
        
    # 기본 키 또는 테스트 키 확인
    invalid_patterns = ["없음", "your_", "test_", "demo_", "placeholder"]
    for pattern in invalid_patterns:
        if pattern in key.lower():
            logger.warning(f"Anthropic API 키에 유효하지 않은 패턴이 포함되어 있습니다: {pattern}")
            return False
    
    # 추가 검증: 단순히 "sk-ant-api03"만 있는지 확인
    if key == "sk-ant-api03":
        logger.warning("Anthropic API 키가 단순히 'sk-ant-api03'만 포함되어 있습니다")
        return False
            
    return True


def is_valid_langsmith_key(key: str) -> bool:
    """LangSmith API 키가 유효한지 확인합니다."""
    if not key:
        return False
        
    # LangSmith 키는 ls_로 시작해야 함 
    if not key.startswith("ls_"):
        logger.warning(f"LangSmith API 키 형식이 올바르지 않습니다: {mask_api_key(key)}")
        return False
        
    # 길이 체크
    if len(key) < 30:
        logger.warning("LangSmith API 키가 너무 짧습니다")
        return False
        
    # 기본 키 또는 테스트 키 확인
    invalid_patterns = ["없음", "your_", "test_", "demo_", "placeholder"]
    for pattern in invalid_patterns:
        if pattern in key.lower():
            logger.warning(f"LangSmith API 키에 유효하지 않은 패턴이 포함되어 있습니다: {pattern}")
            return False
            
    return True


def get_validated_api_keys() -> Dict[str, str]:
    """환경 변수와 파일에서 API 키를 로드하고 검증합니다."""
    # 환경 변수에서 먼저 로드
    keys = load_api_keys_from_env()
    
    # 환경 변수에 없으면 파일에서 로드 시도
    if not any([keys.get("OPENAI_API_KEY"), keys.get("ANTHROPIC_API_KEY")]):
        file_keys = load_api_keys_from_file()
        # 파일에서 가져온 키로 환경 변수의 빈 키 업데이트
        for key_name, key_value in file_keys.items():
            if not keys.get(key_name):
                keys[key_name] = key_value
    
    # 검증 결과 출력
    validation_results = {
        "OPENAI_API_KEY": is_valid_openai_key(keys.get("OPENAI_API_KEY", "")),
        "ANTHROPIC_API_KEY": is_valid_anthropic_key(keys.get("ANTHROPIC_API_KEY", "")),
        "LANGSMITH_API_KEY": is_valid_langsmith_key(keys.get("LANGSMITH_API_KEY", "")),
    }
    
    logger.info(f"API 키 검증 결과: {validation_results}")
    
    return keys


def check_and_display_api_keys() -> None:
    """API 키를 체크하고 상태를 표시합니다."""
    keys = get_validated_api_keys()
    
    # OpenAI API 키 검증
    openai_key = keys.get('OPENAI_API_KEY', '')
    openai_valid = is_valid_openai_key(openai_key)
    openai_error = ""
    if not openai_valid:
        if not openai_key:
            openai_error = "키가 없음"
        elif len(openai_key) < 30:
            openai_error = "키가 너무 짧음"
        elif not openai_key.startswith("sk-"):
            openai_error = "잘못된 형식 (sk- 로 시작해야 함)"
        elif any(pattern in openai_key.lower() for pattern in ["없음", "your_", "test_", "demo_", "placeholder"]):
            openai_error = "테스트/샘플 키 사용됨"
        elif openai_key == "sk-":
            openai_error = "불완전한 키"
        else:
            openai_error = "알 수 없는 문제"
    
    # Anthropic API 키 검증
    anthropic_key = keys.get('ANTHROPIC_API_KEY', '')
    anthropic_valid = is_valid_anthropic_key(anthropic_key)
    anthropic_error = ""
    if not anthropic_valid:
        if not anthropic_key:
            anthropic_error = "키가 없음"
        elif not anthropic_key.startswith("sk-ant"):
            anthropic_error = "잘못된 형식 (sk-ant로 시작해야 함)"
        elif len(anthropic_key) < 30:
            anthropic_error = "키가 너무 짧음"
        elif any(pattern in anthropic_key.lower() for pattern in ["없음", "your_", "test_", "demo_", "placeholder"]):
            anthropic_error = "테스트/샘플 키 사용됨"
        elif anthropic_key == "sk-ant-api03":
            anthropic_error = "불완전한 키"
        else:
            anthropic_error = "알 수 없는 문제"
    
    # LangSmith API 키 검증
    langsmith_key = keys.get('LANGSMITH_API_KEY', '')
    langsmith_valid = is_valid_langsmith_key(langsmith_key)
    langsmith_error = ""
    if not langsmith_valid:
        if not langsmith_key:
            langsmith_error = "키가 없음"
        elif not langsmith_key.startswith("ls_"):
            langsmith_error = "잘못된 형식 (ls_로 시작해야 함)"
        elif len(langsmith_key) < 30:
            langsmith_error = "키가 너무 짧음"
        elif any(pattern in langsmith_key.lower() for pattern in ["없음", "your_", "test_", "demo_", "placeholder"]):
            langsmith_error = "테스트/샘플 키 사용됨"
        else:
            langsmith_error = "알 수 없는 문제"
    
    # 컬러 코드 (터미널에서만 작동)
    GREEN = "\033[92m"  # 초록색
    RED = "\033[91m"    # 빨간색
    YELLOW = "\033[93m" # 노란색
    BLUE = "\033[94m"   # 파란색
    BOLD = "\033[1m"    # 굵게
    END = "\033[0m"     # 서식 종료
    
    print("\n" + BOLD + "╔══════════════════════════════════════════════════╗" + END)
    print(BOLD + "║              🔑 API 키 상태 확인                 ║" + END)
    print(BOLD + "╚══════════════════════════════════════════════════╝" + END)
    
    # OpenAI 키 상태
    print(f"\n🔹 {BOLD}OpenAI API 키:{END} {mask_api_key(openai_key)}")
    if openai_valid:
        print(f"   {GREEN}✅ 상태: 유효함{END}")
    else:
        print(f"   {RED}❌ 상태: 유효하지 않음 - {openai_error}{END}")
    
    # Anthropic 키 상태
    print(f"\n🔹 {BOLD}Anthropic API 키:{END} {mask_api_key(anthropic_key)}")
    if anthropic_valid:
        print(f"   {GREEN}✅ 상태: 유효함{END}")
    else:
        print(f"   {RED}❌ 상태: 유효하지 않음 - {anthropic_error}{END}")
    
    # LangSmith 키 상태
    print(f"\n🔹 {BOLD}LangSmith API 키:{END} {mask_api_key(langsmith_key)}")
    if langsmith_valid:
        print(f"   {GREEN}✅ 상태: 유효함{END}")
    else:
        print(f"   {YELLOW}⚠️ 상태: 유효하지 않음 - {langsmith_error}{END}")
    
    # 사용 가능한 모델 표시
    print("\n" + BOLD + "╔══════════════════════════════════════════════════╗" + END)
    print(BOLD + "║              🤖 사용 가능한 모델                 ║" + END)
    print(BOLD + "╚══════════════════════════════════════════════════╝" + END)
    
    models_available = False
    if openai_valid:
        models_available = True
        print(f"\n{GREEN}✅ OpenAI 모델{END}")
        print(f"   • {BLUE}GPT-4-TURBO{END} - 고성능 추론")
        print(f"   • {BLUE}GPT-3.5-TURBO{END} - 빠른 응답")
    
    if anthropic_valid:
        models_available = True
        print(f"\n{GREEN}✅ Anthropic 모델{END}")
        print(f"   • {BLUE}CLAUDE-3-7-SONNET{END} - 통합 지능")
        print(f"   • {BLUE}CLAUDE-3-HAIKU{END} - 빠른 응답")
    
    if not models_available:
        print(f"\n{RED}❌ 사용 가능한 모델이 없습니다.{END}")
        print(f"{RED}   API 키를 확인하고 .env 파일에 올바르게 설정하세요.{END}")
    
    # 추가 설정 상태
    print("\n" + BOLD + "╔══════════════════════════════════════════════════╗" + END)
    print(BOLD + "║              ⚙️ 시스템 구성 상태                 ║" + END)
    print(BOLD + "╚══════════════════════════════════════════════════╝" + END)
    
    langsmith_endpoint = keys.get('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
    langsmith_project = keys.get('LANGSMITH_PROJECT', 'langgraph-react-mcp-chat')
    ssl_verify = keys.get('SSL_VERIFY', True)
    http2_enabled = keys.get('HTTP2_ENABLED', False)
    requests_timeout = keys.get('REQUESTS_TIMEOUT', 30)
    
    print(f"\n🔹 {BOLD}LangSmith 설정:{END}")
    print(f"   • 엔드포인트: {BLUE}{langsmith_endpoint}{END}")
    print(f"   • 프로젝트: {BLUE}{langsmith_project}{END}")
    print(f"   • 트레이싱: {GREEN if langsmith_valid else YELLOW}{'활성화됨' if langsmith_valid else '비활성화됨'}{END}")
    
    print(f"\n🔹 {BOLD}네트워크 설정:{END}")
    print(f"   • SSL 검증: {GREEN if ssl_verify else YELLOW}{'✅ 사용' if ssl_verify else '⚠️ 비활성화됨'}{END}")
    print(f"   • HTTP/2: {GREEN if http2_enabled else ''}{'✅ 사용' if http2_enabled else '❌ 사용 안 함'}{END}")
    print(f"   • 요청 타임아웃: {BLUE}{requests_timeout}초{END}")
    
    print("\n" + BOLD + "═════════════════════════════════════════════════════" + END)


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
        
        # API 키 준비
        api_key = get_api_key("LANGSMITH_API_KEY")
        api_url = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        print(f"\n===== LangSmith 연결 테스트 =====")
        print(f"API URL: {api_url}")
        print(f"API 키: {'설정됨' if api_key else '없음'}")
        
        if not api_key:
            print("⚠️ LangSmith API 키가 설정되지 않았습니다.")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ["LANGSMITH_TRACING"] = "false"
            return False
        
        # 직접 REST API 호출 테스트 (인증 기본 테스트)
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 1. GET /runs 호출 (기본 API 호출)
            runs_url = f"{api_url}/runs?limit=1"
            print(f"테스트 1: GET {runs_url}")
            runs_response = session.get(
                runs_url,
                headers=headers,
                timeout=10
            )
            print(f"응답 코드: {runs_response.status_code}")
            
            if runs_response.status_code in [200, 201]:
                print("✅ 기본 API 호출 성공")
            else:
                print(f"⚠️ 기본 API 호출 실패: {runs_response.status_code} - {runs_response.text[:100]}")
                
            # 2. 프로젝트 생성 시도 (쓰기 권한 테스트)
            project_name = f"test-project-{int(datetime.now().timestamp())}"
            project_url = f"{api_url}/projects"
            print(f"테스트 2: POST {project_url}")
            project_response = session.post(
                project_url,
                headers=headers,
                json={"name": project_name, "description": "Test project"},
                timeout=10
            )
            print(f"응답 코드: {project_response.status_code}")
            
            if project_response.status_code in [200, 201]:
                print("✅ 프로젝트 생성 API 호출 성공")
            else:
                print(f"⚠️ 프로젝트 생성 API 호출 실패: {project_response.status_code} - {project_response.text[:100]}")
                
            # 테스트 3: Client 객체 사용
            print("테스트 3: LangSmith Client 객체 사용")
            try:
                # Client 초기화 시 명시적 파라미터 사용
                client = Client(
                    api_key=api_key,
                    api_url=api_url,
                    timeout_ms=10000
                )
                
                # 프로젝트 목록 조회
                try:
                    projects = list(client.list_projects(limit=5))
                    print(f"✅ 프로젝트 목록 조회 성공: {len(projects)}개")
                    return True
                except Exception as e:
                    print(f"⚠️ 프로젝트 목록 조회 실패: {str(e)}")
            except Exception as e:
                print(f"⚠️ Client 초기화 실패: {str(e)}")
                
            # 어느 정도 성공했다면 트레이싱 활성화
            if runs_response.status_code in [200, 201] or project_response.status_code in [200, 201]:
                print("✅ 부분적으로 API 호출 성공. 트레이싱 활성화")
                return True
                
            # 모든 테스트 실패
            print("⚠️ 모든 LangSmith API 테스트 실패")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ["LANGSMITH_TRACING"] = "false"
            return False
                
        except Exception as e:
            print(f"⚠️ API 직접 호출 실패: {str(e)}")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            os.environ["LANGSMITH_TRACING"] = "false"
            return False
            
    except ImportError:
        print("⚠️ LangSmith 라이브러리가 설치되지 않았습니다.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False
    except Exception as e:
        print(f"⚠️ LangSmith 연결 테스트 중 오류 발생: {str(e)}")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        os.environ["LANGSMITH_TRACING"] = "false"
        return False 


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    check_and_display_api_keys() 