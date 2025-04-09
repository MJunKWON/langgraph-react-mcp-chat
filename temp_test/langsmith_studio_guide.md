# LangSmith Studio 접속 가이드

LangSmith 스튜디오에서 프로젝트를 확인하고 트레이싱을 관리하는 방법입니다.

## 접속 방법

1. **LangSmith 웹사이트 접속**
   - URL: [https://smith.langchain.com](https://smith.langchain.com)
   - 계정이 없으면 가입 후 로그인하세요

2. **로그인하기**
   - 구글, 깃허브 또는 이메일로 로그인할 수 있습니다
   - API 키를 발급받은 계정으로 로그인해야 합니다

## 프로젝트 확인하기

1. **프로젝트 목록 보기**
   - 로그인 후 좌측 메뉴에서 "Projects" 클릭
   - 또는 직접 URL 접속: [https://smith.langchain.com/projects](https://smith.langchain.com/projects)

2. **특정 프로젝트 접속**
   - 프로젝트 목록에서 `pr-whispered-mining-89` 프로젝트를 찾아 클릭
   - 또는 직접 URL 접속: [https://smith.langchain.com/projects/pr-whispered-mining-89](https://smith.langchain.com/projects/pr-whispered-mining-89)

## 트레이싱 확인하기

1. **트레이스 목록 보기**
   - 프로젝트 페이지에서 "Traces" 탭 클릭
   - 최근 실행된 Hello World 테스트 트레이스가 표시됩니다

2. **트레이스 상세 보기**
   - 목록에서 특정 트레이스를 클릭하면 상세 정보를 확인할 수 있습니다
   - 입력/출력, 토큰 사용량, 실행 시간 등 세부 정보 확인 가능

## API 키 관리

1. **API 키 확인**
   - 우측 상단 프로필 아이콘 클릭 → "API Keys" 선택
   - 또는 직접 URL 접속: [https://smith.langchain.com/settings/api-keys](https://smith.langchain.com/settings/api-keys)

2. **새 API 키 생성**
   - "Create API Key" 버튼 클릭
   - 키 이름 입력 후 생성
   - 생성된 키는 한 번만 표시되므로 안전한 곳에 저장

## 프로젝트 생성하기

1. **새 프로젝트 만들기**
   - Projects 페이지에서 "New Project" 버튼 클릭
   - 프로젝트 이름과 설명 입력 후 생성

## 데이터셋과 평가

1. **데이터셋 관리**
   - 좌측 메뉴에서 "Datasets" 클릭하여 데이터셋 관리 가능

2. **평가 실행**
   - 프로젝트 페이지에서 "Evaluations" 탭을 통해 모델 성능 평가 가능

## 문제 해결

만약 프로젝트가 보이지 않거나 트레이싱이 기록되지 않는 경우:

1. API 키가 올바르게 설정되었는지 확인하세요
2. 환경 변수 `LANGSMITH_TRACING=true`가 설정되었는지 확인하세요
3. 올바른 계정으로 로그인했는지 확인하세요 