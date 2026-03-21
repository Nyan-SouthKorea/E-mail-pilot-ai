# Logbook

> 최근 작업만 유지한다. 오래된 상세 로그는 필요해지면 `docs/archive/`로 옮긴다.

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
