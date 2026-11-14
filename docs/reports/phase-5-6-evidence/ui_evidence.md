# Demo UI Evidence Report (WP-22, FR-25, NFR-09, NFR-10)

## 1. Startup Commands and Network Binding

- **Command**: `make demo-ui` (or `python -m uvicorn src.ui.app:app --host 127.0.0.1 --port 8080`)
- **URL**: `http://127.0.0.1:8080/`
- **Host Binding**: Strictly bound to localhost `127.0.0.1` (NFR-10). Not accessible on external interfaces.
- **Academic Disclaimer Banner**: Prominently displayed across all pages: *"Academic prototype only. Unsecured personal loan eligibility system in INR. Not for production lending."*

## 2. Test Verification (`tests/unit/test_ui.py`)

All 8 tests pass cleanly:

| Test Name | Requirements Verified | Status |
|---|---|---|
| `test_index_page_200_and_banner` | FR-25, NFR-09, NFR-10 (Banner, Accessibility, 127.0.0.1) | ✅ PASS |
| `test_decide_endpoint_returns_trace_without_ml` | FR-22, FR-25 (Decision independent of ML) | ✅ PASS |
| `test_ml_score_endpoint_separate` | FR-22, docs/ui-spec.md §4 (Separate /ui/ml-score call) | ✅ PASS |
| `test_ml_failure_leaves_decision_intact` | FR-22, docs/ui-spec.md §4 (ML error never blocks decision) | ✅ PASS |
| `test_reviewer_view_smoke` | FR-13, FR-14, CR-04 (Reviewer queue dashboard) | ✅ PASS |
| `test_golden_vectors_ui_vs_service_parity` | Golden Vectors TV1–TV9 match DecisionService directly | ✅ PASS |
| `test_static_scan_no_protected_attributes_in_ui` | DR-02, FR-20 (No protected column names in UI source) | ✅ PASS |
| `test_static_scan_no_parsefloat_on_money_in_js` | NFR-03 (No parseFloat, Number(, or toFixed on money) | ✅ PASS |

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
  - **ML Baseline Card**: Displays LR probability (0.015) and GB probability (0.021) in an independent grey container with disclaimer: *"Model outputs are non-decisional baselines for evaluation only."*

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
  - **Review Queue Routing**: Notice states *"Application routed to Underwriter Review Queue with reason NO_CREDIT_HISTORY."*
  - **Action Button**: *"Open in Reviewer Dashboard"*.

### Page 2: Underwriter Review Dashboard (`/ui/reviewer`)
- **Queue Table**: Lists pending referred applications with application ID, timestamp, and referral reason codes.
- **Review Form**:
  - Underwriter action selector: `Approve`, `Deny`, `Override`.
  - Reason input field: Mandatory text area enforced with minimum 10 characters.
  - Audit commitment: Each action writes an immutable record to `reviewer_actions` table.

