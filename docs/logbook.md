# Logbook

> 최근 작업만 유지한다. 오래된 상세 로그는 필요해지면 `docs/archive/`로 옮긴다.

## 2026-03-21 | Human + Codex | `repo/` 안에 Git 저장소 초기화

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 `.git` 디렉토리가 반드시 `repo/` 안에 생성되길 원했다.
- 이에 따라 `repo/`에서 `git init -b main`을 수행해 로컬 Git 저장소를 초기화했다.
- 현재 로컬 커밋 작성용 `user.name`, `user.email`도 `repo/.git/config`에 최소 범위로 설정했다.
- 다음 단계는 현재 작업 트리를 초기 커밋으로 묶고, GitHub 원격을 연결하는 것이다.

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
