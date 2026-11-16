"""Capture UI v2 screenshots using Playwright."""

from __future__ import annotations

import json
import pathlib
import sys
import threading
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uvicorn
from playwright.sync_api import sync_playwright

import src.ui.app as ui_app

OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "docs" / "reports" / "ui-v2-screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("1280", {"width": 1280, "height": 900}),
    ("390", {"width": 390, "height": 844}),
]

SCHEMES = ["light", "dark"]


def main():
    config = uvicorn.Config(ui_app.app, host="127.0.0.1", port=8899, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.5)

    base_url = "http://127.0.0.1:8899"
    captured = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for vp_name, vp_dims in VIEWPORTS:
            for scheme in SCHEMES:
                # 1. Apply (empty)
                ctx = browser.new_context(viewport=vp_dims, color_scheme=scheme)
                page = ctx.new_page()
                page.goto(f"{base_url}/")
                page.wait_for_selector(".preset-btn")
                path = OUT_DIR / f"apply_empty_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))

                # 2. Apply (TV1 filled)
                page.query_selector_all(".preset-btn")[0].click()  # TV1
                time.sleep(0.3)
                path = OUT_DIR / f"apply_tv1_filled_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))

                # 3. Report for ELIGIBLE
                page.click("#submit-btn")
                page.wait_for_selector(".ml-disclaimer", timeout=10000)
                time.sleep(0.5)
                path = OUT_DIR / f"report_eligible_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))
                ctx.close()

                # 4. Report for INELIGIBLE (TV6)
                ctx = browser.new_context(viewport=vp_dims, color_scheme=scheme)
                page = ctx.new_page()
                page.goto(f"{base_url}/")
                page.wait_for_selector(".preset-btn")
                # TV6 is 6th preset (index 5)
                page.query_selector_all(".preset-btn")[5].click()
                time.sleep(0.3)
                page.click("#submit-btn")
                page.wait_for_selector(".ml-disclaimer", timeout=10000)
                time.sleep(0.5)
                path = OUT_DIR / f"report_ineligible_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))
                ctx.close()

                # 5. Report for REFER (TV1 with credit score cleared)
                ctx = browser.new_context(viewport=vp_dims, color_scheme=scheme)
                page = ctx.new_page()
                page.goto(f"{base_url}/")
                page.wait_for_selector(".preset-btn")
                page.query_selector_all(".preset-btn")[0].click()  # TV1
                time.sleep(0.3)
                page.fill("#credit_score", "")  # Clear credit score -> triggers R01 referral
                page.click("#submit-btn")
                page.wait_for_selector(".ml-disclaimer", timeout=10000)
                time.sleep(0.5)
                path = OUT_DIR / f"report_refer_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))
                ctx.close()

                # 6. Results
                ctx = browser.new_context(viewport=vp_dims, color_scheme=scheme)
                page = ctx.new_page()
                page.goto(f"{base_url}/results")
                page.wait_for_selector(".tab-btn")
                time.sleep(1.0)
                path = OUT_DIR / f"results_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))
                ctx.close()

                # 7. About
                ctx = browser.new_context(viewport=vp_dims, color_scheme=scheme)
                page = ctx.new_page()
                page.goto(f"{base_url}/about")
                page.wait_for_selector(".app-bar")
                time.sleep(0.3)
                path = OUT_DIR / f"about_{vp_name}_{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                captured.append(str(path))
                ctx.close()

        browser.close()

    server.should_exit = True
    print(f"Captured {len(captured)} screenshots.")
    for c in captured:
        print(f"  {c}")


if __name__ == "__main__":
    main()
