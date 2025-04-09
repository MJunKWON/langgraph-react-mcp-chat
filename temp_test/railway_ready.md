# Railway 배포 준비 사항

## 환경 구성 완료

LangSmith API 연결 설정이 완료되었습니다. 다음 항목들이 확인되었습니다:

✅ **LangSmith API 키 설정**:
- 새로운 API 키가 생성되었습니다: `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`
- 환경 변수에 적용되었습니다.

✅ **LangSmith 프로젝트 생성**:
- 프로젝트명: `pr-whispered-mining-89`
- 프로젝트가 성공적으로 생성되었습니다.

✅ **테스트 실행 완료**:
- Hello World 테스트가 성공적으로 실행되었습니다.
- LangSmith 트레이싱이 정상 작동했습니다.

## Railway 배포 체크리스트

다음 항목들을 확인하여 Railway 배포를 진행하세요:

1. **환경 변수 설정**
   - `.env.example` 파일이 업데이트되었습니다.
   - Dockerfile에 LangSmith 환경 변수가 설정되었습니다.

2. **빌드 설정**
   - `railway.json`에 Dockerfile 경로가 올바르게 설정되어 있습니다.
   - 필요한 경우 배포 설정을 업데이트하세요.

3. **API 키 보안**
   - Railway 대시보드에서 환경 변수를 설정하여 API 키를 안전하게 관리하세요.
   - `.env` 파일은 `.gitignore`에 추가되어 있으므로 실제 API 키는 GitHub에 올라가지 않습니다.

## 배포 방법

1. Railway CLI가 설치되어 있는지 확인합니다:
   ```bash
   npm i -g @railway/cli
   ```

2. Railway에 로그인합니다:
   ```bash
   railway login
   ```

3. 프로젝트를 Railway에 연결합니다:
   ```bash
   railway link
   ```

4. 배포를 실행합니다:
   ```bash
   railway up
   ```

5. 또는 Railway 대시보드에서 GitHub 저장소를 연결하여 자동 배포를 설정할 수 있습니다.

## 배포 후 확인 사항

- 배포된 애플리케이션의 URL을 확인합니다.
- 테디플로우에서 연결 설정 시 Railway URL을 사용하세요.
- LangSmith 대시보드에서 트레이싱이 정상적으로 기록되는지 확인하세요. 