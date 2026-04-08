# Logbook

> 최근 작업만 유지한다. 오래된 상세 로그는 필요해지면 `docs/archive/`로 옮긴다.

## 2026-03-21 | Human + Codex | mailbox 자동 설정 후보 생성과 connect/auth probe smoke 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `mailbox/README.md`였다.
- 현재 단계에서 GUI를 먼저 만드는 것보다, 실제 메일 엔진의 자동 설정 탐지와 연결 검증을 텍스트 기반 smoke로 먼저 확인하는 편이 더 낫다고 판단했다.
- 이에 따라 `mailbox/autoconfig.py`를 추가해 provider preset, generic domain pattern, Mozilla autoconfig, 실제 probe를 묶은 자동 설정 엔진을 만들었다.
- 현재 provider preset은 Gmail, Outlook.com을 우선 넣었고, 나머지 도메인은 `imap.<domain>`, `smtp.<domain>` 같은 generic pattern과 autoconfig를 함께 사용한다.
- probe는 비밀번호가 없을 때 `connect-only`, 비밀번호나 앱 비밀번호가 있으면 `auth` 모드로 동작하게 만들었다.
- `mailbox/autoconfig_smoke.py`를 추가해 CLI에서 이메일 주소 하나만으로 dry-run 후보 계획 또는 실제 probe 결과를 바로 확인할 수 있게 했다.
- 검증으로 `test@gmail.com` dry-run과 connect-only smoke를 실행했고, Gmail preset 후보와 실제 `imap.gmail.com:993`, `pop.gmail.com:995`, `smtp.gmail.com:587/465` 연결 성공을 확인했다.
- smoke report는 `실행결과/로그/mailbox/test_at_gmail_com_autoconfig_smoke.json`에 저장된다.

## 2026-03-21 | Human + Codex | 멀티모달 입력, timestamped export workbook, GUI 선후순위 기준 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `analysis/README.md`, `exports/README.md`, `llm/README.md`, `README.md`였다.
- 사용자는 LLM 활용 시 텍스트만이 아니라 이미지까지 직접 분석하는 성능 우선 방향, `YYMMDD_HHMM_<template>.xlsx` 형식의 새 export 파일명 규칙, legacy 산출물 정리, 그리고 GUI보다 실연동 엔진 검증이 먼저라는 순서를 문서와 코드에 반영하길 원했다.
- 동시에 reference workbook diff를 품질 목표처럼 숫자 맞추기에 쓰는 것은 과적합 위험이 있으니, Codex가 실제 운영 기준으로 프롬프트를 판단해 수정하고 회귀 비교는 guardrail로만 쓰는 방향이 더 낫다고 의견을 주었다.
- 이에 따라 `analysis/multimodal_input.py`를 추가해 direct image attachment가 있으면 Responses API에 `input_text + input_image` 형태로 함께 넣는 경로를 만들었다. synthetic PNG smoke에서 `input_text`, `input_image` part가 정상 생성되는 것도 확인했다.
- `analysis/fixture_smoke.py`, `analysis/materialized_bundle_smoke.py`는 새 멀티모달 입력 builder를 사용하도록 바꿨고, `analysis/llm_extraction.py`는 신청서 우선, 시각 입력 직접 해석, 운영자 가독성 중심 요약 지시를 더 분명하게 다듬었다.
- `llm/config.py`의 기본 분석 모델은 성능 우선 기준에 맞춰 `gpt-5.4`로 올렸다.
- `exports/output_paths.py`를 추가해 최신 runtime workbook 선택, timestamped workbook 파일명 생성, legacy workbook 정리 규칙을 모듈화했고, fixture/runtime pipeline smoke와 regression check 기본 경로도 새 규칙에 맞췄다.
- 실제 live 실행 결과 새 workbook은 `실행결과/엑셀 산출물/260321_1701_기업_신청서_모음.xlsx`로 생성됐고, 기존 규칙과 맞지 않던 `기업 신청서 모음_fixture_pipeline.xlsx`, `기업 신청서 모음_materialized_bundle_pipeline.xlsx`, `기업_신청서_모음_fixture_smoke.xlsx`는 정리했다.
- 이후 guardrail 용도로 `exports.regression_check`를 다시 돌렸고, 현재 latest report 기준은 `10/22 = 0.4545`였다. 이 숫자는 품질 목표가 아니라 큰 방향이 망가지지 않았는지 확인하는 안전장치로만 유지한다.
- live 재실행 후 usage log 누적 기준은 `entry_count=11`, `input_tokens=16935`, `output_tokens=10326`, `estimated_total_cost_usd=0.1972275`다.

## 2026-03-21 | Human + Codex | materialized bundle 분석 결과를 workbook append까지 잇는 end-to-end smoke 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `analysis/README.md`, `exports/README.md`였다.
- 다음 계획은 이미 만들어 둔 runtime bundle 분석 결과를 기존 export 파이프라인에 연결해, fixture 전용 흐름이 아니라 실제 `받은 메일/<bundle-id>/` 구조에서 바로 엑셀 산출물까지 이어지는 smoke를 만드는 것이었다.
- 이에 따라 `analysis/materialized_bundle_pipeline_smoke.py`를 추가해 `runtime bundle -> extracted_record -> projected_row -> workbook append` 순서의 얇은 end-to-end 진입점을 만들었다.
- 이 smoke는 기존 `analysis/materialized_bundle_smoke.py`와 `exports` 계층 helper를 재사용하고, 결과 workbook은 `실행결과/엑셀 산출물/<template>_materialized_bundle_pipeline.xlsx`, projection JSON은 `실행결과/로그/exports/<bundle-id>_projected_row.json`에 남긴다.
- 검증은 `--reuse-existing-analysis` 기준으로 진행했고, 두 bundle이 결과 workbook 4행과 5행에 정상 append되는 것을 확인했다.
- 이어서 `exports.regression_check`로 reference workbook과 비교한 결과는 `10/22 = 0.4545`였다.
- `analysis/README.md`, `exports/README.md`, `docs/status.md`도 현재 상태에 맞게 갱신했다.

## 2026-03-21 | Human + Codex | materialized bundle의 `normalized.json`을 직접 읽는 live 분석 smoke 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `mailbox/README.md`, `analysis/README.md`, `llm/README.md`였다.
- 다음 계획은 방금 만든 `받은 메일/<bundle-id>/` 구조를 실제 분석 입력으로 재사용하는 것이었고, 이때 가장 중요한 기준은 fixture 전용 로더를 더 늘리지 않고 runtime bundle의 `normalized.json`을 canonical 입력으로 쓰는 것이었다.
- 이에 따라 `mailbox/schema.py`에 `Address`, `BodyPart`, `StoredArtifact`, `MailBundlePaths`, `MailBundle`, `NormalizedMessage`의 `from_dict()` 복원 경로를 추가했다.
- `mailbox/bundle_reader.py`를 추가해 유효한 runtime bundle 목록을 고르고, bundle의 `normalized.json`과 `attachments/`를 읽는 helper를 만들었다.
- `analysis/artifact_summary.py`를 추가해 ZIP 안 XLSX/PDF까지 포함한 첨부 요약 공용 helper를 만들었고, 기존 `analysis/fixture_smoke.py`도 이 공용 helper를 쓰도록 정리했다.
- `analysis/materialized_bundle_smoke.py`를 추가해 실제 runtime bundle의 `normalized.json`을 읽고 live OpenAI 분석을 실행한 뒤, 결과를 `실행결과/로그/analysis_smoke/<bundle-id>_extracted_record.json`에 저장하는 smoke를 만들었다.
- 검증 결과 유효 bundle은 placeholder를 제외한 `20260321_050857_msg_a6850e1c`, `20260321_051425_msg_f80d23b8` 두 건만 잡혔고, 둘 다 live 분석이 성공했다.
- 현재 usage log 누적 기준은 `entry_count=9`, `input_tokens=13175`, `output_tokens=8070`, `estimated_total_cost_usd=0.1539875`다.

## 2026-03-21 | Human + Codex | fixture 첨부 폴더 단순화와 MailBundle materialize smoke 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `mailbox/README.md`, `analysis/README.md`, `llm/README.md`였다.
- 사용자는 LLM 프롬프트가 어디서 관리되는지 물었고, 동시에 reference 예시 이메일을 실제 `받은 메일/<bundle-id>/` 구조로 풀어놓는 다음 계획을 실행하길 원했다.
- 이에 따라 프롬프트 관리 기준을 다시 확인했고, 현재 extraction prompt/schema는 `analysis/llm_extraction.py`, template header prompt/schema는 `exports/llm_mapping.py`, 실제 호출/로그는 `llm/openai_wrapper.py`가 담당하는 구조임을 정리했다.
- `mailbox/fixture_reference.py`를 추가해 fixture 이메일 본문 읽기, 헤더/본문 분리, 주소 파싱, 첨부 디렉토리 탐색, preview/raw.eml 생성 helper를 공용화했다.
- 기존 reference 폴더의 `첨부파일(파일들일지 zip일지 모름)`은 실제로 `첨부파일`로 이름을 바꿨고, 코드는 옛 이름과 새 이름 둘 다 읽을 수 있게 만들었다.
- `mailbox/fixture_materialize.py`를 추가해 예시 이메일 2건을 실제 `실행결과/받은 메일/<bundle-id>/raw.eml, preview.html, normalized.json, summary.md, attachments/` 구조로 materialize 하는 첫 smoke를 구현했다.
- 현재 생성된 bundle은 `20260321_050857_msg_a6850e1c`, `20260321_051425_msg_f80d23b8` 두 건이다.

## 2026-03-21 | Human + Codex | extraction prompt와 projection 정규화 개선으로 회귀 일치율 향상

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `analysis/README.md`, `exports/README.md`, `llm/README.md`였다.
- regression diff를 확인한 결과, 차이의 상당수는 신청서 값을 우선하는 규칙과 운영용 표시 형식이 부족해서 생기는 문제였다.
- 이에 따라 `analysis/llm_extraction.py` 지시문에 `신청서 첨부 우선`, `회사명/전화/웹사이트 표시 방식`, `산업군/제품/신청목적/요약 필드 압축 기준`을 더 명확히 추가했다.
- `exports/record_projection.py`에는 회사명 법인격 제거, 한국 전화번호 표시 정리, 웹사이트 trailing slash 제거, 산업군 구분자 정리 같은 projection 단계 정규화를 넣었다.
- 그 결과 fixture pipeline을 다시 live 실행했을 때 regression match가 `6/22 = 0.2727`에서 `10/22 = 0.4545`로 개선됐다.
- 현재 usage log 누적 기준은 `entry_count=7`, `input_tokens=9905`, `output_tokens=6088`, `estimated_total_cost_usd=0.1160825`다.

## 2026-03-21 | Human + Codex | 프로필 폴더 구조를 `참고자료 / 실행결과`로 정리하고 MailBundle 저장 helper 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `README.md`, `mailbox/README.md`, `exports/README.md`, `llm/README.md`였다.
- 사용자는 실제 산출물을 사용자 프로필 폴더 아래에서 관리하길 원했고, 상위 폴더는 한국어로 두되 내부 기계 식별자는 안정적인 방식으로 가는 의견을 요청했다.
- 이에 따라 `김정민` 프로필 아래를 `참고자료/`와 `실행결과/`로 나누고, 기존 예시 메일과 기대 산출물은 `참고자료/`로, 기존 smoke 산출물은 `실행결과/엑셀 산출물`, `실행결과/로그`로 옮겼다.
- 코드에는 `project_paths.py`를 추가해 프로필 기준 reference/runtime 경로 규칙을 공용 helper로 묶었다.
- `mailbox/bundle_storage.py`에는 `build_mail_bundle_id()`, `build_mail_bundle_paths()`, `create_mail_bundle_skeleton()`을 추가해 `받은 메일/<bundle-id>/raw.eml, preview.html, normalized.json, summary.md, attachments/` 뼈대를 만드는 최소 생성 흐름을 구현했다.
- `analysis/fixture_pipeline_smoke.py`, `exports/regression_check.py`는 기본 경로를 새 프로필 구조로 옮겼고, fixture pipeline smoke와 regression check가 새 경로에서 정상 동작하는 것도 확인했다.
- 현재 새 bundle skeleton smoke 결과 폴더는 `secrets/사용자 설정/김정민/실행결과/받은 메일/20260321_123456_msg_16b0db71/`에 생성되어 있다.

## 2026-03-21 | Human + Codex | 쉬운 설명 우선 원칙 반영

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`였다.
- 사용자는 다음 작업과 계획 설명이 어렵게 들린다고 했고, 앞으로는 항상 알아듣기 쉽게 설명하는 기준을 문서에 반영하길 원했다.
- 이에 따라 `AGENT.md` 보고 규칙에는 계획/상태/다음 작업을 먼저 쉬운 말로 설명한다는 기준을 추가했다.
- `docs/개발방침.md`에는 쉬운 말 우선, 기술 용어는 나중에 덧붙이기, 이해가 어려우면 같은 내용을 더 쉽게 다시 설명하기를 기본 행동으로 반영했다.
- `docs/decisions.md`에는 계획과 상태 설명을 항상 쉬운 말부터 쓴다는 결정을 추가했다.

## 2026-03-21 | Human + Codex | 성능 우선 LLM 기준 반영과 workbook regression check 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, `exports/README.md`, `llm/README.md`였다.
- 사용자는 현재 프로젝트에서 API 비용을 과도하게 아끼지 말고, LLM이 더 잘하는 일은 적극적으로 LLM에 맡기고 rule/code가 더 잘하는 일은 그쪽으로 두는 성능 우선 방향을 원한다고 명시했다.
- 현재 구현은 완전히 반대 방향은 아니었지만, 일부 문서와 `fixture_pipeline_smoke`가 `rule 우선` 쪽으로만 보일 수 있어 기준을 다시 정리했다.
- 이에 따라 `docs/개발방침.md`, `docs/status.md`, `docs/decisions.md`, `llm/README.md`, `exports/README.md`, `README.md`에 비용은 관찰용이고 설계 판단은 성능/정확도 우선이라는 원칙을 반영했다.
- 코드에서는 `analysis/fixture_pipeline_smoke.py`를 pure rule 매핑에서 hybrid 매핑 호출로 바꿨다. 현재 템플릿에서는 unresolved header가 없어 추가 호출은 생기지 않지만, 이후 프로필에서는 더 자연스럽게 LLM 보조를 받을 수 있다.
- `exports/regression_check.py`를 추가해 generated workbook과 reference fixture workbook을 deterministic하게 비교하는 회귀 확인 도구를 만들었다.
- 당시 실제 실행 결과는 `results/exports_smoke/fixture_regression_report.json`에 남겼고, 이후 현재 기준으로는 `secrets/사용자 설정/김정민/실행결과/로그/exports/fixture_regression_report.json`로 정리했다. 비교 결과 자체는 `compared_cell_count=22`, `matched_cell_count=6`, `match_ratio=0.2727`이었다.

## 2026-03-21 | Human + Codex | 체크포인트 7 완료 - unresolved template header LLM fallback 추가

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/decisions.md`, `exports/README.md`, `llm/README.md`였다.
- `exports/semantic_mapping.py`에 여러 매핑 결과를 우선순위대로 합치는 `merge_template_semantic_mappings()`를 추가했다.
- `exports/llm_mapping.py`를 추가해 rule 기반으로 해결되지 않은 템플릿 헤더만 모아, OpenAI structured output으로 의미 키를 보충하는 최소 fallback 절차를 구현했다.
- 이 경로는 `rule -> unresolved 수집 -> LLM fallback -> merged mapping` 순서로만 동작하고, rule로 이미 확정된 헤더에는 추가 호출을 하지 않는다.
- synthetic 템플릿 smoke를 live로 실행해 `참가 목적 -> application_purpose`, `브랜드 소개 -> company_intro_one_line`, `검토 의견 -> internal_notes` 매핑을 확인했고, 결과는 당시 `results/exports_smoke/template_header_llm_fallback_smoke.json`에 저장했다. 현재 기준 경로는 `secrets/사용자 설정/김정민/실행결과/로그/exports/template_header_llm_fallback_smoke.json`이다.
- 실제 김정민 템플릿에도 hybrid mapping을 적용해 보았고, unresolved header가 없어서 usage log entry 수가 `5 -> 5`로 유지되는 것을 확인했다.
- 현재 usage log 누적 기준은 `entry_count=5`, `input_tokens=6641`, `output_tokens=4207`, `estimated_total_cost_usd=0.0797075`다.

## 2026-03-21 | Human + Codex | 체크포인트 6 완료 - fixture end-to-end pipeline smoke 실행

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `analysis/README.md`, `exports/README.md`였다.
- 수동 명령으로만 검증하던 흐름을 `analysis/fixture_pipeline_smoke.py`로 묶어, fixture 이메일 로딩 -> live LLM 분석 -> projection -> workbook append까지 한 번에 실행할 수 있게 했다.
- direct script 실행과 `python -m` 실행 둘 다 가능하도록 import 경로를 정리했고, `reuse_existing_analysis` 옵션도 추가했다.
- 실제로 스크립트를 실행해 당시 `results/exports_smoke/기업 신청서 모음_fixture_pipeline.xlsx`를 생성했고, 두 fixture가 row 4, row 5에 순서대로 append되는 것을 확인했다. 현재 기준 경로는 `secrets/사용자 설정/김정민/실행결과/엑셀 산출물/기업 신청서 모음_fixture_pipeline.xlsx`다.
- 현재 usage log 누적 기준은 `entry_count=4`, `input_tokens=5384`, `output_tokens=4021`, `estimated_total_cost_usd=0.073775`다.

## 2026-03-21 | Human + Codex | 체크포인트 4, 5 완료 - rule 기반 템플릿 매핑과 workbook append 검증

- 기준 문서는 `docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/decisions.md`, `exports/README.md`였다.
- `exports/rule_mapping.py`를 추가해 템플릿 헤더를 공통 의미 키와 rule 기반 exact/partial match로 연결하는 첫 절차를 구현했다.
- 이 과정에서 `번호` 헤더가 `연락처` 계열로 잘못 붙을 수 있는 문제를 발견했고, 공통 의미 키에 `row_number` system field를 추가해 workbook 단계에서 자동 생성하도록 수정했다.
- `analysis/schema.py`에는 저장된 `ExtractedRecord` JSON을 다시 불러오기 위한 `from_dict()` 복원 경로를 추가했다.
- `exports/workbook_writer.py`를 추가해 원본 템플릿을 건드리지 않고 별도 결과 workbook에 append하는 writer를 구현했다.
- writer는 마지막 실데이터 다음 행을 찾고, 직전 데이터 행의 서식과 수식을 최대한 이어받은 뒤 projection 값을 기록하도록 만들었다.
- fixture 2건의 live 분석 결과 JSON을 사용해 실제 workbook append smoke를 실행했고, 결과 파일은 당시 `results/exports_smoke/기업_신청서_모음_fixture_smoke.xlsx`로 생성되었다. 현재 기준 경로는 `secrets/사용자 설정/김정민/실행결과/엑셀 산출물/기업_신청서_모음_fixture_smoke.xlsx`다.
- smoke 결과 기준으로 row 4, row 5에 새 행이 정상 추가되었고, `번호`는 각각 `3`, `4`로 자동 생성되었다.

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
- 사용 로그 기본 경로는 처음에는 `../results/llm/openai_usage.jsonl`로 두었고, 기본 가격표는 `2026-03-21` 기준 OpenAI 공식 가격 페이지 snapshot으로 시작했다. 현재 프로필 기준 기본 경로는 `secrets/사용자 설정/김정민/실행결과/로그/llm/openai_usage.jsonl`이다.
- 동시에 `analysis/fixture_smoke.py`와 `analysis/llm_extraction.py`를 추가해, fixture 이메일 본문 + ZIP 내부 파일 목록 + ZIP 안 XLSX 텍스트 요약을 LLM 입력으로 묶는 첫 smoke 진입점을 만들었다.
- 현재 환경에는 `OPENAI_API_KEY`가 없어서 실제 live 호출까지는 아직 실행하지 않았고, dry-run으로 입력 조립과 wrapper 집계 동작만 먼저 확인했다.

## 2026-03-21 | Human + Codex | 체크포인트 3 완료 - fixture 2건 live 분석 smoke 실행

- 사용자가 `secrets/chatgpt_api_key.txt`에 API 키를 두었다고 알려주어, wrapper가 환경 변수 우선 후 로컬 키 파일을 fallback으로 읽게 했다.
- 이후 fixture 2건에 대해 실제 OpenAI live 호출을 실행했고, `ExtractedRecord` JSON 결과를 처음에는 `results/analysis_smoke/` 아래에 남겼다. 현재 기준 경로는 `secrets/사용자 설정/김정민/실행결과/로그/analysis_smoke/`다.
- usage log는 처음에는 `results/llm/openai_usage.jsonl`에 쌓였고, 현재는 `secrets/사용자 설정/김정민/실행결과/로그/llm/openai_usage.jsonl` 기준으로 이어서 관리한다. 당시 두 호출 합산 기준 `input_tokens=2692`, `output_tokens=1970`, `estimated_total_cost_usd=0.03628`였다.
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

- 기준 문서는 `tmp/legacy-seed/docs/AGENT.md`, `docs/README.md`, `docs/status.md`, `docs/개발방침.md`, `docs/decisions.md`, 모듈 `README.md`들이었다.
- 레퍼런스 레포의 핵심 운영 철학을 현재 이메일 자동화 프로젝트에 맞게 번역했다.
- 상위 문서 역할을 `README / status / 개발방침 / decisions / logbook / archive`로 분리했다.
- 시작 게이트를 `docs/AGENT.md -> docs/README.md -> docs/status.md` 순서로 고정했다.
- 현재 제품의 초기 모듈을 `mailbox / analysis / workflows / exports / responders / notifications / llm / shared`로 정의했다.
- 별도 계획 문서로 `automation_workflow_plan.md`, `background_jobs_plan.md`를 추가해 제품 handoff와 장시간 background job 운영 기준을 분리했다.
