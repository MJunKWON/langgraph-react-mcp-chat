# Railway 배포 가이드

LangGraph ReAct MCP Chat 애플리케이션을 Railway에 도커로 배포하는 방법을 안내합니다.

## 사전 준비사항

1. [Railway 계정](https://railway.app/) 생성 및 로그인
2. Railway CLI 설치 (선택 사항)
```bash
npm i -g @railway/cli
```

## 배포 단계

### 1. 환경 변수 설정

`.env.example` 파일을 참고하여 필요한 환경 변수를 준비합니다:
- `ANTHROPIC_API_KEY`: Anthropic API 키
- `OPENAI_API_KEY`: OpenAI API 키
- `USE_MODEL`: 사용할 모델 설정 (기본값: openai)

### 2. Railway 프로젝트 생성

1. Railway 대시보드에서 새 프로젝트 생성
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 연결 및 권한 부여
4. 프로젝트 저장소 선택

### 3. 환경 변수 설정

Railway 대시보드에서 "Variables" 탭으로 이동하여 `.env.example`에 명시된 환경 변수를 추가합니다.

### 4. 배포 설정

Railway는 자동으로 프로젝트의 `Dockerfile`과 `railway.json`을 인식하여 빌드 및 배포합니다. 
기본적으로 설정을 변경할 필요가 없습니다.

### 5. 배포 완료 및 확인

배포가 완료되면 Railway가 제공하는 도메인을 통해 애플리케이션에 접근할 수 있습니다:
- API 엔드포인트: `https://[your-app-name].railway.app`
- 연결 정보: `https://[your-app-name].railway.app`에 접속하여 상태 확인

## 테디플로우 연결 방법

테디플로우에서 Railway에 배포된 앱에 연결하려면:

1. 테디플로우 로그인 후 "새로운 앱 연결" 클릭
2. 앱 이름 입력 후 "연결" 클릭
3. "LangGraph" 탭 선택 후 다음 정보 입력:
   - Endpoint: `https://[your-app-name].railway.app`
   - Graph: `agent`
4. "저장" 버튼 클릭

## 문제 해결

1. 로그 확인: Railway 대시보드의 "Logs" 탭에서 애플리케이션 로그 확인
2. 환경 변수 확인: API 키가 올바르게 설정되었는지 확인
3. 네트워크 연결: Railway 제공 도메인이 방화벽에 차단되지 않았는지 확인

## 참고 사항

- Railway는 기본적으로 HTTPS를 지원합니다.
- 무료 플랜에는 사용량 제한이 있으므로 필요에 따라 유료 플랜으로 업그레이드하세요.
- 장시간 사용하지 않으면 애플리케이션이 절전 모드로 전환될 수 있습니다. 