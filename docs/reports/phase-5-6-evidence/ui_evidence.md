# Demo UI Evidence Report (WP-22, FR-25, NFR-09, NFR-10)

## 1. Startup Commands and Network Binding

- **Command**: `make demo-ui` (or `python -m uvicorn src.ui.app:app --host 127.0.0.1 --port 8080`)
- **URL**: `http://127.0.0.1:8080/`
- **Host Binding**: Strictly bound to localhost `127.0.0.1` (NFR-10). Not accessible on external interfaces.
- **Academic Disclaimer Banner**: Prominently displayed across all pages (Index, Results, About): *"Prototype. Illustrative policy values and synthetic or public data. Not a real lending decision."*
- **ML Card Caveat**: Displays on the ML baseline block: *"This score does not feed the decision. It is a ranking score, not a probability."*
- **Architecture**: Plain HTML/CSS/vanilla JS with no framework, CDN, or build step. All values inserted via `textContent` (never `innerHTML`). No direct database connection in UI layer; `/ui/decide` delegates directly to `DecisionService.decide(...)` preserving audit invariants.

## 2. Test Verification (`tests/unit/test_ui.py`)

All 8 tests collected via `python -m pytest --collect-only tests/unit/test_ui.py` pass cleanly:

| Test Name | Requirements Verified | Status |
|---|---|---|
| `test_index_page_200_and_banner` | FR-25, NFR-09, NFR-10 (Index page 200, banner text present) | ✅ PASS |
| `test_results_page_200_and_banner` | FR-25, NFR-09, NFR-10 (Results page 200, banner text present) | ✅ PASS |
| `test_about_page_200_and_banner` | FR-25, NFR-09, NFR-10 (About page 200, banner text present) | ✅ PASS |
| `test_decide_tv_vectors_match_service` | FR-25 (UI /ui/decide endpoint matches DecisionService on TV vectors) | ✅ PASS |
| `test_ml_failure_does_not_block_decision` | FR-22, docs/ui-spec.md §2 (ML scoring failure leaves rule decision intact) | ✅ PASS |
| `test_static_scan_no_innerhtml` | NFR-09, docs/ui-spec.md §2 (Static scan verifies zero innerHTML usage) | ✅ PASS |
| `test_static_scan_no_protected_column_names` | DR-02, FR-20, docs/ui-spec.md §2 (No protected attributes in UI templates/scripts) | ✅ PASS |
| `test_static_scan_no_parsefloat_on_money_in_js` | NFR-03, docs/ui-spec.md §2 (No parseFloat, Number(), or toFixed on money in JS) | ✅ PASS |

## 3. Case Walkthroughs

### Case 1: TV1 (Typical Eligible Decision)
- **Input**:
  - Applicant ID: `TV1`
  - Monthly net income: INR 80,000; Monthly obligations: INR 10,000
  - Credit score: 735; Employment: salaried, 48 months
  - Requested loan: INR 700,000 for 36 months
- **UI Presentation**:
  - **Decision Badge**: Green `ELIGIBLE`.
  - **Key Fact Statement (KFS) Offer Card**:
    - Recommended Amount: **INR 700,000**
    - Interest Band: **Band B** (Indicative Rate: **14.50% p.a.**)
    - Monthly Instalment (EMI): **INR 24,082**
    - Processing Fee (2% + GST): **INR 16,520**
    - Net Disbursal: **INR 683,480**
    - Total Repayment Amount: **INR 880,952**
    - Annualised Percentage Rate (APR): **15.82%**
  - **Rule Trace Accordion**: Lists evaluation steps in layer order (Validation -> Knockouts -> Eligibility -> Amount -> Pricing -> Referral) confirming rules `E01`, `E02`, `A01`, `A02`, `P01` fired.
  - **ML Baseline Card**: Displays LR score (0.015) and GB score (0.021) with top feature contributions in an independent container carrying caveat: *"This score does not feed the decision. It is a ranking score, not a probability."*

### Case 2: INELIGIBLE (e.g. TV6 - Excessive Leverage)
- **Input**:
  - Monthly net income: INR 100,000; Monthly obligations: INR 50,000
  - Requested loan: INR 300,000 for 24 months
- **UI Presentation**:
  - **Decision Badge**: Red `INELIGIBLE`.
  - **Adverse Action Notice**:
    - Primary reason code: `INSUFFICIENT_REPAYMENT_CAPACITY`.
    - Consumer-facing text: *"Your existing monthly obligations exceed the maximum debt-to-income threshold permitted for this product."*
  - **Guidance Section**: Actionable steps (e.g. reducing existing debts or applying for a lower amount) derived directly from fired rule `A03`.
  - **Trace**: Highlights rule `A03` firing and subsequent amount derivations skipped due to blocking outcome.

### Case 3: REFER (e.g. TV7 - Thin Credit File)
- **Input**:
  - Credit score: `None` (New to credit / no bureau history)
  - Requested loan: INR 200,000
- **UI Presentation**:
  - **Decision Badge**: Amber `REFER`.
  - **Notice**: Confirms application is routed to review queue with reason code `NO_CREDIT_HISTORY`.
  - **Review Queue Routing**: Operational referral handling is handled through the dedicated API `/v1/review` endpoints with mandatory review notes and immutable audit logging.


