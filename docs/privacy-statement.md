# Privacy Statement (v0.1)

Requirements: NFR-07, CR-03, DR-02, DR-03. Plain statement of what the prototype collects, why, where it is kept and who can read it. It is an academic prototype: it is not a lending product and is not for use with real people.

## 1. Scope

The system processes loan applications on **synthetic or public, anonymised data only**. No real applicant data is collected, entered or stored. Do not enter real personal data into the API, the demo or the reviewer reports. The copy of any public dataset stays outside the repository (`data/raw/` is never committed).

## 2. What is collected and why (data minimisation, CR-03)

Only the 14 input fields in `docs/data-dictionary.md` section 2. Each one is read by a named rule or check; a field that no rule reads is not collected. The consent flag (`consent_given`) is itself an input: with no recorded consent the application is not processed (rule V02).

Not collected: name, address, phone, e-mail, national ID, date of birth, or any free-text field. Age is collected as a whole number, used only for the legal-capacity check (K01).

## 3. Protected attributes

Gender, religion, caste and similar attributes are not accepted by the API (the input schema rejects unknown fields), are never read by a rule, the fact builder or a model, and never appear in the trace, the notice, the audit log or a log line. For the fairness review they are held in a separate store, keyed by a hash of the applicant ID, read only by the evaluation package (DR-02).

## 4. Where data lives

| Data | Where | Who reads it |
|---|---|---|
| The decision, trace, reason codes, notice | `audit_records` (SQLite) | reviewer view, replay, evaluation |
| The validated input | `audit_inputs`, a separate table | replay only |
| Reviewer actions and reasons | `reviewer_actions` | reviewer view, evaluation |
| Application logs | local log output | the developer; logs hold decision IDs and input hashes, never input fields |

The trace contains the values of the facts each rule read, because the explanation and the audit need them. That is why this log is for synthetic data only.

## 5. Retention and deletion

Records are kept for the life of the project. The application has no way to edit or delete a record (the log is append-only, `docs/audit-log-spec.md`). The project owner can remove everything by deleting the `data/audit/` folder.

## 6. Applicant-facing statements

The notice explains each reason in plain language and says what could change the outcome where that can be worked out. A REFER decision tells the applicant that a person will review the application. The applicant text never reveals protected attributes, other applicants' data, or the internal rule IDs.

## 7. Legal references

This prototype is designed with the Indian Digital Personal Data Protection Act, 2023 and the RBI digital lending framework in mind (purpose limitation, minimisation, consent). The exact wording of any legal obligation must be checked against the current official text before it is cited in the final report (SRS section 5).

## 8. Contact and changes

The project owner keeps this file. A change to what is collected, stored or logged needs an update here in the same commit.
