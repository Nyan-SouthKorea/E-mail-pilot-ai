"""Windows 데스크톱 통합 리뷰센터 실행 진입점."""

from __future__ import annotations

import argparse
import threading
import time
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Email Pilot AI desktop launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="pywebview 창 대신 로컬 브라우저 또는 headless 서버로 띄운다.",
    )
    args = parser.parse_args()

    config = uvicorn.Config(
        "app.server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
    )
    server = uvicorn.Server(config)
    url = f"http://{args.host}:{args.port}"

    if args.no_window:
        server.run()
        return

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.2)

    try:
        import webview

        webview.create_window(
            "Email Pilot AI",
            url,
            width=1360,
            height=920,
        )
        webview.start()
    except Exception:
        webbrowser.open(url)
        thread.join()


if __name__ == "__main__":
    main()
