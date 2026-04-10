# checklist-and-canonical-doc-sync

이 skill은 비사소한 변경을 할 때 active checklist와 canonical 문서를 함께 맞추는 절차를 정리한다.

## 언제 쓰나

- 여러 파일을 건드는 작업
- 구조 변경, 문서 변경, 도메인 경계 변경
- smoke 결과가 다음 작업의 기준을 바꾸는 경우
- 완료 응답이나 마감 정리를 앞둔 final gate 점검이 필요할 때

## 기본 원칙

- 변경 사실은 가까운 `docs/logbook.md`에 먼저 반영한다.
- 안정된 설명과 경계는 `README.md` 또는 모듈 `README.md`에 반영한다.
- 같은 내용을 여러 문서에 복제하지 않는다.
- 운영 규칙은 root `AGENTS.md`만 기준으로 두고, 다른 문서에는 각 문서의 역할만 남긴다.
- 승인된 상위 plan이 있으면 구현 전에 root `docs/logbook.md`에 plan 전문과 current checkpoint가 먼저 있어야 한다.

## 해야 할 일

1. 이번 변경이 프로젝트 레벨인지, 모듈 레벨인지 먼저 결정한다.
2. root `docs/logbook.md`의 active plan, 현재 체크포인트, publish 상태가 최신인지 먼저 맞춘다.
3. 관련 `docs/logbook.md`의 active checklist를 현재 작업 단위 기준으로 갱신한다.
4. 바뀐 current truth가 있으면 `README.md` 또는 모듈 `README.md`를 갱신한다.
5. 결과 경로, 다음 연결점, 임시 산출물 정리 여부를 logbook에 남긴다.
6. 어떤 문서를 일부러 건드리지 않았는지도 필요하면 짧게 적는다.
7. 완료 직전에는 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md`를 다시 읽고, 이번 변경이 그 기준과 어긋나지 않는지 마지막으로 확인한다.
8. plan 마감이면 canonical 문서 반영 뒤 `commit -> push -> clean status`까지 닫았는지 확인한다.
