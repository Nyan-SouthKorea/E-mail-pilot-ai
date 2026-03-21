"""OpenAI Responses API 공용 래퍼."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from os import getenv
from typing import Any

from .config import OpenAIResponsesConfig
from .usage_log import (
    JsonlUsageLogger,
    build_request_fingerprint,
    build_usage_log_entry,
    utc_now_iso,
)


@dataclass(slots=True)
class OpenAIResponseEnvelope:
    """기능: OpenAI 응답과 로컬 로그 정보를 함께 묶는다.

    입력:
    - response: OpenAI SDK 응답 객체
    - output_text: SDK가 정리한 output text
    - usage: 응답 usage dict
    - log_entry: 기록된 로그 엔트리 dict

    반환:
    - dataclass 인스턴스
    """

    response: Any
    output_text: str
    usage: dict[str, Any]
    log_entry: dict[str, Any]
    parsed_output: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        """기능: envelope 메타정보를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return {
            "output_text": self.output_text,
            "usage": self.usage,
            "log_entry": self.log_entry,
            "parsed_output": self.parsed_output,
        }


class OpenAIResponsesWrapper:
    """기능: 모든 OpenAI Responses API 호출을 공용 경로로 감싼다."""

    def __init__(self, config: OpenAIResponsesConfig | None = None) -> None:
        self.config = config or OpenAIResponsesConfig()
        self.logger = JsonlUsageLogger(self.config.usage_log_path)
        self._client: Any | None = None

    def create_response(
        self,
        *,
        operation: str,
        input_payload: Any,
        instructions: str | None = None,
        model: str | None = None,
        metadata: dict[str, str] | None = None,
        text: dict[str, Any] | None = None,
        reasoning: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        store: bool | None = None,
        service_tier: str | None = None,
        timeout_seconds: float | None = None,
    ) -> OpenAIResponseEnvelope:
        """기능: Responses API 호출을 실행하고 로그를 남긴다.

        입력:
        - operation: 상위 작업명
        - input_payload: API `input`에 전달할 payload
        - instructions: 시스템/지시 문자열
        - model: 사용할 모델명
        - metadata: 호출 metadata
        - text / reasoning / tools: Responses API 파라미터
        - max_output_tokens / temperature / store / service_tier / timeout_seconds: 실행 옵션

        반환:
        - 응답과 로그 정보가 담긴 `OpenAIResponseEnvelope`
        """

        call_id = str(uuid.uuid4())
        started_at = utc_now_iso()
        started_perf = time.perf_counter()

        merged_metadata = dict(self.config.default_metadata)
        merged_metadata.update(metadata or {})
        merged_metadata.setdefault("operation", operation)
        resolved_model = model or self.config.model

        request_fingerprint = build_request_fingerprint(
            model=resolved_model,
            instructions=instructions,
            input_payload=input_payload,
            metadata=merged_metadata,
            include_preview=self.config.include_request_preview,
            max_preview_chars=self.config.max_preview_chars,
        )

        request_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "input": input_payload,
            "metadata": merged_metadata,
            "store": self.config.store if store is None else store,
            "service_tier": service_tier or self.config.service_tier,
        }
        if instructions is not None:
            request_kwargs["instructions"] = instructions
        if text is not None:
            request_kwargs["text"] = text
        if reasoning is not None:
            request_kwargs["reasoning"] = reasoning
        if tools is not None:
            request_kwargs["tools"] = tools
        if max_output_tokens is not None:
            request_kwargs["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            request_kwargs["temperature"] = temperature

        timeout_value = (
            self.config.timeout_seconds if timeout_seconds is None else timeout_seconds
        )

        try:
            response = self.client().responses.create(
                **request_kwargs,
                timeout=timeout_value,
            )
            finished_at = utc_now_iso()
            duration_ms = int((time.perf_counter() - started_perf) * 1000)
            usage = self._usage_to_dict(getattr(response, "usage", None))
            output_text = self.extract_output_text(response)

            log_entry = build_usage_log_entry(
                call_id=call_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                operation=operation,
                model_name=str(getattr(response, "model", resolved_model)),
                metadata=merged_metadata,
                request_fingerprint=request_fingerprint,
                usage=usage,
                response_id=getattr(response, "id", None),
            )
            self.logger.append(log_entry)
            return OpenAIResponseEnvelope(
                response=response,
                output_text=output_text,
                usage=usage,
                log_entry=log_entry.to_dict(),
                parsed_output=getattr(response, "output_parsed", None),
            )
        except Exception as exc:
            finished_at = utc_now_iso()
            duration_ms = int((time.perf_counter() - started_perf) * 1000)
            log_entry = build_usage_log_entry(
                call_id=call_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                operation=operation,
                model_name=resolved_model,
                metadata=merged_metadata,
                request_fingerprint=request_fingerprint,
                usage=None,
                error={
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )
            self.logger.append(log_entry)
            raise

    def parse_response(
        self,
        *,
        operation: str,
        text_format: type,
        input_payload: Any,
        instructions: str | None = None,
        model: str | None = None,
        metadata: dict[str, str] | None = None,
        text: dict[str, Any] | None = None,
        verbosity: str | None = None,
        reasoning: dict[str, Any] | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        store: bool | None = None,
        service_tier: str | None = None,
        timeout_seconds: float | None = None,
    ) -> OpenAIResponseEnvelope:
        """기능: Responses API parse 호출을 실행하고 로그를 남긴다.

        입력:
        - operation: 상위 작업명
        - text_format: SDK가 파싱할 출력 모델 class
        - input_payload: API `input`에 전달할 payload
        - 나머지 옵션은 `create_response`와 동일

        반환:
        - 응답과 로그 정보가 담긴 `OpenAIResponseEnvelope`
        """

        call_id = str(uuid.uuid4())
        started_at = utc_now_iso()
        started_perf = time.perf_counter()

        merged_metadata = dict(self.config.default_metadata)
        merged_metadata.update(metadata or {})
        merged_metadata.setdefault("operation", operation)
        resolved_model = model or self.config.model

        request_fingerprint = build_request_fingerprint(
            model=resolved_model,
            instructions=instructions,
            input_payload=input_payload,
            metadata=merged_metadata,
            include_preview=self.config.include_request_preview,
            max_preview_chars=self.config.max_preview_chars,
        )

        request_kwargs: dict[str, Any] = {
            "text_format": text_format,
            "model": resolved_model,
            "input": input_payload,
            "metadata": merged_metadata,
            "store": self.config.store if store is None else store,
            "service_tier": service_tier or self.config.service_tier,
        }
        if instructions is not None:
            request_kwargs["instructions"] = instructions
        if text is not None:
            request_kwargs["text"] = text
        if verbosity is not None:
            request_kwargs["verbosity"] = verbosity
        if reasoning is not None:
            request_kwargs["reasoning"] = reasoning
        if tools is not None:
            request_kwargs["tools"] = tools
        if max_output_tokens is not None:
            request_kwargs["max_output_tokens"] = max_output_tokens
        if temperature is not None:
            request_kwargs["temperature"] = temperature

        timeout_value = (
            self.config.timeout_seconds if timeout_seconds is None else timeout_seconds
        )

        try:
            response = self.client().responses.parse(
                **request_kwargs,
                timeout=timeout_value,
            )
            finished_at = utc_now_iso()
            duration_ms = int((time.perf_counter() - started_perf) * 1000)
            usage = self._usage_to_dict(getattr(response, "usage", None))
            output_text = self.extract_output_text(response)
            parsed_output = getattr(response, "output_parsed", None)

            log_entry = build_usage_log_entry(
                call_id=call_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                operation=operation,
                model_name=str(getattr(response, "model", resolved_model)),
                metadata=merged_metadata,
                request_fingerprint=request_fingerprint,
                usage=usage,
                response_id=getattr(response, "id", None),
            )
            self.logger.append(log_entry)
            return OpenAIResponseEnvelope(
                response=response,
                output_text=output_text,
                usage=usage,
                log_entry=log_entry.to_dict(),
                parsed_output=parsed_output,
            )
        except Exception as exc:
            finished_at = utc_now_iso()
            duration_ms = int((time.perf_counter() - started_perf) * 1000)
            log_entry = build_usage_log_entry(
                call_id=call_id,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                operation=operation,
                model_name=resolved_model,
                metadata=merged_metadata,
                request_fingerprint=request_fingerprint,
                usage=None,
                error={
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )
            self.logger.append(log_entry)
            raise

    def summarize_usage(self) -> dict[str, Any]:
        """기능: 현재 로그 파일 기준 사용량과 예상 비용을 집계한다.

        입력:
        - 없음

        반환:
        - 집계 dict
        """

        return self.logger.summarize()

    def client(self):
        """기능: OpenAI SDK client를 lazy 로드한다.

        입력:
        - 없음

        반환:
        - `openai.OpenAI` 인스턴스
        """

        if self._client is None:
            from openai import OpenAI

            api_key = getenv(self.config.api_key_env)
            if not api_key:
                raise RuntimeError(
                    f"환경 변수 `{self.config.api_key_env}`가 없어 OpenAI API를 호출할 수 없습니다."
                )
            self._client = OpenAI(api_key=api_key)
        return self._client

    def extract_output_text(self, response: Any) -> str:
        """기능: SDK 응답에서 사람이 읽을 텍스트를 뽑는다.

        입력:
        - response: OpenAI SDK 응답 객체

        반환:
        - 합쳐진 output text
        """

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            return output_text

        parts: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) == "output_text":
                    text = getattr(content, "text", "")
                    if text:
                        parts.append(text)
        return "\n".join(parts).strip()

    def _usage_to_dict(self, usage: Any) -> dict[str, Any]:
        if usage is None:
            return {}

        if hasattr(usage, "to_dict"):
            return usage.to_dict()

        if hasattr(usage, "model_dump"):
            return usage.model_dump()

        if hasattr(usage, "__dict__"):
            return dict(usage.__dict__)

        return dict(usage)
