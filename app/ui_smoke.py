"""FastAPI + pywebview 앱 UI의 반복 smoke를 수행한다."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path
import time

from fastapi.testclient import TestClient

from app.server import SERVER_STATE, app, set_shell_context
from runtime.workspace import load_shared_workspace


@dataclass(slots=True)
class AppUiSmokeStep:
    """기능: 앱 UI smoke의 단계별 결과를 표현한다."""

    step: str
    status: str
    detail: str
    status_code: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class AppUiSmokeReport:
    """기능: 앱 UI smoke 전체 결과를 표현한다."""

    generated_at: str
    workspace_root: str
    report_relpath: str
    status: str
    steps: list[AppUiSmokeStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "workspace_root": self.workspace_root,
            "report_relpath": self.report_relpath,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "notes": list(self.notes),
        }


def run_app_ui_smoke(
    *,
    workspace_root: str | Path,
    workspace_password: str,
) -> AppUiSmokeReport:
    """기능: 앱 핵심 화면과 관리도구를 빠르게 검증하는 UI smoke를 실행한다."""

    workspace = load_shared_workspace(workspace_root)
    app_logs_root = workspace.profile_paths().runtime_logs_root() / "app"
    app_logs_root.mkdir(parents=True, exist_ok=True)
    report_path = app_logs_root / f"{datetime.now().strftime('%y%m%d_%H%M')}_ui_smoke.json"
    template_relpath = workspace.to_workspace_relative(workspace.profile_paths().template_workbook_path())

    steps: list[AppUiSmokeStep] = []
    SERVER_STATE.current_session = None
    set_shell_context(
        shell_mode="desktop_window",
        native_dialog_state="desktop_pending",
        startup_log_path="C:\\Users\\tester\\AppData\\Roaming\\EmailPilotAI\\startup.log",
        official_local_bundle_path="D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe",
        native_dialog_expected=True,
        launch_path="D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe",
    )
    client = TestClient(app)

    def _record(step: str, response=None, ok: bool = True, detail: str = "") -> None:
        steps.append(
            AppUiSmokeStep(
                step=step,
                status="pass" if ok else "fail",
                detail=detail,
                status_code=getattr(response, "status_code", None),
            )
        )

    try:
        home_response = client.get("/")
        _record(
            step="home_without_workspace",
            response=home_response,
            ok=(
                home_response.status_code == 200
                and "세이브 파일 불러오기" in home_response.text
                and "세이브 파일 가이드" in home_response.text
                and "앱 실행 진단" in home_response.text
                and "앱 전용 창 연결 확인 중입니다." in home_response.text
                and "브라우저 fallback" not in home_response.text
            ),
            detail="워크스페이스가 없을 때 홈 화면과 세이브 파일 가이드 진입이 보여야 한다.",
        )

        open_response = client.post(
            "/workspace/open",
            data={
                "workspace_root": str(workspace.root()),
                "workspace_password": workspace_password,
            },
            follow_redirects=False,
        )
        _record(
            step="open_workspace",
            response=open_response,
            ok=open_response.status_code == 303,
            detail="공유 워크스페이스를 편집 모드로 열어야 한다.",
        )

        routes = [
            ("/", "home_with_workspace", "앱 실행 진단"),
            ("/settings", "settings_page", "공식 실행 파일"),
            ("/review", "review_page", "통합 리뷰센터"),
            ("/admin/features", "admin_features_page", "startup.log"),
            ("/jobs/current", "job_status_api", '"status"'),
            ("/workspace/guide", "workspace_guide_page", "세이브 파일 가이드"),
        ]
        for route, step_name, expected_text in routes:
            response = client.get(route)
            text = response.text if "application/json" not in response.headers.get("content-type", "") else response.text
            _record(
                step=step_name,
                response=response,
                ok=response.status_code == 200 and expected_text in text,
                detail=f"{route} 응답에 기대 문자열 `{expected_text}`가 있어야 한다.",
            )

        settings_save_response = client.post(
            "/settings/save",
            data={
                "llm_model": "gpt-5.4",
                "llm_api_key": "sk-smoke",
                "email_address": "smoke@example.com",
                "login_username": "smoke-login",
                "mailbox_password": "smoke-password",
                "default_folder": "INBOX",
                "template_workbook_relative_path": template_relpath,
            },
            follow_redirects=True,
        )
        _record(
            step="settings_save",
            response=settings_save_response,
            ok=(
                settings_save_response.status_code == 200
                and "설정을 저장했다." in settings_save_response.text
                and "마지막 저장" in settings_save_response.text
            ),
            detail="설정 저장 후 성공 배너와 마지막 저장 안내가 보여야 한다.",
        )

        rebuild_response = client.post("/review/rebuild", follow_redirects=False)
        _record(
            step="review_rebuild_trigger",
            response=rebuild_response,
            ok=rebuild_response.status_code == 303,
            detail="리뷰센터에서 운영 workbook 재반영 job을 시작해야 한다.",
        )

        final_job_status = "running"
        deadline = time.time() + 20.0
        while time.time() < deadline:
            current_job = client.get("/jobs/current")
            payload = current_job.json()
            final_job_status = str(payload.get("status") or "")
            if final_job_status != "running":
                break
            time.sleep(0.2)
        _record(
            step="review_rebuild_complete",
            ok=final_job_status == "completed",
            detail=f"최종 job 상태: {final_job_status}",
        )

        close_response = client.post("/workspace/close", follow_redirects=False)
        _record(
            step="close_workspace",
            response=close_response,
            ok=close_response.status_code == 303,
            detail="smoke 종료 시 워크스페이스를 닫아야 한다.",
        )
        status = "completed" if all(step.status == "pass" for step in steps) else "failed"
    finally:
        if SERVER_STATE.current_session is not None and SERVER_STATE.current_session.lock_handle is not None:
            SERVER_STATE.current_session.lock_handle.release()
        SERVER_STATE.current_session = None
        set_shell_context(
            shell_mode="browser_fallback",
            native_dialog_state="browser_fallback",
        )

    report = AppUiSmokeReport(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        workspace_root=str(workspace.root()),
        report_relpath=workspace.to_workspace_relative(report_path),
        status=status,
        steps=steps,
        notes=[
            "이 smoke는 앱 핵심 화면과 관리도구 접근, 재반영 버튼, background job polling을 함께 확인한다.",
            "실메일이 없는 샘플 워크스페이스에서도 반복 실행할 수 있다.",
        ],
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="desktop app UI smoke")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--workspace-password", required=True)
    args = parser.parse_args()

    result = run_app_ui_smoke(
        workspace_root=args.workspace_root,
        workspace_password=args.workspace_password,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
