# Logbook

> 최근 작업만 유지한다. 오래된 상세 로그는 필요해지면 `docs/archive/`로 옮긴다.

## 2026-03-21 | Human + Codex | 프로필별 Excel 템플릿 해석 중심 계획 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `exports/README.md`, `analysis/README.md`였다.
- 사용자는 엑셀 칸이 프로젝트 전체에서 고정되는 것이 아니라, 각 사용자 프로필 폴더의 레퍼런스 Excel 문서에 따라 달라질 것이라고 설명했다.
- 이에 따라 다음 계획을 `전역 고정 ExportRow` 설계에서 `프로필별 템플릿 해석 -> 공통 의미 필드 매핑 -> workbook 쓰기` 순서로 조정했다.
- 문서에는 `공통 의미 필드`와 `프로필별 템플릿 규칙`을 분리하는 기준, LLM이 맡는 부분과 코드가 맡는 부분, 다음 작업 순서를 반영했다.
- 이후에는 계획이 대화에서만 사라지지 않도록, 방향이 바뀔 때마다 `status`, `decisions`, `logbook`을 함께 읽고 갱신하는 흐름으로 계속 진행한다.

## 2026-03-21 | Human + Codex | exports 템플릿 객체 모델과 reader 골격 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `exports/README.md`였다.
- `openpyxl`이 아직 설치되어 있지 않은 상태라서, 의존성 설치보다 먼저 재사용 가능한 `TemplateProfile` 객체 모델과 reader 인터페이스를 추가하는 쪽이 적절하다고 판단했다.
- 이에 따라 `exports/schema.py`에 `TemplateProfile`, `TemplateSheet`, `TemplateColumn`을 추가했다.
- `exports/template_profile.py`에는 레퍼런스 Excel을 읽어 템플릿 초안을 만드는 `TemplateWorkbookReader` 골격과 `read_template_profile` helper를 추가했다.
- 실제 열 의미 해석과 semantic key 부여는 다음 단계에서 LLM 매핑 계층으로 이어가기로 했다.

## 2026-03-21 | Human + Codex | Python 개발 환경을 envs/venv 기준으로 고정

- 사용자는 시스템 Python 대신 워크스페이스 `envs` 아래 venv를 써서 의존성을 관리하길 원했다.
- 확인 결과 현재 시스템 `python3`에는 `pip`가 없고, `envs/`는 비어 있었다.
- 이에 따라 Python 의존성은 시스템에 직접 설치하지 않고 `envs/venv`를 기본 개발 환경으로 두는 기준을 문서에 반영했다.
- `python3.10-venv`를 시스템에 설치할 sudo 권한은 없어 `venv --without-pip` + `get-pip.py` 방식으로 `envs/venv`를 부트스트랩했다.
- 이후 `envs/venv` 안에 `openpyxl`을 설치했고, 현재 리포의 Python 패키지 목록은 `requirements.txt`로 관리하기 시작했다.
- 이후 사용자가 sudo 비밀번호를 제공해 주어 `python3.10-venv`를 설치했고, 현재 이 머신은 표준 `python3 -m venv` 경로도 정상 동작한다.

## 2026-03-21 | Human + Codex | 권한이 필요한 정석 경로는 먼저 사용자에게 묻는 기준 추가

- 사용자는 권한이나 비밀번호가 필요한 더 좋은 경로가 있으면, 우회 전에 먼저 사용자에게 물어서 정석 경로로 진행하길 원했다.
- 이에 따라 `docs/개발방침.md`에 권한/비밀번호/자격 증명 관련 정보가 필요할 때의 기본 행동 기준을 추가했다.
- 앞으로는 가능한 표준 경로가 권한 제공에 달려 있으면 먼저 그 사실을 설명하고 사용자 선택을 받은 뒤 진행한다.

## 2026-03-21 | Human + Codex | 체크포인트 1 - 템플릿 의미 키 catalog와 mapping schema 추가

- 사용자는 이후 계획을 체크포인트로 명시하고 하나씩 수행하길 원했다.
- 이에 따라 `docs/status.md`에 현재 체크포인트 목록을 추가하고, 먼저 1번 작업으로 템플릿 열 의미 해석에 필요한 공통 의미 키 catalog와 mapping schema를 구현했다.
- `exports/semantic_mapping.py`에 `SemanticFieldDefinition`, `TemplateColumnSemanticMapping`, `TemplateSemanticMapping`, `apply_template_semantic_mapping`를 추가했다.
- v1 기준 공통 의미 키는 기업명, 담당자명, 연락처, 이메일, 홈페이지/SNS, 산업군, 제품/서비스, 신청목적, 요약 필드, 내부 관리 필드 등을 포함하도록 시작했다.

## 2026-03-21 | Human + Codex | 체크포인트 2 - `ExtractedRecord -> 템플릿 열` projection 규칙 추가

- 체크포인트 2의 목표는 분석 결과 공통 필드를 프로필별 Excel 열과 연결하는 규칙을 코드로 고정하는 것이었다.
- `exports/record_projection.py`에 `ResolvedSemanticValue`, `ResolvedRecordProjection`, `ProjectedTemplateValue`, `ProjectedTemplateRow`와 관련 helper를 추가했다.
- 기본 전략은 `analysis` 계층 필드명이 의미 키와 정확히 같으면 그대로 쓰고, 그렇지 않아도 alias 목록과 요약 fallback으로 최대한 같은 공통 의미 키에 연결하는 방식이다.
- 이후 실제 템플릿 열에는 `semantic_key`가 붙어 있으면 `project_record_to_template()`가 순서대로 workbook 쓰기 직전 값 목록을 만들 수 있게 했다.

## 2026-03-21 | Human + Codex | 체크포인트 3 준비 - OpenAI wrapper와 fixture smoke 골격 추가

- 사용자는 ChatGPT API를 쓸 때 반드시 공용 wrapper를 거치고, 사용 로그를 바탕으로 토큰량과 예상 비용을 계산할 수 있길 원했다.
- 이에 따라 `llm/` 계층에 OpenAI Responses wrapper, JSONL usage logger, 가격표 snapshot 기반 비용 계산기를 추가했다.
- 사용 로그 기본 경로는 `../results/llm/openai_usage.jsonl`로 두었고, 기본 가격표는 `2026-03-21` 기준 OpenAI 공식 가격 페이지 snapshot으로 시작했다.
- 동시에 `analysis/fixture_smoke.py`와 `analysis/llm_extraction.py`를 추가해, fixture 이메일 본문 + ZIP 내부 파일 목록 + ZIP 안 XLSX 텍스트 요약을 LLM 입력으로 묶는 첫 smoke 진입점을 만들었다.
- 현재 환경에는 `OPENAI_API_KEY`가 없어서 실제 live 호출까지는 아직 실행하지 않았고, dry-run으로 입력 조립과 wrapper 집계 동작만 먼저 확인했다.

## 2026-03-21 | Human + Codex | 체크포인트 3 완료 - fixture 2건 live 분석 smoke 실행

- 사용자가 `secrets/chatgpt_api_key.txt`에 API 키를 두었다고 알려주어, wrapper가 환경 변수 우선 후 로컬 키 파일을 fallback으로 읽게 했다.
- 이후 fixture 2건에 대해 실제 OpenAI live 호출을 실행했고, `ExtractedRecord` JSON 결과를 `results/analysis_smoke/` 아래에 남겼다.
- usage log는 `results/llm/openai_usage.jsonl`에 2건이 누적되었고, 현재 두 호출 합산 기준 `input_tokens=2692`, `output_tokens=1970`, `estimated_total_cost_usd=0.03628`로 집계됐다.
- 이제 체크포인트 3은 완료로 보고, 다음 단계는 템플릿 열 의미 키의 실제 rule/LLM 매핑 절차로 넘어간다.

## 2026-03-21 | Human + Codex | 객체지향 허용 기준 복원과 schema 클래스 구조 복귀

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `mailbox/README.md`, `analysis/README.md`였다.
- 사용자는 `오버엔지니어링 금지` 규칙이 문서에 있는지 다시 확인해달라고 했고, 자신은 객체지향 프로그래밍의 중요성을 높게 보는 사람이라고 설명했다.
- 확인 결과 `오버엔지니어링 금지`는 이미 문서에 있었지만, 직전 턴의 `class보다 함수 중심` 해석은 사용자의 의도보다 과하게 좁혀진 상태였다.
- 이에 따라 코드 스타일 규칙을 `객체지향 허용`, `재사용성과 유지보수성 우선`, `표준 Python 문법 허용`, `과한 추상화만 제한` 방향으로 다시 정리했다.
- `mailbox/schema.py`, `analysis/schema.py`와 각 `__init__.py`는 helper dict 중심 구조에서 다시 class 기반 schema 구조로 되돌렸다.

## 2026-03-21 | Human + Codex | 코드 스타일 단순화 기준 추가와 schema 함수형 리팩토링

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `mailbox/README.md`, `analysis/README.md`였다.
- 사용자는 함수 설명/인자/반환 설명 같은 코드 스타일 규칙과, `@decorator`처럼 친숙하지 않은 Python 문법 제한이 문서에 있는지 확인해달라고 요청했다.
- 확인 결과 `모든 함수는 한국어 docstring으로 기능 / 입력 / 반환을 적는다`는 규칙은 이미 있었지만, 낯선 문법 제한은 아직 없었다.
- 이에 따라 `개발방침`, `status`, `decisions`에 `함수 중심`, `dict/list + helper function 우선`, `decorator와 복잡한 Python 문법은 필요할 때만 사용` 기준을 추가했다.
- 기존 `mailbox/schema.py`, `analysis/schema.py`는 dataclass 기반 구조에서 plain dict와 helper function 기반 구조로 리팩토링했다.
- `__init__.py` 노출 API와 모듈 README도 새 스타일에 맞게 정리했다.

## 2026-03-21 | Human + Codex | 메일 번들과 중간 schema 기본 골격 정의

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `mailbox/README.md`, `analysis/README.md`, `exports/README.md`였다.
- 다음 구현 우선순위는 메일 연동 자체보다 `이메일 보관 번들`, `중간 JSON schema`, `분석 산출물 계약`을 먼저 고정하는 편이 재작업을 줄인다고 판단했다.
- 이에 따라 내부 데이터 흐름을 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4단계로 고정했다.
- `mailbox/`에는 메일 번들 보관 단위와 분석 공통 입력 단위를 나타내는 기본 dataclass 골격을 추가했다.
- `analysis/`에는 evidence 기반 추출 결과를 표현하는 기본 dataclass 골격을 추가했다.
- `status`, `개발방침`, `decisions`, 각 모듈 `README`도 이 기준에 맞게 갱신했다.

## 2026-03-21 | Human + Codex | 협업 모드 전환과 마일스톤 커밋 정책 강화

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 앞으로 이 프로젝트를 `에이전트 모드`가 아니라 `협업 모드`로 운영하길 원한다고 명시했다.
- 또한 커밋은 필요 여부만 소극적으로 점검하는 수준보다, 안정된 마일스톤마다 더 적극적으로 남기는 방향으로 정책을 바꾸길 원했다.
- 이에 따라 `docs/status.md`의 현재 작업 모드를 `협업 모드`로 전환했다.
- `docs/개발방침.md`에는 안정된 마일스톤마다 local commit을 기본으로 남기고, 가치 있는 마일스톤이면 push도 같은 흐름에서 점검하는 기준으로 문구를 강화했다.
- `docs/decisions.md`에는 이 기준을 현재 유효한 핵심 결정으로 추가했다.

## 2026-03-21 | Human + Codex | 샘플 2건 과적합 방지와 multimodal 입력 전제 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `mailbox/README.md`, `analysis/README.md`였다.
- 사용자는 현재 존재하는 수신 이메일 2개만 보고 그 형식에 맞춰 개발하지 말고, 실제로는 이미지 캡처, 이미지 안 표, 스캔 문서 등 AI를 전제로 하지 않은 다양한 이메일 입력을 모두 커버할 수 있게 고민하길 원한다고 설명했다.
- 이에 따라 현재 fixture 2건은 smoke/reference 용도로만 쓰고, 실제 설계는 더 일반적인 이메일 변형을 포괄하는 방향으로 정리했다.
- 문서에는 multimodal 입력 해석, OCR/VLM/table extraction 확장 가능 구조, 샘플 과적합 방지 기준을 반영했다.

## 2026-03-21 | Human + Codex | reference fixture 유지와 메일/엑셀 산출물 관리 기준 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `mailbox/README.md`, `analysis/README.md`, `exports/README.md`였다.
- 사용자는 `secrets/사용자 설정/<이름>/...` 안의 예시 이메일과 기대 산출물은 참고용 레퍼런스일 뿐이며, 프로그램이나 assistant가 직접 수정하면 안 된다고 설명했다.
- 또한 실제 이메일이 연동된 뒤에는 수신 메일을 사람이 편하게 열어볼 수 있는 형식으로 저장하고, 메일별 산출물 문서도 별도로 관리하길 원한다고 정리했다.
- 이에 따라 reference fixture는 read-only로 두고, 실제 수신 메일은 `raw eml + html preview + attachment 추출물 + summary/normalized 문서` 번들로 관리하는 기준을 추가했다.
- Excel 쪽에는 human-first append, 기존 스타일/수식 보존, 신청서 기반 readable summary 원칙을 반영했다.

## 2026-03-21 | Human + Codex | GUI 프로필의 메일 설정 자동 탐지 방향 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `mailbox/README.md`, `llm/README.md`였다.
- 사용자는 GUI에서 이메일 정보만 입력하면, 앱이 IMAP / POP / SMTP 등 가능한 설정을 알아서 실험하고 맞는 세팅값을 GUI에 같이 보여주길 원한다고 설명했다.
- 이에 따라 제품 기본 사용 흐름에 `최소 입력 -> 자동 탐지 -> GUI 반영 -> 저장` 단계를 추가했다.
- 구현 원칙은 `LLM 중심`이 아니라 `도메인 규칙 / provider 프리셋 / autodiscover / 접속 테스트 우선, LLM은 보조 fallback`으로 정리했다.
- 이 기준은 `status`, `개발방침`, `decisions`, `mailbox/README.md`, `llm/README.md`에 반영했다.

## 2026-03-21 | Human + Codex | GUI 프로필 기반 실행과 로컬 JSON 프로필 저장 방향 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 이 프로젝트가 Python 또는 Windows `exe`로 실행되더라도, 실제 사용은 GUI에서 프로필을 만들고 그 프로필에 이메일 계정 정보를 저장한 뒤 자동으로 동작하길 원한다고 설명했다.
- 또한 개인용 PC 전제를 바탕으로, 프로필 정보는 실행 파일 인접 디렉토리에 생성되는 로컬 `json` 파일 형태로 저장해도 괜찮다고 정리했다.
- 이에 따라 현재 목표와 고정 기준에는 GUI 프로필 기반 사용 흐름과 로컬 프로필 파일 저장 기준을 추가했다.
- `docs/개발방침.md`에는 GUI-first 사용 흐름과 로컬 프로필 파일을 Git 추적 대상이 아닌 런타임 자산으로 보는 원칙을 반영했다.

## 2026-03-21 | Human + Codex | Windows exe 배포 목표를 문서 기준에 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 이 프로젝트가 Python으로 실행 가능해야 할 뿐 아니라, 최종적으로는 Windows에서 실행 가능한 `exe` 형태도 지원하길 원한다고 설명했다.
- 이에 따라 현재 목표와 고정 기준에는 Python 실행 + Windows `exe` 패키징 목표를 추가했다.
- `docs/개발방침.md`에는 Linux 전용 가정과 셸 의존 진입점을 주경로에 넣지 않는 packaging-aware 원칙을 반영했다.
- `docs/decisions.md`에는 이 요구를 현재 유효한 핵심 결정으로 기록했다.

## 2026-03-21 | Human + Codex | 비효율적 요청에는 더 나은 큰 그림을 먼저 제시하는 원칙 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 자신이 이메일 자동화 프로젝트 경험이 적기 때문에, 앞으로 비효율적이거나 두서 없는 요청을 할 수 있다고 설명했다.
- 이에 따라 assistant는 요청을 그대로 세부 실행으로 옮기기보다, 비효율적인 부분을 짚고 더 나은 큰 그림과 권장 순서를 먼저 제시하는 태도를 기본 원칙으로 반영했다.
- 이 기준은 `AGENT.md`, `개발방침.md`, `decisions.md`에 모두 반영했다.

## 2026-03-21 | Human + Codex | `repo/` 안에 Git 저장소 초기화

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 `.git` 디렉토리가 반드시 `repo/` 안에 생성되길 원했다.
- 이에 따라 `repo/`에서 `git init -b main`을 수행해 로컬 Git 저장소를 초기화했다.
- 현재 로컬 커밋 작성용 `user.name`, `user.email`도 `repo/.git/config`에 최소 범위로 설정했다.
- 현재 작업 트리를 초기 커밋으로 묶었고, GitHub 원격 `origin`도 연결했다.
- 첫 푸시는 일회성 인증 URL로 수행한 뒤, branch tracking은 다시 plain `origin/main`으로 되돌려 토큰이 `.git/config`에 남지 않게 정리했다.

## 2026-03-21 | Human + Codex | 초기 리포 구조의 오버엔지니어링과 중복 문서 정리

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 현재 리포를 점검한 결과, 아직 코드가 없는 단계인데도 미래 확장용 빈 디렉토리와 보조 문서가 다소 앞서 만들어져 있었다.
- 이에 따라 `status`와 겹치는 얇은 보조 문서와 실제 내용이 없는 플레이스홀더 디렉토리를 정리했다.
- active 루트 구조는 `mailbox`, `analysis`, `exports`, `llm` 중심으로 축소했다.
- workflow, reply, notification, shared, tests, tools, examples는 실제 구현이 시작될 때 추가하는 기준으로 되돌렸다.
- 레퍼런스로 쓰던 `tmp/` 디렉토리도 이번 작업 마지막에 삭제했다.

## 2026-03-21 | Human + Codex | 사용자 안내 말투를 친절한 톤으로 고정

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 앞으로의 안내 말투를 더 친절하게 유지하길 원했다.
- 이에 따라 `AGENT.md`의 보고 규칙에 친절하고 차분한 안내 말투 기준을 추가했다.
- `docs/개발방침.md`에는 안내 말투 원칙과 진행 보고 시의 적용 기준을 반영했다.
- `docs/decisions.md`에는 친절하되 명확한 안내 톤을 유지한다는 결정을 추가했다.

## 2026-03-21 | Human + Codex | 현재 세션을 에이전트 모드로 전환

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자가 지금부터 이 프로젝트를 `에이전트 모드`로 운영하길 명시했다.
- 이에 따라 시작 게이트를 다시 통과해 현재 기준 문서를 재확인했다.
- `docs/status.md`의 현재 작업 모드를 `에이전트 모드`로 갱신했다.
- 이후 비사소한 작업에서는 `AI)` prefix와 에이전트 모드 운영 규칙을 따른다.

## 2026-03-21 | Human + Codex | 레퍼런스 레포 기반 초기 운영 문서와 디렉토리 뼈대 생성

- 기준 문서는 `tmp/ondevice-voice-agent/docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, 모듈 `README.md`들이었다.
- 레퍼런스 레포의 핵심 운영 철학을 현재 이메일 자동화 프로젝트에 맞게 번역했다.
- 상위 문서 역할을 `README / status / 개발방침 / decisions / logbook / archive`로 분리했다.
- 시작 게이트를 `docs/AGENT.md -> docs/README.md -> docs/status.md` 순서로 고정했다.
- 현재 제품의 초기 모듈을 `mailbox / analysis / workflows / exports / responders / notifications / llm / shared`로 정의했다.
- 별도 계획 문서로 `automation_workflow_plan.md`, `background_jobs_plan.md`를 추가해 제품 handoff와 장시간 background job 운영 기준을 분리했다.
