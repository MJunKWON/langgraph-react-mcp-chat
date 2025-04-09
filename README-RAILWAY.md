# Railway 배포 안내

이 프로젝트는 [Railway](https://railway.app/)를 사용하여 배포할 수 있도록 구성되었습니다.

## 배포 전 필수 확인사항

1. **API 키 설정**
   - Anthropic API 키와 OpenAI API 키를 Railway 환경 변수에 설정해야 합니다.

2. **MCP 서버 구성**
   - `src/react_agent/mcp_config.json` 파일이 올바르게 구성되었는지 확인하세요.
   - 이 파일은 Model Context Protocol(MCP) 도구를 정의합니다.

3. **환경 변수**
   - `.env.example`을 참고하여 필요한 환경 변수를 Railway에 설정하세요.

## 배포 과정

자세한 배포 과정은 `DEPLOYMENT.md` 파일을 참고하세요.

## 주의사항

- 이 애플리케이션은 2024 포트에서 실행됩니다.
- Railway는 기본적으로 HTTPS를 지원합니다.
- Railway 무료 플랜에는 사용량 제한이 있습니다.

## 테디플로우 연결

배포된 애플리케이션은 다음 정보로 테디플로우에 연결할 수 있습니다:
- Endpoint: `https://[your-app-name].railway.app`
- Graph: `agent` 