# Reviewer View Specification (v0.1)

Requirements: FR-14, FR-25, CR-04. Decision CP-10 (web page or generated report): **a generated, self-contained HTML report plus the JSON endpoints**. No web framework, no JavaScript framework, no server-side pages. This is a default set by the reviewer of the plan; the owner may change it before Phase 3 starts, and the change is then a new decision in `docs/00-reference.md`.

Why: the SRS acceptance for FR-25 is "both visible for one applicant on one screen". A static page meets it, costs little to build, can be attached to the final report, and has no moving parts to test.

## 1. What is built

| Item | How |
|---|---|
| `GET /v1/review/queue` | JSON list of REFER decisions with no reviewer action yet (`queue_response` in `schemas/response.schema.json`) |
| `POST /v1/decisions/{decision_id}/review` | records one action (`docs/human-oversight-policy.md`) |
| `make review-report` | writes `reports/reviewer/queue.html` and one `reports/reviewer/<decision_id>.html` per decision in the queue, plus per-case pages for decisions that have an action. Reads the audit store directly; needs no running server |

`reports/reviewer/` is not committed.

## 2. Queue page (`queue.html`)

A table, oldest first (the order the cases should be worked): decision ID (link to its case page), evaluated at, applicant ref (first 12 characters of the hash), reason codes, rule-set version. Above it, one line: `<n> pending, <m> reviewed`.

## 3. Case page (`<decision_id>.html`)

One page, two columns on a wide screen, stacked on a narrow one. All text is escaped; the page has no script, no external font, image or stylesheet link (it must open offline). Inline CSS only, light and dark colours through `prefers-color-scheme`.

Header: decision ID, decision (large), evaluated at, rule-set version and hash (first 12 characters, full value in a `title`).

**Left column, "Rule trace" (FR-10):**

- Reason codes, each with its applicant text from the notice.
- A table of every step in order: order, rule ID, layer, status, outcome, reason code, facts used (name and value). Status `fired` rows are visually distinct (bold plus a text label, not colour alone). `not_evaluated` rows show the `missing` fields. `skipped` rows show `skipped_reason`.
- "Derived values": every key of `trace.derived`.
- For an eligible decision: the offer summary rows.

**Right column, "Comparison baseline" (FR-25):** a labelled block "ML baseline score". In Phase 3 it reads: "Not available. The baseline model is built in Phase 4." In Phase 4 the report generator fills it from the experiment outputs (score, predicted class, top SHAP features), with the line "This score does not feed the decision." The block always exists, so the layout does not change. Do not invent a score.

**Reviewer action block:** shows the action history if there is one (reviewer, action, reason, time, effective outcome); otherwise the instruction "Record an action with `POST /v1/decisions/<id>/review`" and a ready-made `curl` example for this decision, with the reason left as `<write your reason>`.

**Guidance box (static text from the oversight policy):** "Do not base a reason on gender, religion, caste or any other protected attribute."

## 4. Tests (lean mode)

Reviewer-view tests are not required for the Phase 3 gate. Build `make review-report` and run it once in `make demo` for the REFER case so the evidence exists. One smoke check is enough: the report for the demo REFER case contains the decision ID, every rule ID of the trace, and the text "Not available".
