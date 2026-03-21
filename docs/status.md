# Status

> 마지막 업데이트: 2026-03-21

## 현재 작업 모드

- `협업 모드`
- 의미:
  - 사용자의 중간 질문, 선택, 방향 수정 의도를 더 자주 반영하면서 함께 진행한다.
  - 비사소한 작업 단위의 시작 게이트는 항상 `docs/AGENT.md`다.
  - 새 단계 착수 전, 결과 정리 전, 커밋/푸시 전에는 `docs/README.md`와 이 문서를 다시 읽고 기준을 맞춘다.

## 현재 목표

- 이메일 자동화 프로젝트의 운영 문서 체계와 모듈 구조를 먼저 고정한다.
- v1 전달 범위를 `이메일 수신 -> 분석 -> Excel 출력` 경로로 명확히 잡는다.
- Python 직접 실행과 Windows `exe` 패키징이 모두 가능한 방향으로 초기 구조를 잡는다.
- GUI에서 사용자별 프로필을 만들고, 그 프로필 설정으로 자동화가 동작하는 흐름을 기본 사용 방식으로 잡는다.
- 사용자는 이메일 주소와 인증 정보만 입력하고, 메일 서버/프로토콜 설정은 앱이 자동 탐지해 보정하는 흐름을 기본으로 잡는다.
- `secrets/사용자 설정` 아래의 예시 이메일과 기대 산출물은 레퍼런스 fixture로만 사용하고 자동 수정 대상에서 제외한다.
- 프로필마다 레퍼런스 Excel 문서가 다를 수 있으므로, 출력 열 구조도 프로필별 템플릿 기준으로 해석하는 방향을 잡는다.
- 현재 fixture 2건에 과적합하지 않고, 텍스트/HTML/이미지 캡처/이미지 안 표/스캔 PDF/ZIP 복합 첨부까지 포괄하는 입력 처리 방향을 잡는다.
- reply draft / 자동 발송 / 외부 알림은 위 기본 경로가 실제로 선 뒤에 붙인다.
- mailbox provider, 내부 데이터 계약, Excel row schema, action policy를 순서대로 설계할 준비를 한다.

## 현재 고정 기준

- 문서 시작 게이트: `docs/AGENT.md -> docs/README.md -> docs/status.md`
- 현재 활성 모드: `협업 모드`
- 제품 기본 방향: `이메일 수신 -> 구조화 분석 -> Excel 출력`을 먼저 완성하고, 답장/알림은 다음 단계로 둔다.
- 배포 목표: 개발 중에는 Python으로 직접 실행하고, 최종적으로는 Windows `exe` 패키징 가능 형태를 지향한다.
- 기본 사용 방식: GUI에서 프로필을 생성하고, 저장된 프로필 기준으로 메일 계정과 자동화 설정을 불러와 실행한다.
- 프로필 저장 방식: 초기 버전은 실행 파일 인접 디렉토리의 로컬 `json` 파일 저장을 허용한다.
- 메일 설정 탐지 방식: 이메일 주소와 인증 정보만 입력받고, protocol / host / port / security 후보는 자동 탐지 후 GUI에 표시한다.
- 탐지 구현 기준: 도메인 규칙, provider 프리셋, autodiscover/autoconfig, 접속 테스트를 우선하고 LLM은 보조 fallback으로 제한한다.
- 레퍼런스 데이터 기준: `secrets/사용자 설정/<이름>/...` 안의 예시 텍스트와 기대 산출물은 학습/비교용 reference로만 사용하고, 프로그램이 직접 덮어쓰지 않는다.
- 수신 메일 보관 기준: canonical 원본은 `.eml`로 저장하고, 사용자가 편하게 열어볼 수 있는 파생본은 `.html` preview를 기본으로 둔다. PDF는 선택적 파생본으로만 본다.
- 메일별 산출물 기준: 수신 메일마다 `raw email + preview + attachment 추출물 + 요약/분석 문서`를 하나의 관리 단위로 남긴다.
- 내부 데이터 흐름 기준: `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4단계 계약으로 계층을 나눈다.
- 템플릿 기준: `ExtractedRecord`의 공통 의미 필드는 유지하되, 실제 Excel 열 구조와 시트/헤더/스타일 규칙은 프로필별 레퍼런스 Excel 템플릿에서 읽어온다.
- LLM 역할 기준: 프로필 템플릿의 열 의미 해석, 필드 매핑 보조, 요약/정리 문장 생성에 사용한다.
- 코드 역할 기준: 실제 workbook의 행 위치, 셀 쓰기, 스타일 복사, 수식 보존, append 순서를 결정적으로 처리한다.
- 시스템 필드 기준: `번호` 같은 system 필드는 `ExtractedRecord`에서 직접 뽑지 않고, workbook append 단계에서 코드가 자동 생성한다.
- 코드 스타일 기준: 가독성만을 이유로 class를 피하지 않고, 재사용성과 유지보수성이 좋아지면 객체지향 설계와 표준 Python 문법을 사용한다. 단, 과한 추상화는 피한다.
- Excel 갱신 기준: 사용자가 직접 수정할 수 있는 문서를 기본으로 보고, AI는 기존 사람이 작성한 내용 뒤에 append하며 기존 스타일과 수식을 최대한 보존한다.
- 요약 기준: 신청서 내용을 기초로 하되, 중복 표현을 줄이고 사람이 읽기 쉬운 한줄/짧은 문단 요약을 생성한다.
- 입력 해석 기준: 본문 텍스트가 없어도 inline 이미지, 첨부 이미지, 스캔 PDF, 이미지 속 표에서 필요한 정보를 추출할 수 있는 방향을 기본값으로 둔다.
- 구현 우선순위: 현재 샘플 2건을 smoke fixture로만 쓰고, 설계는 더 일반적인 메일 입력 변형을 커버하도록 잡는다.
- 커밋 정책: 안정된 마일스톤마다 local commit을 기본으로 남기고, 원격에 남길 가치가 있는 마일스톤이면 push까지 같은 흐름에서 점검한다.
- LLM 기본 방향: ChatGPT API 기반 structured output 우선
- 워크스페이스 기준: `repo / envs / results / secrets` sibling 구조를 지향
- Python 환경 기준: 시스템 Python에 직접 패키지를 깔지 않고, 기본 개발 환경은 `envs/venv` 같은 프로젝트 전용 가상환경 하나를 기준으로 맞춘다.
- 권한 요청 기준: 더 표준적이거나 안정적인 경로에 sudo 비밀번호나 자격 증명이 필요하면, 우회 전에 먼저 사용자에게 그 필요를 설명하고 요청한다.
- 민감 정보 기준: 실제 메일 원문, 첨부파일, 계정 정보, API 키는 문서나 Git 추적 자산에 넣지 않고 로컬 런타임 경로에서만 관리한다.

## 모듈 상태

| 모듈 | 상태 | 메모 |
|---|---|---|
| Mailbox | 기본 schema 클래스 골격 있음 | `MailBundle`, `NormalizedMessage` 객체 계약 정의 |
| Analysis | schema + fixture analysis/export smoke 진입점 있음 | `ExtractedRecord` 계약, fixture loader, structured output schema, end-to-end smoke 스크립트 정의 |
| Exports | template schema/reader + semantic mapping + record projection + workbook append 있음 | rule 기반 열 의미 매핑, `ExtractedRecord -> 템플릿 열` 연결, 결과 workbook append와 스타일 상속 검증 완료 |
| LLM | wrapper + usage logging 골격 있음 | OpenAI Responses wrapper, JSONL usage log, 비용 추정 집계 정의 |

## 핵심 메모

- 현재 리포는 코드보다 운영 틀을 먼저 고정하는 초기 단계다.
- 현재는 메일 provider 연동보다 먼저 메일 보관 번들, 중간 schema, 프로필별 Excel 템플릿 해석 기준을 고정하는 단계다.
- 레퍼런스 레포에서 가져온 핵심 철학은 아래다.
  - 문서 역할 분리
  - 시작 게이트 고정
  - status를 현재 상태의 단일 기준으로 유지
  - 장시간 작업의 detached 운영과 smoke-first
  - 과도한 추상화보다 주경로 우선
- 배포 형태는 Python 실행형과 Windows `exe`를 함께 고려하므로, 초기부터 OS 종속성이 강한 주경로 설계를 피한다.
- 사용 형태는 개인용 PC의 GUI 앱을 우선하므로, 초반부터 CLI-only 흐름보다 `프로필 생성 -> 저장 -> 실행` 경로를 기준으로 설계한다.
- 보안 강화는 현재 최우선 범위가 아니지만, 실제 프로필 파일은 커밋 대상이 아닌 로컬 런타임 산출물로 취급한다.
- 메일 설정 자동 탐지는 실제 접속 성공 여부가 중요하므로, LLM 단독 추론보다 룰베이스와 probe 기반 검증을 우선한다.
- 예시 메일과 기대 산출물은 fixture이므로, 실제 구현 검증에 참고하되 원본 자체를 수정하는 방식으로 작업하지 않는다.
- 수신 메일 열람성은 PDF보다 HTML preview가 유리하고, 원본 보존성은 `.eml`이 유리하므로 두 층을 분리한다.
- 실제 신청 메일은 사용자가 AI를 전제로 작성하지 않은 경우가 많으므로, 비정형 이미지/캡처/표 기반 입력도 기본적으로 들어온다고 가정한다.
- 현재 제품 요구는 아직 넓게 열려 있으므로, provider와 세부 taxonomy를 성급히 고정하지 않는다.
- workflow, reply, notification 같은 후속 계층은 실제 구현이 시작될 때 디렉토리와 문서를 추가한다.
- 단, 답장 자동화는 안전성 때문에 기본적으로 `draft 우선` 기준을 유지한다.

## 진행 체크포인트

1. 완료: `TemplateProfile` 공통 의미 키 목록과 템플릿 열 의미 매핑 schema를 정의한다.
2. 완료: `ExtractedRecord` 공통 필드와 프로필별 Excel 열을 연결하는 규칙을 정한다.
3. 완료: fixture 2건에 대해 첫 live 분석 smoke를 실행해 `ExtractedRecord` JSON 결과와 usage/cost log를 남긴다.
4. 완료: 템플릿 의미 키 부여를 위한 실제 rule 기반 매핑 절차와 system field 처리 기준을 정한다.
5. 완료: workbook append와 스타일 상속 규칙을 구현하고 fixture 결과 workbook을 생성한다.
6. 완료: fixture 기반 `mailbox -> analysis -> exports` 첫 runnable smoke를 만들고 실제 workbook까지 생성한다.

## 다음 작업

1. 현재 rule 기반 템플릿 의미 매핑을 LLM fallback과 함께 어떻게 섞을지 최소 절차를 정한다.
2. generated workbook 결과와 reference fixture의 차이를 비교하는 회귀 확인 방식을 정한다.
3. fixture smoke 결과를 기반으로 실제 mailbox 연동 전에 어떤 artifact 저장 경로를 먼저 고정할지 정한다.
