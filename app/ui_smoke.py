"""FastAPI + pywebview 앱 UI의 반복 smoke를 수행한다."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import re
import time

from fastapi.testclient import TestClient

from app.server import SERVER_STATE, app, set_shell_context
from runtime import (
    LocalAppSettings,
    LocalDeviceSecrets,
    default_device_secrets_path,
    default_local_settings_path,
    save_local_app_settings,
    save_local_device_secrets,
)
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
    local_settings_path = default_local_settings_path()
    device_secrets_path = default_device_secrets_path()
    previous_local_settings = (
        local_settings_path.read_text(encoding="utf-8")
        if local_settings_path.exists()
        else None
    )
    previous_device_secrets = (
        device_secrets_path.read_text(encoding="utf-8")
        if device_secrets_path.exists()
        else None
    )
    previous_picker_test_response = os.environ.get("EPA_PICKER_TEST_RESPONSE")

    steps: list[AppUiSmokeStep] = []
    if SERVER_STATE.current_session is not None and SERVER_STATE.current_session.lock_handle is not None:
        SERVER_STATE.current_session.lock_handle.release()
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
        os.environ["EPA_PICKER_TEST_RESPONSE"] = str(workspace.root())
        save_local_app_settings(LocalAppSettings(), path=local_settings_path)
        save_local_device_secrets(LocalDeviceSecrets(), path=device_secrets_path)
        home_response = client.get("/")
        home_text = home_response.text
        _record(
            step="home_without_workspace",
            response=home_response,
            ok=(
                home_response.status_code == 200
                and "세 단계만 끝내면 바로 업무를 시작할 수 있습니다" in home_text
                and "처음 사용하는 방법" in home_text
                and "기존 세이브 열기" in home_text
                and "새 세이브 만들기" in home_text
                and "파일 탐색기 다시 확인" in home_text
                and "브라우저 fallback" not in home_text
                and re.search(r'<button[^>]*data-picker-target="open_workspace_root"[^>]*disabled', home_text) is None
                and re.search(r'<button[^>]*data-picker-target="save_parent_dir"[^>]*disabled', home_text) is None
            ),
            detail="세이브 파일 미오픈 상태에서 3단계 시작 화면과 활성화된 찾아보기 버튼이 보여야 한다.",
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
            ("/", "home_with_workspace", "다음 행동"),
            ("/sync", "sync_page", "선택한 개수로 동기화"),
            ("/settings", "settings_page", "계정 연결 확인"),
            ("/review", "review_page", "엑셀 반영 대상만"),
            ("/admin/features", "admin_features_page", "고급 도구"),
            ("/jobs/current", "job_status_api", '"status"'),
            ("/app-meta", "app_meta_api", '"app_id":"email_pilot_ai_desktop"'),
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
                and "설정을 저장했습니다." in settings_save_response.text
                and "다음 단계" in settings_save_response.text
                and "계정 연결 확인" in settings_save_response.text
            ),
            detail="설정 저장 후 성공 배너와 마지막 저장 안내가 보여야 한다.",
        )

        settings_page_response = client.get("/settings")
        settings_page_text = settings_page_response.text
        _record(
            step="settings_browse_button_enabled",
            response=settings_page_response,
            ok=(
                settings_page_response.status_code == 200
                and 'data-picker-target="template_workbook_relative_path"' in settings_page_text
                and re.search(
                    r'<button[^>]*data-picker-target="template_workbook_relative_path"[^>]*disabled',
                    settings_page_text,
                ) is None
            ),
            detail="설정 화면의 엑셀 양식 찾아보기 버튼도 기본 disabled가 아니어야 한다.",
        )

        picker_diag_response = client.get("/diagnostics/picker-bridge")
        picker_diag_payload = picker_diag_response.json()
        _record(
            step="picker_bridge_diagnostics",
            response=picker_diag_response,
            ok=picker_diag_response.status_code == 200 and "native_dialog_supported" in picker_diag_payload,
            detail="파일 탐색기 self-test endpoint가 진단 결과를 반환해야 한다.",
        )

        picker_folder_response = client.post(
            "/diagnostics/pick-folder",
            data={
                "current_path": "",
                "workspace_root": str(workspace.root()),
            },
        )
        picker_folder_payload = picker_folder_response.json()
        _record(
            step="picker_folder_endpoint",
            response=picker_folder_response,
            ok=picker_folder_response.status_code == 200 and bool(picker_folder_payload.get("ok")) and bool(picker_folder_payload.get("path")),
            detail="파일 탐색기 route가 테스트 override 기준으로 선택 경로를 반환해야 한다.",
        )

        sync_page_response = client.get("/sync")
        sync_text = sync_page_response.text
        _record(
            step="sync_scope_presets",
            response=sync_page_response,
            ok=(
                sync_page_response.status_code == 200
                and "최근 100건" in sync_text
                and "최근 500건" in sync_text
                and "최근 1000건" in sync_text
                and "직접 입력" in sync_text
            ),
            detail="동기화 화면에 preset + 직접입력 옵션이 보여야 한다.",
        )

        rebuild_response = client.post("/review/rebuild", follow_redirects=False)
        _record(
            step="review_rebuild_trigger",
            response=rebuild_response,
            ok=rebuild_response.status_code == 303,
            detail="리뷰센터에서 운영 엑셀 재반영 job을 시작해야 한다.",
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

        recent_reopen_response = client.post(
            "/workspace/recent/open",
            data={"workspace_root": str(workspace.root())},
            follow_redirects=False,
        )
        _record(
            step="reopen_recent_workspace",
            response=recent_reopen_response,
            ok=recent_reopen_response.status_code == 303,
            detail="이 PC에 저장된 암호로 최근 세이브를 바로 다시 열 수 있어야 한다.",
        )

        final_close_response = client.post("/workspace/close", follow_redirects=False)
        _record(
            step="close_workspace_after_recent_reopen",
            response=final_close_response,
            ok=final_close_response.status_code == 303,
            detail="recent reopen 검증 후 다시 세이브를 닫아야 한다.",
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
        if previous_local_settings is None:
            local_settings_path.unlink(missing_ok=True)
        else:
            local_settings_path.parent.mkdir(parents=True, exist_ok=True)
            local_settings_path.write_text(previous_local_settings, encoding="utf-8")
        if previous_device_secrets is None:
            device_secrets_path.unlink(missing_ok=True)
        else:
            device_secrets_path.parent.mkdir(parents=True, exist_ok=True)
            device_secrets_path.write_text(previous_device_secrets, encoding="utf-8")
        if previous_picker_test_response is None:
            os.environ.pop("EPA_PICKER_TEST_RESPONSE", None)
        else:
            os.environ["EPA_PICKER_TEST_RESPONSE"] = previous_picker_test_response

    report = AppUiSmokeReport(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        workspace_root=str(workspace.root()),
        report_relpath=workspace.to_workspace_relative(report_path),
        status=status,
        steps=steps,
        notes=[
            "이 smoke는 앱 핵심 화면과 관리도구 접근, 재반영 버튼, background job polling을 함께 확인한다.",
            "실메일이 없는 샘플 워크스페이스에서도 반복 실행할 수 있다.",
            "파일 탐색기 route는 EPA_PICKER_TEST_RESPONSE override로 GUI wrapper 경로를 자동 검증한다.",
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
