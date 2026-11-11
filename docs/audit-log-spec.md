# Audit Log and Replay Specification (v0.1)

Requirements: FR-15, FR-16, FR-19, NFR-02, NFR-08, DR-03, CR-04. Source of truth for the stores, the record layout, the hash chain, replay and the append-only rule. Where this file and `docs/05-architecture.md` section 4 differ, this file governs (it adds the replay input store, decision P3-3).

## 1. Stores

One SQLite file, path from `config/app.toml` key `audit_db_path` (default `data/audit/audit.sqlite`). Never committed. Three tables, all insert-only.

| Table | Written by | Read by | Holds |
|---|---|---|---|
| `audit_records` | `src/audit` only | reviewer view, replay, evaluation | one row per decision |
| `audit_inputs` | `src/audit` only, same transaction as the record | replay only | the validated input, keyed by `input_hash` (decision P3-3) |
| `reviewer_actions` | the review endpoint only | reviewer view, evaluation, audit reports | one row per reviewer action |

Why `audit_inputs` exists: FR-16 needs the input to re-run a decision, and DR-03 keeps raw fields out of the audit log. The input lives in a separate table with its own reader list (replay only). The data is synthetic (docs/privacy-statement.md). If `store_input_snapshot` is `false` in config, no row is written and replay returns `match: false` with `note: "no input snapshot"`; the default is `true`.

## 2. Record layout

`audit_records` columns:

| Column | Type | Meaning |
|---|---|---|
| `seq` | INTEGER PRIMARY KEY AUTOINCREMENT | position in the chain, starts at 1 |
| `decision_id` | TEXT UNIQUE NOT NULL | `d-` plus `seq` zero-padded to 4 digits (`d-0001`); more digits when needed |
| `applicant_ref` | TEXT NOT NULL | as in the trace |
| `input_hash` | TEXT NOT NULL | as in the trace |
| `rule_set_version` | TEXT NOT NULL | as in the trace |
| `rule_set_hash` | TEXT NOT NULL | as in the trace |
| `evaluated_at` | TEXT NOT NULL | UTC, whole seconds, `Z` suffix |
| `decision` | TEXT NOT NULL | `eligible`, `ineligible` or `refer` |
| `reason_codes` | TEXT NOT NULL | JSON array |
| `offer` | TEXT | JSON object or NULL |
| `trace` | TEXT NOT NULL | the full trace JSON, canonical form (section 3) |
| `notice` | TEXT NOT NULL | the notice JSON, canonical form |
| `system_flags` | TEXT NOT NULL | JSON object; `{}` normally. Keys allowed: `experimental_rules_on` (boolean) |
| `prev_hash` | TEXT NOT NULL | `record_hash` of the previous row; `sha256:` plus 64 zeros for row 1 |
| `record_hash` | TEXT NOT NULL | section 4 |

`decision_id` is the API layer's counter: it takes `seq` from the insert, so ids are gapless and never random. The id is therefore known only after the insert. Build the response, insert the row (which fixes `decision_id`), then set the `decision_id` field inside the stored trace in the same transaction before computing `record_hash` (compute the hash last). Implementation hint: reserve the next `seq` with `SELECT COALESCE(MAX(seq),0)+1` inside a `BEGIN IMMEDIATE` transaction.

`audit_inputs`: `input_hash` TEXT PRIMARY KEY, `input` TEXT NOT NULL (canonical JSON). `INSERT OR IGNORE`: the same input sent twice stores one row.

`reviewer_actions`: `action_id` INTEGER PRIMARY KEY AUTOINCREMENT, `decision_id` TEXT NOT NULL, `reviewer` TEXT NOT NULL, `action` TEXT NOT NULL (`approve`, `deny`, `override`), `reason` TEXT NOT NULL, `acted_at` TEXT NOT NULL, `effective_outcome` TEXT NOT NULL (`approved` or `denied`).

## 3. Canonical JSON

Used for every hash and every stored JSON column: UTF-8, keys sorted, separators `,` and `:` with no spaces, `ensure_ascii` false, no floats anywhere (the schemas forbid them; integers and strings only). One function in `src/audit/canonical.py`; nothing else serialises for hashing.

- `input_hash` = `"sha256:" + hex(SHA-256(canonical(input)))` over the validated input exactly as received after validation (a field sent as `null` stays `null`; a field not sent stays absent).
- `applicant_ref` = `"sha256:" + hex(SHA-256(UTF-8 bytes of applicant_id))`.

## 4. Hash chain (NFR-08)

`record_hash` = `"sha256:" + hex(SHA-256(prev_hash + "\n" + canonical(row without record_hash)))`, where the row is every other column of that row as a JSON object (the `trace`, `notice`, `offer`, `reason_codes` and `system_flags` columns parsed back to JSON first, so key order never matters).

`make audit-verify` recomputes the chain from row 1 and prints `OK <n> records` or the first `seq` where it breaks, and exits non-zero on a break. `GET /v1/health` reports `audit_chain_ok`. A break never stops the service from answering reads, but `POST /v1/decisions` refuses to append to a broken chain (`AUDIT_UNAVAILABLE`).

## 5. Append-only rule (FR-15)

- The application has no code path that updates or deletes a row in any of the three tables.
- SQLite triggers enforce it: `BEFORE UPDATE` and `BEFORE DELETE` on each table raise `ABORT` with the message `audit tables are append-only`. Created by the schema migration, tested by one test that tries both and expects the error.
- The hash chain is what detects a change made outside the application (for example by editing the file with another tool).
- The one allowed "change" to a decision's state is a new row in `reviewer_actions`; the audit record is never edited.

## 6. Write order and failure (fail closed)

1. Validate the request. On failure: return `422`. Write nothing.
2. Compute the decision with `decide(application, rule_set)`.
3. Build the trace and the notice.
4. Append `audit_inputs` and `audit_records` in one transaction.
5. Return the response only after the commit succeeds.

Any failure in step 4 returns `503 AUDIT_UNAVAILABLE` with `suggested_route: "refer"` and no `decision` field. A decision that was computed but not recorded is never returned. Failures in steps 2 and 3 return `500 SYSTEM_ERROR` the same way, and the exception is written to the application log with the `input_hash` and no applicant fields (NFR-07).

## 6a. What is and is not volatile

Replay and the "same input twice" test ignore exactly two fields: `decision_id` and `evaluated_at` (inside `trace`, and the same two at the top of the response). Nothing else may differ. In particular `rule_set_hash`, `steps`, `derived`, `reason_codes`, `offer` and the notice text must be identical.

## 7. Replay (FR-16)

Code placement: `src/audit/replay.py` holds the loading and comparison. It must not import `src/engine`, `src/explain` or `src/calc` (calls go downward only). The caller passes in one function, `rebuild(input, decision_id, evaluated_at) -> (result_fields, trace, notice)`, which `src/api` builds from `decide()` and the trace and notice builders. `make replay-all` and the replay endpoint both go through `src/api`.

`replay(decision_id)`:

1. Load the record and its input snapshot (by `input_hash`). If the snapshot is missing, return `match: false`, `note: "no input snapshot"`.
2. Load the rule set that the record names. The baseline is whatever is on disk now: compare the current `rule_set_hash` with `rule_set_hash` in the record. If they differ, still re-run with the current files, and report the difference (this is how "changing a rule file or parameter makes replay report a mismatch" is met). The prototype does not archive old rule sets; the git commit that produced the recorded hash is the way to reconstruct one, and `note` says so.
3. Call `decide(input, rule_set)` and rebuild the trace and notice with the recorded `decision_id` and `evaluated_at` copied in.
4. Compare `decision`, `reason_codes`, `offer` and the whole trace (after removing the two volatile fields). Report every differing JSON path in `differences` (`path` like `trace.steps[14].status`).
5. Rebuild the notice and set `notice_match`. If the notice differs and `notice_version` differs from the recorded one, that is not a failure: set `notice_match` false and `note: "notice wording version changed"`. If the notice differs under the same `notice_version`, `match` is false.

`make replay-all` replays every record and prints `replayed <n>, matched <n>, mismatched <n>`; it exits non-zero if any record mismatches.

## 8. Tests (lean mode)

Required for Phase 3: a record is written for every decision in a run over all of D1; an UPDATE and a DELETE are rejected; replay of one stored decision matches; changing one value in a copy of `params/params.toml` makes replay report a mismatch. A tamper test and `make audit-verify` are built but their tests are optional.
