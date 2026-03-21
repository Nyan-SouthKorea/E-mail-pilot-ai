"""OpenAI 호출 로그와 사용량 집계를 담당한다."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from .pricing import estimate_cost_from_usage


@dataclass(slots=True)
class OpenAIUsageLogEntry:
    """기능: OpenAI API 호출 1건의 로그를 표현한다.

    입력:
    - call_id: 로컬 호출 id
    - started_at / finished_at: 시작/종료 시각
    - duration_ms: 호출 시간
    - status: `completed` 또는 `error`
    - wrapper_kind: 래퍼 종류
    - operation: 상위 작업명
    - model_name: 실제 사용 모델명
    - response_id: OpenAI 응답 id
    - metadata: 호출 metadata
    - request_fingerprint: 요청 fingerprint 정보
    - usage: API usage dict
    - cost_estimate: 예상 비용 dict
    - error: 실패 정보

    반환:
    - dataclass 인스턴스
    """

    call_id: str
    started_at: str
    finished_at: str
    duration_ms: int
    status: str
    wrapper_kind: str
    operation: str
    model_name: str
    response_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    request_fingerprint: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    cost_estimate: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """기능: 로그 엔트리를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return asdict(self)


class JsonlUsageLogger:
    """기능: OpenAI 사용 로그 JSONL 파일을 읽고 쓴다."""

    def __init__(self, log_path: str) -> None:
        self.log_path = Path(log_path)

    def append(self, entry: OpenAIUsageLogEntry) -> None:
        """기능: 로그 엔트리 1건을 JSONL에 추가한다.

        입력:
        - entry: 로그 엔트리

        반환:
        - 없음
        """

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def read_entries(self) -> list[dict[str, Any]]:
        """기능: 현재 JSONL 로그 전체를 읽는다.

        입력:
        - 없음

        반환:
        - 로그 dict 목록
        """

        if not self.log_path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def summarize(self) -> dict[str, Any]:
        """기능: 현재 로그를 기준으로 토큰과 예상 비용을 합산한다.

        입력:
        - 없음

        반환:
        - 집계 dict
        """

        entries = self.read_entries()
        completed = [entry for entry in entries if entry.get("status") == "completed"]

        input_tokens = 0
        cached_tokens = 0
        output_tokens = 0
        total_tokens = 0
        total_cost_usd = 0.0

        for entry in completed:
            usage = entry.get("usage") or {}
            input_tokens += int(usage.get("input_tokens") or 0)
            output_tokens += int(usage.get("output_tokens") or 0)
            total_tokens += int(usage.get("total_tokens") or 0)
            input_details = usage.get("input_tokens_details") or {}
            cached_tokens += int(input_details.get("cached_tokens") or 0)

            cost_estimate = entry.get("cost_estimate") or {}
            total_cost_usd += float(cost_estimate.get("total_cost_usd") or 0.0)

        return {
            "log_path": str(self.log_path),
            "entry_count": len(entries),
            "completed_count": len(completed),
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_total_cost_usd": round(total_cost_usd, 10),
        }


def utc_now_iso() -> str:
    """기능: 현재 UTC 시각을 ISO 문자열로 반환한다.

    입력:
    - 없음

    반환:
    - ISO8601 문자열
    """

    return datetime.now(timezone.utc).isoformat()


def build_request_fingerprint(
    *,
    model: str,
    instructions: str | None,
    input_payload: Any,
    metadata: dict[str, Any] | None,
    include_preview: bool = False,
    max_preview_chars: int = 280,
) -> dict[str, Any]:
    """기능: 민감 원문 전체를 남기지 않는 요청 fingerprint를 만든다.

    입력:
    - model: 모델명
    - instructions: 시스템/지시 문자열
    - input_payload: 입력 payload
    - metadata: metadata dict
    - include_preview: preview 포함 여부
    - max_preview_chars: preview 최대 길이

    반환:
    - fingerprint dict
    """

    instructions_text = instructions or ""
    input_text = _safe_json_dump(input_payload)
    metadata_text = _safe_json_dump(metadata or {})

    fingerprint = {
        "model": model,
        "instructions_sha256": sha256(instructions_text.encode("utf-8")).hexdigest(),
        "input_sha256": sha256(input_text.encode("utf-8")).hexdigest(),
        "metadata_sha256": sha256(metadata_text.encode("utf-8")).hexdigest(),
        "instructions_chars": len(instructions_text),
        "input_chars": len(input_text),
        "metadata_chars": len(metadata_text),
    }

    if include_preview:
        fingerprint["instructions_preview"] = instructions_text[:max_preview_chars]
        fingerprint["input_preview"] = input_text[:max_preview_chars]

    return fingerprint


def build_usage_log_entry(
    *,
    call_id: str,
    started_at: str,
    finished_at: str,
    duration_ms: int,
    operation: str,
    model_name: str,
    metadata: dict[str, Any],
    request_fingerprint: dict[str, Any],
    usage: dict[str, Any] | None,
    response_id: str | None = None,
    error: dict[str, Any] | None = None,
) -> OpenAIUsageLogEntry:
    """기능: usage와 비용 계산을 포함한 로그 엔트리를 만든다.

    입력:
    - 로그에 필요한 각 필드들

    반환:
    - `OpenAIUsageLogEntry`
    """

    cost_estimate = estimate_cost_from_usage(model_name=model_name, usage=usage)
    return OpenAIUsageLogEntry(
        call_id=call_id,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        status="error" if error else "completed",
        wrapper_kind="openai.responses",
        operation=operation,
        model_name=model_name,
        response_id=response_id,
        metadata=metadata,
        request_fingerprint=request_fingerprint,
        usage=usage or {},
        cost_estimate=cost_estimate,
        error=error,
    )


def _safe_json_dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
