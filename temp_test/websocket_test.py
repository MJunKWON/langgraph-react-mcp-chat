"""
WebSocket 연결 테스트 스크립트

이 스크립트는 WebSocket 서버에 대한 연결을 테스트하고 잠재적인 문제를 진단합니다.
"""

import os
import sys
import json
import time
import asyncio
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

try:
    import websockets
except ImportError:
    print("websockets 패키지가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install websockets")
    sys.exit(1)

# 기본 WebSocket 엔드포인트
DEFAULT_WEBSOCKET_URL = "wss://server.smithery.ai/@smithery-ai/server-sequential-thinking"
WEBSOCKET_URL = os.environ.get("WEBSOCKET_URL", DEFAULT_WEBSOCKET_URL)

# 테스트 설정
MAX_RECONNECT_ATTEMPTS = int(os.environ.get("LANGGRAPH_WEBSOCKET_MAX_RECONNECT_ATTEMPTS", "3"))
RECONNECT_INTERVAL = int(os.environ.get("LANGGRAPH_WEBSOCKET_RECONNECT_INTERVAL", "2000")) / 1000
PING_INTERVAL = int(os.environ.get("LANGGRAPH_WEBSOCKET_PING_INTERVAL", "30000")) / 1000
PING_TIMEOUT = int(os.environ.get("LANGGRAPH_WEBSOCKET_PING_TIMEOUT", "10000")) / 1000
TEST_DURATION = 30  # 테스트 실행 시간(초)

print(f"=== WebSocket 연결 테스트 시작 ===")
print(f"WebSocket URL: {WEBSOCKET_URL}")
print(f"최대 재연결 시도 횟수: {MAX_RECONNECT_ATTEMPTS}")
print(f"재연결 간격: {RECONNECT_INTERVAL}초")
print(f"Ping 간격: {PING_INTERVAL}초")
print(f"Ping 타임아웃: {PING_TIMEOUT}초")
print(f"테스트 지속 시간: {TEST_DURATION}초")

# 결과 통계
connection_attempts = 0
successful_connections = 0
failed_connections = 0
reconnections = 0
messages_sent = 0
messages_received = 0
connection_errors = {}


async def test_websocket_connection():
    """WebSocket 연결을 테스트합니다."""
    global connection_attempts, successful_connections, failed_connections, reconnections
    global messages_sent, messages_received, connection_errors
    
    for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
        connection_attempts += 1
        
        try:
            print(f"\n시도 {attempt}/{MAX_RECONNECT_ATTEMPTS}:")
            print(f"WebSocket 연결 중: {WEBSOCKET_URL}")
            
            async with websockets.connect(
                WEBSOCKET_URL,
                ping_interval=PING_INTERVAL,
                ping_timeout=PING_TIMEOUT,
                close_timeout=5
            ) as websocket:
                successful_connections += 1
                print(f"✅ WebSocket 연결 성공!")
                
                # 간단한 PING 메시지 전송
                test_message = json.dumps({"type": "ping", "timestamp": time.time()})
                await websocket.send(test_message)
                messages_sent += 1
                print(f"📤 메시지 전송됨: {test_message}")
                
                # 응답 대기
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    messages_received += 1
                    print(f"📥 응답 수신됨: {response}")
                except asyncio.TimeoutError:
                    print("⚠️ 응답 타임아웃")
                
                # 연결 유지 테스트
                print(f"연결 유지 테스트 ({min(10, TEST_DURATION)}초)...")
                for i in range(min(10, TEST_DURATION)):
                    try:
                        keep_alive = json.dumps({"type": "keepalive", "timestamp": time.time()})
                        await websocket.send(keep_alive)
                        messages_sent += 1
                        await asyncio.sleep(1)
                        if i % 2 == 0:
                            print(f"연결 유지 중... ({i+1}/{min(10, TEST_DURATION)})")
                    except websockets.exceptions.WebSocketException as e:
                        print(f"❌ 연결 유지 중 오류 발생: {e}")
                        error_type = type(e).__name__
                        connection_errors[error_type] = connection_errors.get(error_type, 0) + 1
                        break
                
                # 정상적인 연결 종료
                await websocket.close()
                print("WebSocket 연결 정상 종료")
                return True
                
        except Exception as e:
            failed_connections += 1
            error_type = type(e).__name__
            connection_errors[error_type] = connection_errors.get(error_type, 0) + 1
            print(f"❌ 연결 실패: {e}")
            
            if attempt < MAX_RECONNECT_ATTEMPTS:
                reconnections += 1
                print(f"재연결 시도 중... {RECONNECT_INTERVAL}초 후 재시도")
                await asyncio.sleep(RECONNECT_INTERVAL)
            else:
                print(f"최대 재연결 시도 횟수 도달")
                return False
    
    return False

async def main():
    """메인 테스트 함수"""
    start_time = time.time()
    
    # 연결 테스트 수행
    connection_successful = await test_websocket_connection()
    
    # 테스트 결과 출력
    elapsed_time = time.time() - start_time
    print("\n=== WebSocket 연결 테스트 결과 ===")
    print(f"테스트 소요 시간: {elapsed_time:.2f}초")
    print(f"연결 시도 횟수: {connection_attempts}")
    print(f"성공한 연결: {successful_connections}")
    print(f"실패한 연결: {failed_connections}")
    print(f"재연결 시도: {reconnections}")
    print(f"전송한 메시지: {messages_sent}")
    print(f"수신한 메시지: {messages_received}")
    
    if connection_errors:
        print("\n발생한 오류:")
        for error_type, count in connection_errors.items():
            print(f"  - {error_type}: {count}회")
    
    if connection_successful:
        print("\n✅ WebSocket 연결 테스트 성공!")
    else:
        print("\n❌ WebSocket 연결 테스트 실패!")
    
    # 문제 진단 및 해결 방법
    print("\n문제 진단 및 해결 방법:")
    
    if failed_connections > 0:
        print("1. 연결 실패 문제:")
        print("   - 네트워크 연결 상태를 확인하세요")
        print("   - 방화벽이나 프록시 설정을 확인하세요")
        print("   - WebSocket URL이 올바른지 확인하세요")
        print("   - SSL/TLS 인증서 문제가 있는지 확인하세요")
    
    if messages_sent > messages_received:
        print("2. 메시지 수신 문제:")
        print("   - 서버가 응답하지 않거나 타임아웃이 발생했습니다")
        print("   - Ping 간격과 타임아웃 설정을 확인하세요")
        print("   - 네트워크 지연이 발생하는지 확인하세요")
    
    if "WebSocketConnectionClosedError" in connection_errors:
        print("3. 연결 종료 문제:")
        print("   - 서버에서 연결을 닫았습니다")
        print("   - 연결 유지(keepalive) 메시지 간격을 줄여보세요")
        print("   - LANGGRAPH_KEEP_ALIVE=true 설정을 확인하세요")
    
    if "TimeoutError" in connection_errors:
        print("4. 타임아웃 문제:")
        print("   - 네트워크 지연이 발생했거나 서버 응답이 늦었습니다")
        print("   - 타임아웃 설정을 늘려보세요")
    
    # Dockerfile 설정 제안
    print("\nDockerfile 설정 제안:")
    print("""
ENV LANGGRAPH_WEBSOCKET_MAX_RECONNECT_ATTEMPTS=5
ENV LANGGRAPH_WEBSOCKET_RECONNECT_INTERVAL=5000
ENV LANGGRAPH_WEBSOCKET_PING_INTERVAL=30000
ENV LANGGRAPH_WEBSOCKET_PING_TIMEOUT=10000
ENV LANGGRAPH_KEEP_ALIVE=true
    """)

# 비동기 테스트 실행
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n테스트 실행 중 오류 발생: {e}")
    finally:
        print("\n=== WebSocket 테스트 완료 ===") 