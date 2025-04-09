"""
HTTPS 연결 테스트 스크립트

이 스크립트는 LangSmith API 엔드포인트에 대한 HTTPS 연결을 테스트합니다.
SSL/TLS 연결, 인증서, 프록시 설정 등을 확인합니다.
"""

import os
import sys
import requests
import socket
import ssl
import json
import urllib3
from urllib.parse import urlparse
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 LangSmith 엔드포인트 설정
LANGSMITH_ENDPOINT = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_API_KEY = os.environ.get("LANGSMITH_API_KEY", "")

# 연결 디버깅 활성화
urllib3.connectionpool.log.setLevel(20)  # INFO 레벨로 설정

def mask_key(key):
    """API 키 마스킹"""
    if key and len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    return "없음"

print(f"=== HTTPS 연결 테스트 시작 ===")
print(f"LangSmith 엔드포인트: {LANGSMITH_ENDPOINT}")
print(f"API 키: {mask_key(LANGSMITH_API_KEY)}")

# URL 파싱
url_parts = urlparse(LANGSMITH_ENDPOINT)
hostname = url_parts.netloc
print(f"호스트명: {hostname}")

# 1. DNS 확인 테스트
print("\n1. DNS 확인 테스트:")
try:
    ip_address = socket.gethostbyname(hostname)
    print(f"✅ DNS 확인 성공: {hostname} -> {ip_address}")
except socket.gaierror as e:
    print(f"❌ DNS 확인 실패: {hostname} -> {e}")
    sys.exit(1)

# 2. TCP 연결 테스트
print("\n2. TCP 연결 테스트:")
try:
    # 기본 포트는 443(HTTPS)
    port = url_parts.port or (443 if url_parts.scheme == 'https' else 80)
    sock = socket.create_connection((hostname, port), timeout=10)
    sock.close()
    print(f"✅ TCP 연결 성공: {hostname}:{port}")
except socket.error as e:
    print(f"❌ TCP 연결 실패: {hostname}:{port} -> {e}")
    sys.exit(1)

# 3. SSL/TLS 인증서 검증
print("\n3. SSL/TLS 인증서 검증:")
try:
    context = ssl.create_default_context()
    with socket.create_connection((hostname, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            
            # 인증서 정보 출력
            subject = dict(x[0] for x in cert['subject'])
            issued_to = subject.get('commonName', 'Unknown')
            issuer = dict(x[0] for x in cert['issuer'])
            issued_by = issuer.get('commonName', 'Unknown')
            
            print(f"✅ SSL/TLS 연결 성공")
            print(f"   인증서 발급 대상: {issued_to}")
            print(f"   인증서 발급자: {issued_by}")
            print(f"   인증서 만료일: {cert['notAfter']}")
except Exception as e:
    print(f"❌ SSL/TLS 검증 실패: {e}")

# 4. HTTP 요청 테스트 (GET)
print("\n4. HTTP GET 요청 테스트:")
try:
    headers = {
        "Authorization": f"Bearer {LANGSMITH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 요청 정보 출력
    print(f"요청 URL: {LANGSMITH_ENDPOINT}")
    print(f"요청 헤더: {json.dumps({k: (v if k != 'Authorization' else '***') for k, v in headers.items()})}")
    
    # 요청 시도
    response = requests.get(f"{LANGSMITH_ENDPOINT}", headers=headers, timeout=10)
    
    # 응답 정보 출력
    print(f"응답 상태 코드: {response.status_code}")
    print(f"응답 헤더: {json.dumps(dict(response.headers))}")
    
    if response.status_code == 200:
        print("✅ HTTP GET 요청 성공")
    elif response.status_code == 403:
        print("❌ HTTP GET 요청 실패: 403 Forbidden (권한 없음)")
        print("   - API 키를 확인하세요")
        print("   - 계정 권한을 확인하세요")
    elif response.status_code == 401:
        print("❌ HTTP GET 요청 실패: 401 Unauthorized (인증 실패)")
        print("   - API 키가 올바른지 확인하세요")
    else:
        print(f"❌ HTTP GET 요청 실패: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ HTTP 요청 실패: {e}")

# 5. HTTP/2 프로토콜 지원 확인
print("\n5. HTTP/2 프로토콜 지원 확인:")
try:
    # requests는 기본적으로 HTTP/2를 지원하지 않으므로 httpx를 사용해야 함
    # 하지만 HTTP/2 지원 확인만 목적이므로 requests로 헤더만 확인
    response = requests.get(f"{LANGSMITH_ENDPOINT}", headers=headers)
    protocol_version = response.raw.version
    
    if protocol_version == 11:
        print("ℹ️ HTTP/1.1 프로토콜을 사용 중입니다")
        print("   - HTTP/2가 지원되지 않을 수 있습니다")
        print("   - 서버가 HTTP/2를 지원하더라도 클라이언트 라이브러리가 지원하지 않을 수 있습니다")
    elif protocol_version == 20:
        print("✅ HTTP/2 프로토콜을 사용 중입니다")
    else:
        print(f"ℹ️ HTTP 프로토콜 버전: {protocol_version}")
except Exception as e:
    print(f"❌ HTTP/2 프로토콜 확인 실패: {e}")

# 6. LangSmith API 특정 엔드포인트 테스트
print("\n6. LangSmith API 특정 엔드포인트 테스트:")
try:
    headers = {
        "Authorization": f"Bearer {LANGSMITH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # /sessions 엔드포인트 테스트
    response = requests.get(f"{LANGSMITH_ENDPOINT}/sessions", headers=headers, timeout=10)
    print(f"sessions 엔드포인트 응답 코드: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ LangSmith API 세션 조회 성공")
    elif response.status_code == 403:
        print("❌ LangSmith API 세션 조회 실패: 403 Forbidden (권한 없음)")
    elif response.status_code == 401:
        print("❌ LangSmith API 세션 조회 실패: 401 Unauthorized (인증 실패)")
    else:
        print(f"❌ LangSmith API 세션 조회 실패: {response.status_code}")
    
    # /projects 엔드포인트 테스트
    response = requests.get(f"{LANGSMITH_ENDPOINT}/projects", headers=headers, timeout=10)
    print(f"projects 엔드포인트 응답 코드: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ LangSmith API 프로젝트 조회 성공")
        projects = response.json()
        print(f"   프로젝트 수: {len(projects)}")
    elif response.status_code == 403:
        print("❌ LangSmith API 프로젝트 조회 실패: 403 Forbidden (권한 없음)")
    elif response.status_code == 401:
        print("❌ LangSmith API 프로젝트 조회 실패: 401 Unauthorized (인증 실패)")
    else:
        print(f"❌ LangSmith API 프로젝트 조회 실패: {response.status_code}")
except Exception as e:
    print(f"❌ LangSmith API 엔드포인트 테스트 실패: {e}")

# 7. 프록시 설정 확인
print("\n7. 프록시 설정 확인:")
http_proxy = os.environ.get("HTTP_PROXY")
https_proxy = os.environ.get("HTTPS_PROXY")
no_proxy = os.environ.get("NO_PROXY")

if http_proxy or https_proxy:
    print(f"ℹ️ HTTP 프록시: {http_proxy}")
    print(f"ℹ️ HTTPS 프록시: {https_proxy}")
    print(f"ℹ️ 프록시 제외 목록: {no_proxy}")
    print("   - 프록시 설정이 API 연결에 영향을 줄 수 있습니다")
    print("   - 필요한 경우 NO_PROXY에 api.smith.langchain.com을 추가하세요")
else:
    print("✅ 프록시 설정이 감지되지 않았습니다")

print("\n=== HTTPS 연결 테스트 완료 ===")

# 종합 결과 및 해결 방법
print("\n종합 결과 및 해결 방법:")
print("1. 403 Forbidden 오류가 계속 발생하는 경우:")
print("   - LangSmith 계정에서 새 API 키를 발급받으세요")
print("   - API 키가 유효한지 확인하세요")
print("   - 계정의 요금제와 권한을 확인하세요")
print("   - 프로젝트에 접근 권한이 있는지 확인하세요")
print("2. HTTP/2 프로토콜 오류가 발생하는 경우:")
print("   - 클라이언트 라이브러리가 HTTP/2를 지원하는지 확인하세요")
print("   - 프록시나 방화벽이 HTTP/2 트래픽을 차단하지 않는지 확인하세요")
print("   - TLS 1.2 이상을 지원하는지 확인하세요")
print("3. SSL/TLS 연결 오류가 발생하는 경우:")
print("   - 인증서가 유효한지 확인하세요")
print("   - 시스템 시간이 정확한지 확인하세요")
print("   - 필요한 인증 기관(CA) 인증서가 설치되어 있는지 확인하세요") 