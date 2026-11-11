# Data Flows (v0.1)

Requirements: FR-15, FR-16, FR-20, DR-02, DR-03, NFR-07. Shows what moves where, so a reviewer of the code can check that no store is read or written by a component that is not listed. The component names and the calling order are those of `docs/05-architecture.md` (calls go downward only).

## 1. Flow of one decision

```text
caller
  |  POST /v1/decisions  (application JSON)
  v
src/api  ---- validates against schemas/input.schema.json ----> 422 INVALID_REQUEST (stop; nothing written)
  |
  v
src/facts  builds the fact base; absent or null becomes unknown
  |
  v
src/engine  decide(application, rule_set) -> engine result (fired, not fired, not evaluated, skipped, derived)
  |   reads: params/, rules/ (through the rule loader only)
  |   calls: src/calc (pure functions)
  v
src/explain  builds the trace from the engine result; reason_codes from fired steps; notice from the trace
  |   reads: rules/reason_codes.toml, config/notice_frame.toml
  |   (counterfactual guidance calls decide() again on a changed input; writes nothing)
  v
src/audit  one transaction: audit_inputs + audit_records (hash chain)  ---- failure ----> 503 AUDIT_UNAVAILABLE
  |
  v
src/api  returns the response (decision, reason_codes, offer, notice, trace)
```

## 2. Stores, writers and readers

| Store | Written by | Read by | Never read by |
|---|---|---|---|
| `params/`, `rules/` | policy owner through Git | rule loader | any other component |
| `config/` | developer through Git | api, audit, explain | the engine and the rules |
| `audit_records` | `src/audit` | reviewer report, replay, `eval/` | the engine, the rules |
| `audit_inputs` | `src/audit` | replay | reviewer report, `eval/`, the engine |
| `reviewer_actions` | review endpoint | reviewer report, `eval/` | the engine, the rules |
| audit-only attribute store (Phase 4) | data loader, once per dataset | `eval/` fairness module | the engine, the rules, the fact builder, the ML features, the audit log |
| ML outputs (Phase 4) | `ml/` | reviewer report, `eval/` | the engine |

## 3. Flow of a replay

```text
make replay-all  or  POST /v1/decisions/{id}/replay
  -> src/audit reads audit_records + audit_inputs
  -> src/api calls the same decide() and the same trace/notice builders, with the current rule files
  -> compares decision, reason_codes, offer, trace (ignoring decision_id and evaluated_at)
  -> returns match / differences; writes nothing
```

## 4. Flow of a review

```text
GET /v1/review/queue         audit_records (decision = refer) minus decisions with a reviewer action
POST /v1/decisions/{id}/review   checks section 4 of the oversight policy, then inserts one reviewer_actions row
make review-report           reads audit_records + reviewer_actions, writes HTML under reports/reviewer/
```

## 5. What leaves the system

Only the API response and the generated reports. The API response contains the notice and the trace. The reviewer reports contain the trace and the reviewer's own text. Application logs contain decision IDs, input hashes and error codes, never input fields (NFR-07).

## 6. Boundaries that tests and review check

1. No import of `src/audit` from `src/engine` or `src/calc`.
2. No import of `src/engine` internals from `ml/` or `eval/`; only the public `decide`.
3. Only `eval/` opens the attribute store.
4. No `float` in `src/explain` (notice formatting uses `Decimal`).
5. No SQL `UPDATE` or `DELETE` statement anywhere in `src/`.
