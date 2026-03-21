"""OpenAI 사용량 기준 예상 비용 계산을 담당한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class OpenAIModelPricing:
    """기능: 모델별 1M 토큰 단가를 표현한다.

    입력:
    - model_name: 기준 모델명
    - input_per_1m_usd: 일반 입력 토큰 단가
    - cached_input_per_1m_usd: cached input 토큰 단가
    - output_per_1m_usd: 출력 토큰 단가
    - source_url: 가격표 출처
    - snapshot_date: 가격 스냅샷 날짜

    반환:
    - dataclass 인스턴스
    """

    model_name: str
    input_per_1m_usd: float
    cached_input_per_1m_usd: float
    output_per_1m_usd: float
    source_url: str = "https://openai.com/api/pricing/"
    snapshot_date: str = "2026-03-21"

    def to_dict(self) -> dict[str, object]:
        """기능: 가격 정보를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return asdict(self)


def default_openai_pricing_catalog() -> dict[str, OpenAIModelPricing]:
    """기능: 기본 OpenAI 가격표 snapshot을 반환한다.

    입력:
    - 없음

    반환:
    - `model_name -> OpenAIModelPricing` dict
    """

    return {
        "gpt-5.4": OpenAIModelPricing(
            model_name="gpt-5.4",
            input_per_1m_usd=2.50,
            cached_input_per_1m_usd=0.25,
            output_per_1m_usd=15.00,
        ),
        "gpt-5.4-mini": OpenAIModelPricing(
            model_name="gpt-5.4-mini",
            input_per_1m_usd=0.750,
            cached_input_per_1m_usd=0.075,
            output_per_1m_usd=4.500,
        ),
        "gpt-5.4-nano": OpenAIModelPricing(
            model_name="gpt-5.4-nano",
            input_per_1m_usd=0.20,
            cached_input_per_1m_usd=0.02,
            output_per_1m_usd=1.25,
        ),
    }


def match_pricing(
    model_name: str,
    catalog: dict[str, OpenAIModelPricing] | None = None,
) -> OpenAIModelPricing | None:
    """기능: 모델명에 대응하는 가격표를 찾는다.

    입력:
    - model_name: 실제 응답에 기록된 모델명
    - catalog: 가격표 dict

    반환:
    - 일치하는 가격표 또는 `None`
    """

    catalog = catalog or default_openai_pricing_catalog()
    if model_name in catalog:
        return catalog[model_name]

    lowered = model_name.casefold()
    for key, pricing in catalog.items():
        if lowered.startswith(key.casefold()):
            return pricing
    return None


def estimate_cost_from_usage(
    *,
    model_name: str,
    usage: dict[str, object] | None,
    catalog: dict[str, OpenAIModelPricing] | None = None,
) -> dict[str, object] | None:
    """기능: usage dict와 모델명으로 예상 비용을 계산한다.

    입력:
    - model_name: 모델명
    - usage: `input_tokens`, `output_tokens`, `input_tokens_details`를 포함한 usage dict
    - catalog: 가격표 dict

    반환:
    - 비용 계산 결과 dict 또는 `None`
    """

    if not usage:
        return None

    pricing = match_pricing(model_name=model_name, catalog=catalog)
    if pricing is None:
        return None

    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    input_details = usage.get("input_tokens_details") or {}
    cached_tokens = int(input_details.get("cached_tokens") or 0)
    billable_input_tokens = max(input_tokens - cached_tokens, 0)

    input_cost = (billable_input_tokens / 1_000_000) * pricing.input_per_1m_usd
    cached_input_cost = (
        cached_tokens / 1_000_000
    ) * pricing.cached_input_per_1m_usd
    output_cost = (output_tokens / 1_000_000) * pricing.output_per_1m_usd
    total_cost = input_cost + cached_input_cost + output_cost

    return {
        "model_name": model_name,
        "pricing_model_name": pricing.model_name,
        "pricing_snapshot_date": pricing.snapshot_date,
        "pricing_source_url": pricing.source_url,
        "billable_input_tokens": billable_input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 10),
        "cached_input_cost_usd": round(cached_input_cost, 10),
        "output_cost_usd": round(output_cost, 10),
        "total_cost_usd": round(total_cost, 10),
    }
