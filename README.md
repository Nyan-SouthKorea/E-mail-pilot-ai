# Email Agent

이 리포지토리는 ChatGPT API를 활용해 이메일을 읽고, 분류하고, 필요한 정보를 구조화해 Excel로 내보내는 소프트웨어를 만들기 위한 시작점이다. 현재는 미래 확장용 구조를 과하게 미리 늘리지 않고, `이메일 수신 -> 분석 -> Excel 출력`의 주경로를 먼저 고정하는 단계다.

## 현재 범위

- 수신 이메일 동기화와 정규화
- LLM 기반 분류 / 추출 / 요약
- Excel 출력 자동화
- 이후 reply draft와 외부 알림으로 확장 가능한 설계 준비

## 현재 활성 디렉토리

| 디렉토리 | 역할 | 상태 |
|---|---|---|
| [mailbox](mailbox/README.md) | 메일 수집, thread fetch, attachment 메타데이터 수집, cursor 관리 | 구조만 정의 |
| [analysis](analysis/README.md) | 분류, 정보 추출, 요약, schema 정규화 | 구조만 정의 |
| [exports](exports/README.md) | Excel 출력, row schema, workbook 반영 | 구조만 정의 |
| [llm](llm/README.md) | OpenAI 호출, prompt, structured response | 구조만 정의 |

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

로컬 워크스페이스는 보통 `repo/`, `envs/`, `results/`, `secrets/`를 같은 상위 루트 아래 sibling으로 둔다. Git으로 추적할 공식 상태와 운영 기준은 이 리포 안의 문서를 기준으로 유지하고, 민감 정보와 재생성 가능한 실행 산출물은 리포 바깥 로컬 경로에서 관리한다.
