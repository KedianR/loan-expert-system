# Demo UI Specification (v1.0, WP-22)

Requirements: FR-25 (ML score beside the trace), NFR-09, NFR-10, CR-02. Decision P5-12 (docs/fairness-audit-plan.md section 2).

## 1. Goal and the cheap option

A person with no technical background can try the system in a browser: enter or pick an application, see the decision, the reasons, the offer summary and the trace, and see the ML baseline score beside it. A second page shows the project's results.

The cheap option that works: **one small web app in `src/ui/` plus plain static files**. No JavaScript framework, no build step, no CDN, no new dependency beyond what the API already uses (FastAPI and uvicorn). It runs offline. It does **not** touch `src/api`, `src/engine`, `src/calc`, `src/explain` or `src/audit`; it imports the service function the API calls.

## 2. Hard rules (Stop and ask if you cannot meet one)

1. The UI never computes a decision, an amount, a rate or any money figure. It shows what the service returns, as strings, unchanged. No `parseFloat`, `Number()` or `toFixed` on a money field.
2. The ML score never feeds the decision. The service is called first and alone; the ML endpoint is a separate call. If the ML call fails, the decision still shows and the ML block says "Not available".
3. The form has the input-schema fields only. No protected attribute is collected, shown, stored or read. Nothing under `src/ui/` mentions a protected column name or the protected file paths.
4. Every API string is inserted with `textContent`, never `innerHTML`. A test scans for `innerHTML`.
5. A banner on every page: "Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."
6. The ML block carries the line "This score does not feed the decision. It is a ranking score, not a probability."
7. If the service writes an audit record, use the same mechanism and location the API uses; say in the report which. Do not edit the audit code to move it.

## 3. Pages

| Page | Content |
|---|---|
| `/` Try an application | A preset menu (TV1 to TV9 from the golden vectors, loaded from the file the tests use; read-only) and a form of the input fields with the schema's types and limits. Submit shows: decision (large, with the words ELIGIBLE, INELIGIBLE or REFER), recommended amount and band, the KFS-style offer summary for ELIGIBLE, the applicant-facing reasons in the notice's own words with their codes, a collapsible rule trace (rule ID, version, facts used, result), and the ML block (score, the top three contributions of the logistic regression, the caveat line). Field-level errors from the service are shown against the fields |
| `/results` Project results | Read-only tabs that render files if they exist, otherwise "Not generated yet; run `make phase5`": ML metrics (`reports/ml/`), the comparison scorecard (`reports/comparison/scorecard.json`), the fairness tables (`reports/fairness/*.json`, group sizes first, "too small" and "unstable" visible), the edge-case summary. Each tab starts with its limits text from the report |
| `/about` | One screen: what the system is, the three possible decisions, that policy values are illustrative, where the documents are |

Layout: one column, readable at laptop and phone width, system font, high contrast, labels tied to inputs, keyboard usable, decision not conveyed by color alone.

## 4. Files and commands

- `src/ui/app.py` (FastAPI app): `GET /`, `GET /results`, `GET /about`, `POST /ui/decide` (calls the service function, returns its result unchanged), `POST /ui/ml-score` (feature builder, `models/d3_lr.joblib`, the Phase 4 contribution function), `GET /ui/presets`, `GET /ui/report/{name}` (allow-list of report files, no path from the user).
- `src/ui/static/` (`index.html`, `results.html`, `about.html`, `app.js`, `style.css`). Keep `app.js` under about 300 lines.
- `make demo-ui` starts the app on localhost (print the URL). It does not open a firewall port and binds to 127.0.0.1.
- If the models do not exist the ML block says "Not available; run `make baseline`".
- If the service function cannot be imported without changing `src/api`, STOP and ask. The fallback is to call the running API over HTTP from `src/ui/app.py`; ask before using it.

## 5. Tests (lean: these four, no more)

1. `GET /`, `/results` and `/about` return 200 and the banner text.
2. For TV1 to TV9, `POST /ui/decide` returns the same decision, amount, band and reason codes as the service function called directly.
3. With the ML scorer monkeypatched to raise, `POST /ui/decide` still returns the decision (ML never feeds or blocks the decision).
4. Static scan: no `innerHTML`, no protected column name, no `parseFloat` or `Number(` applied to money in `src/ui/`.

## 6. Demo check for the report

Start `make demo-ui`, open the pages with the built-in checks only (the four tests). Include in the report: the command, the URL, the four test results, and a text description of what each page shows for TV1 and for one INELIGIBLE and one REFER case. If a screenshot tool is available, attach one screenshot per page; if not, say so.

## 7. Not in scope

Authentication, a database, editing rules in the UI, charts, the reviewer queue (the existing reviewer page stays as is; link to it if a make target produces it), Windows service packaging.
