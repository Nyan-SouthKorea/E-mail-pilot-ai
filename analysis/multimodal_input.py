"""이메일 분석용 멀티모달 Responses API 입력 payload helper."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from .artifact_summary import ArtifactSummary

IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
}
SUPPORTED_OPENAI_IMAGE_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


def build_email_analysis_input_payload(
    *,
    subject: str,
    sender: str,
    recipient: str,
    body_text: str,
    artifact_summaries: list[ArtifactSummary],
    attachment_paths: list[str | Path] | None = None,
    artifact_ids: list[str] | None = None,
) -> list[dict[str, object]]:
    """기능: 이메일/첨부 분석용 멀티모달 Responses API 입력 payload를 만든다.

    입력:
    - subject: 이메일 제목
    - sender: 발신자 표시 문자열
    - recipient: 수신자 표시 문자열
    - body_text: 본문 텍스트
    - artifact_summaries: 첨부 요약 목록
    - attachment_paths: 실제 첨부 파일 경로 목록
    - artifact_ids: direct attachment 순서에 대응하는 artifact id 목록

    반환:
    - Responses API `input`에 바로 넣을 메시지 payload 목록
    """

    content: list[dict[str, object]] = [
        {
            "type": "input_text",
            "text": build_email_analysis_text_payload(
                subject=subject,
                sender=sender,
                recipient=recipient,
                body_text=body_text,
                artifact_summaries=artifact_summaries,
            ),
        }
    ]
    content.extend(
        build_visual_attachment_content_parts(
            attachment_paths=attachment_paths or [],
            artifact_ids=artifact_ids,
        )
    )
    return [{"role": "user", "content": content}]


def build_email_analysis_text_payload(
    *,
    subject: str,
    sender: str,
    recipient: str,
    body_text: str,
    artifact_summaries: list[ArtifactSummary],
) -> str:
    """기능: 이메일/첨부 분석용 텍스트 요약 payload를 만든다.

    입력:
    - subject: 이메일 제목
    - sender: 발신자 표시 문자열
    - recipient: 수신자 표시 문자열
    - body_text: 본문 텍스트
    - artifact_summaries: 첨부 요약 목록

    반환:
    - 멀티모달 요청 안에 들어갈 텍스트 요약 문자열
    """

    normalized_body = body_text.strip() or "본문 텍스트 없음"
    lines = [
        "[email_metadata]",
        "evidence_id: header_subject",
        f"subject: {subject}",
        "evidence_id: header_sender",
        f"sender: {sender}",
        "evidence_id: header_recipient",
        f"recipient: {recipient}",
        "",
        "[email_body]",
        "evidence_id: body_text",
        normalized_body,
        "",
        "[attachment_artifacts]",
    ]

    if not artifact_summaries:
        lines.append("첨부 없음")
    else:
        for artifact in artifact_summaries:
            lines.append(f"evidence_id: {artifact.evidence_id}")
            lines.append(f"name: {artifact.artifact_name}")
            lines.append(f"kind: {artifact.artifact_kind}")
            lines.append(artifact.summary_text)
            lines.append("")

    return "\n".join(lines).strip()


def build_visual_attachment_content_parts(
    *,
    attachment_paths: list[str | Path],
    artifact_ids: list[str] | None = None,
) -> list[dict[str, object]]:
    """기능: 직접 이미지 첨부를 `input_image` content part 목록으로 만든다.

    입력:
    - attachment_paths: 직접 첨부 파일 경로 목록
    - artifact_ids: direct attachment 순서에 대응하는 artifact id 목록

    반환:
    - Responses API `content` 목록에 붙일 part dict 목록
    """

    parts: list[dict[str, object]] = []
    for offset, path_like in enumerate(attachment_paths):
        path = Path(path_like)
        media_type = _normalize_supported_media_type(path)
        if not _is_direct_image(path, media_type):
            continue

        evidence_id = _resolve_artifact_id(
            artifact_ids=artifact_ids,
            offset=offset,
        )
        parts.append(
            {
                "type": "input_text",
                "text": (
                    "[visual_attachment]\n"
                    f"evidence_id: {evidence_id}\n"
                    f"name: {path.name}\n"
                    f"media_type: {media_type}\n"
                    "이 이미지를 함께 읽어라. 캡처 화면, 표, 문서 스캔, 이미지 안 텍스트와 숫자도 "
                    "분석 대상이다."
                ),
            }
        )
        parts.append(
            {
                "type": "input_image",
                "image_url": _build_data_url(path, media_type=media_type),
                "detail": "high",
            }
        )
    return parts


def _resolve_artifact_id(
    *,
    artifact_ids: list[str] | None,
    offset: int,
) -> str:
    if artifact_ids and offset < len(artifact_ids):
        return artifact_ids[offset]
    return f"artifact_{offset + 1}"


def _guess_media_type(path: Path) -> str:
    guessed_type, _ = mimetypes.guess_type(path.name)
    return guessed_type or "application/octet-stream"


def _normalize_supported_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".gif":
        return "image/gif"
    if suffix == ".webp":
        return "image/webp"
    return _guess_media_type(path)


def _is_direct_image(path: Path, media_type: str) -> bool:
    if media_type in SUPPORTED_OPENAI_IMAGE_MEDIA_TYPES:
        return True
    return path.suffix.lower() in IMAGE_SUFFIXES


def _build_data_url(path: Path, *, media_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
