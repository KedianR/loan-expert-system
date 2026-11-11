"""
Reviewer static HTML report generator.

Implements: FR-14, FR-25, CR-04, WP-14
Spec: docs/reviewer-view.md
Self-contained HTML reports with inline CSS, no JavaScript, no external resources.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from src.api.config import load_config
from src.audit.store import AuditStore, get_connection


def _escape(val: Any) -> str:
    if val is None:
        return ""
    return html.escape(str(val))


CSS_STYLES = """
:root {
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-color: #0f172a;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --primary: #2563eb;
    --success-bg: #dcfce7;
    --success-text: #166534;
    --danger-bg: #fee2e2;
    --danger-text: #991b1b;
    --warning-bg: #fef3c7;
    --warning-text: #92400e;
    --table-stripe: #f1f5f9;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #0f172a;
        --card-bg: #1e293b;
        --text-color: #f8fafc;
        --text-muted: #94a3b8;
        --border-color: #334155;
        --primary: #3b82f6;
        --success-bg: #14532d;
        --success-text: #bbf7d0;
        --danger-bg: #7f1d1d;
        --danger-text: #fecaca;
        --warning-bg: #78350f;
        --warning-text: #fde68a;
        --table-stripe: #1e293b;
    }
}
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    margin: 0;
    padding: 24px;
    line-height: 1.5;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
}
.card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 24px;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
    margin-bottom: 20px;
}
.header h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
}
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
}
.badge-eligible { background-color: var(--success-bg); color: var(--success-text); }
.badge-ineligible { background-color: var(--danger-bg); color: var(--danger-text); }
.badge-refer { background-color: var(--warning-bg); color: var(--warning-text); }
.grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
}
@media (max-width: 900px) {
    .grid { grid-template-columns: 1fr; }
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 13px;
}
th, td {
    border: 1px solid var(--border-color);
    padding: 8px 10px;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: var(--table-stripe);
}
tr.row-fired {
    font-weight: bold;
    background-color: rgba(37, 99, 235, 0.08);
}
pre {
    background: var(--table-stripe);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 12px;
    font-family: monospace;
}
.guidance-box {
    border-left: 4px solid var(--warning-text);
    background-color: var(--warning-bg);
    color: var(--warning-text);
    padding: 12px 16px;
    margin-bottom: 20px;
    border-radius: 4px;
}
"""


def render_queue_page(
    pending_items: list[dict[str, Any]],
    reviewed_count: int,
) -> str:
    rows_html = []
    for item in pending_items:
        d_id = item["decision_id"]
        eval_at = item["evaluated_at"]
        ref_short = item["applicant_ref"][:12] if item["applicant_ref"] else ""
        codes = ", ".join(item.get("reason_codes", []))
        ver = item.get("rule_set_version", "")
        rows_html.append(
            f"<tr>"
            f"<td><a href='{_escape(d_id)}.html'>{_escape(d_id)}</a></td>"
            f"<td>{_escape(eval_at)}</td>"
            f"<td><code>{_escape(ref_short)}</code></td>"
            f"<td>{_escape(codes)}</td>"
            f"<td>{_escape(ver)}</td>"
            f"</tr>"
        )

    table_body = (
        "\n".join(rows_html) if rows_html else "<tr><td colspan='5'>Queue is empty</td></tr>"
    )
    pending_count = len(pending_items)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Reviewer Queue</title>
    <style>{CSS_STYLES}</style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>Reviewer Queue</h1>
        <p><strong>{pending_count} pending, {reviewed_count} reviewed</strong></p>
        <table>
            <thead>
                <tr>
                    <th>Decision ID</th>
                    <th>Evaluated At</th>
                    <th>Applicant Ref</th>
                    <th>Reason Codes</th>
                    <th>Rule Set Version</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""


def render_case_page(
    record: dict[str, Any],
    action: dict[str, Any] | None,
) -> str:
    decision_id = record["decision_id"]
    decision = record["decision"]
    evaluated_at = record["evaluated_at"]
    rule_ver = record["rule_set_version"]
    rule_hash = record["rule_set_hash"]
    rule_hash_short = rule_hash[:12] if rule_hash else ""

    trace = record["trace"]
    notice = record["notice"]

    # Reason codes with text
    reasons_html = []
    notice_reasons = notice.get("reasons", [])
    reason_map = {r["code"]: r["text"] for r in notice_reasons}
    for code in record["reason_codes"]:
        text = reason_map.get(code, "")
        reasons_html.append(f"<li><strong>{_escape(code)}</strong>: {_escape(text)}</li>")
    reasons_list = "<ul>" + "".join(reasons_html) + "</ul>" if reasons_html else "<p>None</p>"

    # Step table
    steps = trace.get("steps", [])
    step_rows = []
    for s in steps:
        order = s.get("order")
        r_id = s.get("rule_id")
        layer = s.get("layer")
        status = s.get("status")
        outcome = s.get("outcome", "")
        code = s.get("reason_code", "")

        facts_list = []
        if "facts_used" in s and s["facts_used"]:
            for k, v in sorted(s["facts_used"].items()):
                facts_list.append(f"{k}={v}")
        if status == "not_evaluated" and "missing" in s:
            facts_list.append(f"missing: {', '.join(s['missing'])}")
        if status == "skipped" and "skipped_reason" in s:
            facts_list.append(f"skipped: {s['skipped_reason']}")

        facts_str = "; ".join(facts_list)
        is_fired = status == "fired"
        row_cls = " class='row-fired'" if is_fired else ""
        status_label = "<strong>FIRED</strong>" if is_fired else _escape(status)

        step_rows.append(
            f"<tr{row_cls}>"
            f"<td>{_escape(order)}</td>"
            f"<td><code>{_escape(r_id)}</code></td>"
            f"<td>{_escape(layer)}</td>"
            f"<td>{status_label}</td>"
            f"<td>{_escape(outcome)}</td>"
            f"<td>{_escape(code)}</td>"
            f"<td>{_escape(facts_str)}</td>"
            f"</tr>"
        )
    steps_table_body = "\n".join(step_rows)

    # Derived values
    derived = trace.get("derived", {})
    derived_rows = []
    for k, v in sorted(derived.items()):
        derived_rows.append(f"<tr><td><code>{_escape(k)}</code></td><td>{_escape(v)}</td></tr>")
    derived_table = (
        "\n".join(derived_rows) if derived_rows else "<tr><td colspan='2'>None</td></tr>"
    )

    # Offer summary if eligible
    offer_summary_html = ""
    if (
        decision == "eligible"
        and notice.get("offer_summary")
        and notice["offer_summary"].get("rows")
    ):
        rows = notice["offer_summary"]["rows"]
        o_rows = []
        for r in rows:
            o_rows.append(
                f"<tr><td><strong>{_escape(r['label'])}</strong></td><td>{_escape(r['value'])}</td></tr>"
            )
        offer_summary_html = f"""
        <div style="margin-top: 20px;">
            <h3>Offer Summary</h3>
            <table>
                <tbody>{"".join(o_rows)}</tbody>
            </table>
        </div>
        """

    # Action block
    if action:
        action_html = f"""
        <div class="card">
            <h3>Reviewer Action</h3>
            <p><strong>Reviewer:</strong> {_escape(action["reviewer"])}</p>
            <p><strong>Action:</strong> <span class="badge badge-{action["effective_outcome"]}">{_escape(action["action"])}</span></p>
            <p><strong>Effective Outcome:</strong> {_escape(action["effective_outcome"])}</p>
            <p><strong>Acted At:</strong> {_escape(action["acted_at"])}</p>
            <p><strong>Reason:</strong></p>
            <pre>{_escape(action["reason"])}</pre>
        </div>
        """
    else:
        curl_example_body = (
            '{"reviewer": "officer_1", "action": "approve", "reason": "<write your reason>"}'
        )
        curl_cmd = (
            f"curl -X POST http://127.0.0.1:8000/v1/decisions/{_escape(decision_id)}/review \\\n"
            f"  -H 'Content-Type: application/json' \\\n"
            f"  -d '{curl_example_body}'"
        )
        action_html = f"""
        <div class="card">
            <h3>Reviewer Action</h3>
            <p>Record an action with <code>POST /v1/decisions/{_escape(decision_id)}/review</code>:</p>
            <pre>{_escape(curl_cmd)}</pre>
        </div>
        """

    badge_class = f"badge-{decision}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Decision {_escape(decision_id)}</title>
    <style>{CSS_STYLES}</style>
</head>
<body>
<div class="container">
    <p><a href="queue.html">&larr; Back to queue</a></p>
    <div class="card">
        <div class="header">
            <div>
                <h1>Decision {_escape(decision_id)}</h1>
                <p style="color: var(--text-muted); margin: 0;">
                    Evaluated at: {_escape(evaluated_at)} |
                    Rule set: {_escape(rule_ver)} (<span title="{_escape(rule_hash)}">{_escape(rule_hash_short)}...</span>)
                </p>
            </div>
            <div>
                <span class="badge {badge_class}" style="font-size: 18px; padding: 6px 16px;">{_escape(decision)}</span>
            </div>
        </div>

        <div class="guidance-box">
            <strong>Guidance:</strong> Do not base a reason on gender, religion, caste or any other protected attribute.
        </div>

        <div class="grid">
            <!-- Left Column: Rule trace -->
            <div>
                <div class="card">
                    <h2>Rule Trace</h2>
                    <h3>Reason Codes</h3>
                    {reasons_list}

                    <h3>Rule Evaluation Steps</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Rule</th>
                                <th>Layer</th>
                                <th>Status</th>
                                <th>Outcome</th>
                                <th>Code</th>
                                <th>Facts Used / Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {steps_table_body}
                        </tbody>
                    </table>

                    <h3 style="margin-top: 20px;">Derived Values</h3>
                    <table>
                        <thead>
                            <tr><th>Field</th><th>Value</th></tr>
                        </thead>
                        <tbody>
                            {derived_table}
                        </tbody>
                    </table>

                    {offer_summary_html}
                </div>
            </div>

            <!-- Right Column: Comparison Baseline & Review Actions -->
            <div>
                <div class="card">
                    <h2>Comparison baseline</h2>
                    <div style="padding: 12px; border: 1px solid var(--border-color); border-radius: 6px; background-color: var(--table-stripe);">
                        <p style="margin: 0; font-weight: bold;">ML baseline score</p>
                        <p style="margin: 8px 0 0 0; color: var(--text-muted);">
                            Not available. The baseline model is built in Phase 4.
                        </p>
                        <p style="margin: 4px 0 0 0; font-size: 11px; color: var(--text-muted);">
                            This score does not feed the decision.
                        </p>
                    </div>
                </div>

                {action_html}
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""


def generate_review_reports(
    db_path: Path | str | None = None,
    output_dir: Path | str | None = None,
) -> tuple[int, int]:
    """
    Generate static HTML reports from audit store.
    Returns (num_queue_cases, num_reviewed_cases).
    """
    config = load_config()
    db = Path(db_path) if db_path else Path(config.audit_db_path)
    out = Path(output_dir) if output_dir else Path(config.review_report_dir)
    out.mkdir(parents=True, exist_ok=True)

    store = AuditStore(db)
    conn = get_connection(db)
    try:
        # Get pending cases in queue
        pending_items = store.get_pending_review_queue(limit=1000)

        # Count reviewed cases
        cur = conn.execute("SELECT COUNT(DISTINCT decision_id) as cnt FROM reviewer_actions")
        row = cur.fetchone()
        reviewed_count = int(row["cnt"]) if row else 0

        # 1. Render queue.html
        queue_html = render_queue_page(pending_items, reviewed_count)
        (out / "queue.html").write_text(queue_html, encoding="utf-8")

        # 2. Render case pages for queue cases
        for item in pending_items:
            d_id = item["decision_id"]
            rec = store.get_decision(d_id)
            if rec:
                act = store.get_reviewer_action(d_id)
                case_html = render_case_page(rec, act)
                (out / f"{d_id}.html").write_text(case_html, encoding="utf-8")

        # 3. Render case pages for any decisions that have a reviewer action
        cur = conn.execute("SELECT DISTINCT decision_id FROM reviewer_actions")
        for r in cur.fetchall():
            d_id = r["decision_id"]
            rec = store.get_decision(d_id)
            if rec:
                act = store.get_reviewer_action(d_id)
                case_html = render_case_page(rec, act)
                (out / f"{d_id}.html").write_text(case_html, encoding="utf-8")

        return len(pending_items), reviewed_count
    finally:
        conn.close()


if __name__ == "__main__":
    pending, reviewed = generate_review_reports()
    print(f"Generated review reports: {pending} pending in queue, {reviewed} reviewed.")
