# Email Agent

이 리포지토리는 ChatGPT API를 활용해 이메일을 읽고, 분류하고, 필요한 정보를 구조화해 Excel로 내보내는 소프트웨어를 만들기 위한 시작점이다. 현재는 미래 확장용 구조를 과하게 미리 늘리지 않고, `이메일 수신 -> 분석 -> Excel 출력`의 주경로를 먼저 고정하는 단계다. 장기적으로는 Python으로 직접 실행할 수 있으면서도, Windows 환경에서 `exe`로 패키징해 실행 가능한 형태를 함께 목표로 한다. 사용자 경험은 개인용 데스크톱 앱을 우선으로 보고, GUI에서 프로필을 만들고 그 프로필 설정으로 자동화가 동작하는 흐름을 지향한다. 다만 구현 순서는 GUI 화면보다 메일 설정/수신/분석 엔진을 텍스트 기반 smoke로 먼저 검증한 뒤 그 위를 감싸는 방향을 우선한다. 메일 연동 설정은 사용자가 이메일 주소와 인증 정보만 입력하면 앱이 가능한 프로토콜과 서버 설정을 자동 탐지해 GUI에 채워주는 방향을 기본으로 둔다. 사용자별 예시 메일과 기대 산출물은 `secrets/사용자 설정/<이름>/참고자료/` 아래에 레퍼런스 fixture로 보관하고, 실제 런타임 메일/엑셀/로그는 같은 프로필 아래 `실행결과/` 계층으로 분리해 관리한다. 입력 형식은 현재 샘플 두 건에 맞추지 않고, 텍스트/HTML/inline 이미지/첨부 이미지/스캔 PDF/ZIP 안 문서/이미지 안 표까지 포괄하는 방향을 기본으로 둔다. 이미지 첨부가 있으면 텍스트 요약만 보내지 않고 실제 이미지를 함께 보는 멀티모달 입력을 기본으로 삼는다. 현재 내부 데이터 흐름은 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 네 단계 계약으로 고정해 간다. 단, `ExportRow`의 실제 열 구조는 프로젝트 전체에서 하나로 고정하지 않고, 사용자 프로필 폴더의 레퍼런스 Excel 템플릿을 해석해 프로필별로 달라질 수 있게 설계한다.

## 현재 범위

- 수신 이메일 동기화와 정규화
- LLM 기반 분류 / 추출 / 요약
- Excel 출력 자동화
- Python 실행형과 Windows `exe` 패키징을 함께 고려한 구조 설계
- GUI 기반 프로필 생성/선택과 로컬 설정 파일 저장
- 도메인 규칙, autodiscover, 접속 테스트 기반 메일 설정 자동 탐지
- 수신 이메일 `raw eml + html preview + attachment bundle + summary doc` 보관
- 프로필별 레퍼런스 Excel 템플릿 해석과 그에 맞는 출력 매핑
- 사람이 수정하는 Excel 문서를 존중하는 append 중심 업데이트
- 이미지 기반 정보와 표가 포함된 메일/첨부까지 처리 가능한 multimodal 입력 해석
- 이후 reply draft와 외부 알림으로 확장 가능한 설계 준비

## 현재 활성 디렉토리

| 디렉토리 | 역할 | 상태 |
|---|---|---|
| [mailbox](mailbox/README.md) | 메일 수집, 번들 보관, 정규화 입력 생성 | 기본 schema 클래스 골격 있음 |
| [analysis](analysis/README.md) | 분류, 정보 추출, 요약, schema 정규화 | fixture analysis/export smoke 진입점 있음 |
| [exports](exports/README.md) | Excel 출력, 템플릿 해석, workbook 반영 | 템플릿 해석, projection, workbook append, regression check 규칙 있음 |
| [llm](llm/README.md) | OpenAI 호출, prompt, structured response | wrapper + usage log + 성능 우선 LLM orchestration 기준 있음 |

workflow routing, reply draft, notification은 실제 구현이 시작될 때 디렉토리를 추가한다.

## 시작 문서

1. [docs/AGENT.md](docs/AGENT.md)
2. [docs/README.md](docs/README.md)
3. [docs/status.md](docs/status.md)
4. 필요한 모듈의 `README.md`
5. [docs/decisions.md](docs/decisions.md)
6. [docs/logbook.md](docs/logbook.md)

## 문서 역할 요약

| 문서 | 역할 |
|---|---|
| [docs/status.md](docs/status.md) | 현재 상태와 다음 작업의 단일 기준 |
| [docs/개발방침.md](docs/개발방침.md) | 장기적으로 유지할 운영 원칙 |
| [docs/decisions.md](docs/decisions.md) | 현재 유효한 핵심 결정 |
| [docs/logbook.md](docs/logbook.md) | 최근 작업 로그 |

## 리포 구조

```text
.
├── mailbox/
├── analysis/
├── exports/
├── llm/
└── docs/
```

로컬 워크스페이스는 보통 `repo/`, `envs/`, `results/`, `secrets/`를 같은 상위 루트 아래 sibling으로 둔다. Python 개발 의존성은 기본적으로 `envs/venv` 같은 프로젝트 전용 가상환경에만 설치한다. 현재 리포의 Python 패키지 목록은 [`requirements.txt`](requirements.txt)로 관리한다. Git으로 추적할 공식 상태와 운영 기준은 이 리포 안의 문서를 기준으로 유지하고, 실제 프로필 기반 reference/runtime 자산은 기본적으로 `secrets/사용자 설정/<이름>/참고자료/`, `secrets/사용자 설정/<이름>/실행결과/` 아래에서 관리한다.
