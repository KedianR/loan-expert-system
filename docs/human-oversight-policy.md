# Human Oversight Policy (v0.1)

Requirements: FR-14, FR-25, CR-04, CR-01. Defines when a person must look at a decision, what the person may do, and what is recorded. Prototype scope: the reviewers are the project's evaluator and owner, on synthetic data.

## 1. Principles

1. The rule engine decides. A reviewer never changes a stored decision; a reviewer adds a recorded action next to it.
2. Every REFER decision goes to a person. No REFER decision is turned into an approval or a denial by software.
3. Every reviewer action carries a reason that the reviewer wrote. No reason, no action.
4. Nothing a reviewer does is hidden: actions are stored in an append-only table and are visible in the reviewer report and to evaluation.
5. Reviewers see the rule trace. The ML score appears beside it from Phase 4 and is labelled as a comparison baseline that does not feed the decision.

## 2. What goes to review

| Decision | In the queue? |
|---|---|
| `refer` (V01, R01, R02, R03, or the default `NO_RULE_APPLICABLE`) | Yes, until it has one action |
| `ineligible` | No. A reviewer may still look it up by ID and add an `override` (section 4) |
| `eligible` | No. A reviewer may look it up by ID and add an `override` |

## 3. What the reviewer sees

The case page (see `docs/reviewer-view.md`) shows the decision, every reason code with its applicant text, the full rule trace (each rule: fired, not fired, not evaluated, skipped, and the facts it used), the rule-set version and hash, and the ML score block (empty until Phase 4). It does not show protected attributes. It does not show raw input beyond the facts in the trace.

## 4. Actions and what each means

| Decision | `approve` | `deny` | `override` |
|---|---|---|---|
| `refer` | Allowed. Effective outcome `approved`: the reviewer accepts the application for manual handling. No amount or price is computed or stored (out of scope for v0.1). | Allowed. Effective outcome `denied`. | Not allowed (`ACTION_NOT_ALLOWED`): a referral has no system outcome to override. |
| `ineligible` | Not allowed. | Not allowed. | Allowed. Effective outcome `approved`: the reviewer departs from the system's denial. |
| `eligible` | Not allowed. | Not allowed. | Allowed. Effective outcome `denied`: the reviewer departs from the system's eligibility. |

The queue holds `refer` decisions only. One action resolves a case: a second action on the same decision returns `ALREADY_REVIEWED` (409). A mistake is handled by a note in the evaluation, not by editing.

## 5. Mandatory reason

`reason` is required for every action. It is trimmed; it must have at least `min_reason_length` characters (`config/app.toml`, default 10). A shorter or empty reason returns `REASON_REQUIRED` (422) and nothing is written (FR-14). The reason is stored word for word and shown in the reviewer report.

## 6. Overrides and fairness

Every `override` is counted in the evaluation: how many, in which direction, on which reason codes. Group-level override rates are part of the fairness review (Phase 5). A reviewer reason must not refer to a protected attribute; the prototype cannot check this automatically, and the reviewer guidance says so on the case page.

## 7. What the applicant is told

The applicant notice for a REFER decision says a person will review the application and lists the reasons. After a review the applicant-facing wording is out of scope in v0.1 (no contact path is built).

## 8. Limits

There is no reviewer authentication in the prototype (local use only, `host` is 127.0.0.1). The `reviewer` field is a label the caller supplies, not a verified identity. The final report states this as a limit.
