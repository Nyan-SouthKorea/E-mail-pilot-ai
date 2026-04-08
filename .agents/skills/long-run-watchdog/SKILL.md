# long-run-watchdog

이 skill은 `10분 이상` 또는 여러 단계가 자동으로 이어지는 작업을 안전하게 거는 절차를 정리한다.

## 언제 쓰나

- inbox polling
- 대량 backfill
- batch export
- queue worker
- 장시간 분석/변환 파이프라인

## 기본 원칙

- 실전 실행 전에 smoke를 먼저 통과시킨다.
- 현재 무엇이 실제로 돌고 있는지는 대화 맥락이 아니라 `pid`, `ps`, `status.local.md`, `events.log`, progress 파일로 확인한다.
- 실제 사용자 runtime이라면 산출물은 `../secrets/사용자 설정/<이름>/실행결과/로그/` 아래에 둔다.
- repo-safe한 장시간 실험이라면 `<module>/results/YYMMDD_HHMM_설명/`을 쓸 수 있다.

## 최소 산출물

- `pid`
- `status.local.md`
- `events.log`
- 종료 코드 또는 종료 원인
- 다음 단계 실행 여부

## 해야 할 일

1. smoke에서 정상 종료, 실패 종료, stale 상태를 먼저 검증한다.
2. 실전 실행 전에 결과 경로를 정한다.
3. 실행 중간 설명보다 실제 상태 파일을 먼저 확인한다.
4. 완료 후에는 canonical 문서와 cleanup 여부를 함께 정리한다.
