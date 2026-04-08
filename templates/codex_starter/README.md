# Project Starter

이 문서는 새 저장소를 시작할 때 프로젝트 소개, 전체 구조, 기능 배치 기준을 적는 starter template이다.

## 먼저 바꿔야 하는 것

- 프로젝트 이름
- 프로젝트 한줄 소개
- 현재 active 모듈 목록
- `새 기능을 어디에 둘까` 기준
- local private 문서 경계

## 추천 구조

- `AGENTS.md`
- `README.md`
- `docs/logbook.md`
- `docs/logbook_archive/`
- `.agents/skills/`
- 각 모듈 `README.md`
- 각 모듈 `docs/logbook.md`
- `tools/`
- `templates/codex_starter/`

## 새 기능을 어디에 둘까

- 도메인 입력/수집 계층
- 도메인 해석/변환 계층
- 출력/반영 계층
- 공용 모델/외부 API transport 계층
- GUI 또는 사용자 진입점 계층
- 장시간 실행 조율 계층

각 저장소는 위 분류를 자기 구조에 맞게 이름을 바꾸고, 의존 방향도 함께 적는다.

## 산출물 경계 예시

- 실제 사용자 데이터, 실제 운영 로그, 실제 결과 파일은 local private 경로를 canonical로 둔다.
- 재현 가능한 smoke 결과, diff summary, 소형 metadata만 repo 내부 공식 위치 후보를 쓴다.
- 미래 상위 계층은 실제 코드가 처음 들어가는 턴에만 만들고, 같은 턴에 각 디렉토리 `README.md`와 `docs/logbook.md`를 함께 연다.
