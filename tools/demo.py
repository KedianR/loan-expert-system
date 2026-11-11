"""
Demo runner for Phase 3.

Implements: WP-14, docs/07-implementation-plan.md
Spec:
- Uses a fresh audit database
- Sends TV1 to TV9 and N-R01 through the FastAPI decision API
- Prints decision, reason codes, headline, reasons, guidance, basis, and offer summary rows
- Compares TV1-TV9 with tests/golden/vectors.json (PASS/FAIL per vector)
- Runs replay-all, audit-verify, and review-report
- Prints path of the REFER case page
- Exits non-zero on any FAIL
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from src.api.app import create_app  # noqa: E402
from src.api.config import load_config  # noqa: E402
from src.api.review_report import generate_review_reports  # noqa: E402
from src.api.service import DecisionService  # noqa: E402
from src.audit.replay_all import main as replay_all_main  # noqa: E402
from src.audit.store import AuditStore  # noqa: E402
from src.audit.verify import main as verify_main  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = REPO_ROOT / "tests" / "golden" / "vectors.json"
NOTICE_CASES_PATH = REPO_ROOT / "tests" / "golden" / "notice_cases.json"


def main() -> None:
    config = load_config()
    db_path = Path(config.audit_db_path)

    # 1. Fresh audit database
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    audit_store = AuditStore(db_path)
    service = DecisionService(config=config, repo_root=REPO_ROOT, audit_store=audit_store)
    app = create_app(service=service)
    client = TestClient(app)

    # 2. Load test vectors TV1 to TV9
    vectors_data = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]
    notice_cases = json.loads(NOTICE_CASES_PATH.read_text(encoding="utf-8"))["cases"]

    # Find N-R01
    nr01_case = next((c for c in notice_cases if c["id"] == "N-R01"), None)
    if not nr01_case:
        print("ERROR: N-R01 case not found in notice_cases.json", file=sys.stderr)
        sys.exit(1)

    all_cases = []
    for vec in vectors_data:
        all_cases.append(
            {
                "id": vec["id"],
                "input": vec["input"],
                "expected_decision": vec["expected"]["decision"],
                "is_vector": True,
            }
        )

    all_cases.append(
        {
            "id": "N-R01",
            "input": nr01_case["input"],
            "expected_decision": nr01_case["expected"]["decision"],
            "is_vector": False,
        }
    )

    print("================================================================================")
    print("LOAN EXPERT SYSTEM - PHASE 3 DEMO")
    print("================================================================================")

    failed_vectors = []
    refer_case_id = None

    for idx, case in enumerate(all_cases, 1):
        c_id = case["id"]
        inp = case["input"]
        exp_dec = case["expected_decision"]

        res = client.post("/v1/decisions", json=inp)
        if res.status_code != 200:
            print(f"[{c_id}] API ERROR {res.status_code}: {res.text}", file=sys.stderr)
            if case["is_vector"]:
                failed_vectors.append(c_id)
            continue

        data = res.json()
        dec_id = data["decision_id"]
        act_dec = data["decision"]
        reason_codes = data.get("reason_codes", [])
        notice = data.get("notice", {})
        headline = notice.get("headline", "")
        reasons = notice.get("reasons", [])
        guidance = notice.get("guidance", [])
        basis = notice.get("basis", [])
        offer_summary = notice.get("offer_summary")

        status_str = "PASS" if act_dec == exp_dec else "FAIL"
        if status_str == "FAIL" and case["is_vector"]:
            failed_vectors.append(c_id)

        if c_id == "N-R01":
            refer_case_id = dec_id

        print(f"\n--- {c_id} ({dec_id}): {act_dec.upper()} [{status_str}] ---")
        print(f"Reason Codes : {', '.join(reason_codes) if reason_codes else 'None'}")
        print(f"Headline     : {headline}")
        print("Reasons      :")
        for r in reasons:
            print(f"  * [{r['code']}] {r['text']}")

        if guidance:
            print("Guidance     :")
            for g in guidance:
                print(f"  * [{g['code']}] {g['text']} (verified: {g['verified_decision']})")

        if basis:
            print("Basis Lines  :")
            for b in basis:
                print(f"  * {b['label']}: {b['text']}")

        if offer_summary and offer_summary.get("rows"):
            print("Offer Summary:")
            for row in offer_summary["rows"]:
                print(f"  * {row['label']:<20}: {row['value']}")

    print("\n================================================================================")
    print("VECTOR COMPARISON SUMMARY")
    print("================================================================================")
    for vec in vectors_data:
        v_id = vec["id"]
        v_status = "FAIL" if v_id in failed_vectors else "PASS"
        print(f"Vector {v_id:<5}: {v_status}")

    if failed_vectors:
        print(
            f"\nDEMO FAILED: {len(failed_vectors)} vector(s) failed: {failed_vectors}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n================================================================================")
    print("RUNNING REPLAY-ALL")
    print("================================================================================")
    try:
        replay_all_main()
    except SystemExit as e:
        if e.code != 0:
            print("make replay-all failed", file=sys.stderr)
            sys.exit(e.code)

    print("\n================================================================================")
    print("RUNNING AUDIT-VERIFY")
    print("================================================================================")
    try:
        verify_main()
    except SystemExit as e:
        if e.code != 0:
            print("make audit-verify failed", file=sys.stderr)
            sys.exit(e.code)

    print("\n================================================================================")
    print("GENERATING REVIEWER REPORT")
    print("================================================================================")
    pending_cnt, reviewed_cnt = generate_review_reports(db_path=db_path)
    print(f"Reviewer report generated: {pending_cnt} pending in queue, {reviewed_cnt} reviewed.")

    if refer_case_id:
        refer_page_path = REPO_ROOT / config.review_report_dir / f"{refer_case_id}.html"
        print(f"\nREFER case page: {refer_page_path}")

    print("\nDEMO COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
