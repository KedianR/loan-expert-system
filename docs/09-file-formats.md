# Rule File and Parameter File Format Specification (v0.1)

Nov 7, 2026 · @Kulvinder

## 1. Scope and design decisions

This specification fixes how policy parameters, rules, reason codes and field definitions are stored in files and loaded, so the coding agent never has to invent a format. It follows the Credit Policy and Rule Catalog (section 5, rule file requirements), the Predicate and Fact Schema, and ADR-001. Where this document and those disagree, I list the point below and fix the other document.

**The file set.** Eleven files in two folders. The parameter file is needed first, in Phase 0.

| Path | Content | Needed by |
| --- | --- | --- |
| `params/params.toml` | Thresholds, pricing bands and experimental switches | Phase 0 |
| `rules/fields.toml` | Registry of input and derived fields with types and ranges | Phase 1 |
| `rules/reason_codes.toml` | Reason codes and applicant-facing text templates | Phase 2 |
| `rules/manifest.toml` | Layer order, file list and the rules version | Phase 2 |
| `rules/validation.toml`, `knockout.toml`, `referral.toml`, `eligibility.toml`, `amount.toml`, `pricing.toml`, `experimental.toml` | The rules, one file per layer | Phase 2 |

**Design decisions.** I made these choices; change any of them before the phase that needs it.

| ID | Decision | Why |
| --- | --- | --- |
| DS-1 | All eleven files are TOML. Integers are native; every ratio, rate and other decimal is a quoted string such as `"0.50"`. A TOML float anywhere is an error. | Python 3.11 and later reads TOML with no extra package, comments are allowed, and no money or ratio can pass through a binary float. |
| DS-2 | Rules are declarative entries with a condition written in a small condition language (section 4). The loader generates the Prolog clauses and the first-order formulas from them. Rules are not hand-written Prolog. | The same files then feed the pure-Python fallback in ADR-001. The hygiene checks (completeness, contradiction, redundancy) need conditions as data. No threshold can hide in rule text. The cost is a parser and a generator in Phase 2. |
| DS-3 | Rule IDs and band IDs keep the catalog's case (`K04`, `A`). The generated Prolog lowercases them to atoms. | Traces and notices then show the catalog's names. |

DS-1 is the only one Phase 0 depends on. If you would prefer hand-written Prolog (DS-2), tell me before Phase 2; Phases 0 and 1 are not affected.

**Points I found in the earlier documents while writing this.**

1. The TV2 trace example in the Predicate and Fact Schema numbers its steps 1, 5, 12 and so on. With 20 active rules in layer order the numbers are V01 1, K04 8, E01 14, E02 15, A01 16, A02 17, A03 18, A04 19, P01 20. I have corrected that document.
2. Four reason-code templates use names that are not field names: `{income}`, `{requested_tenure}`, `{min_months}` and `{existing_foir_pct}`. Section 3 defines display fields for them.
3. The reason-code texts write parameter values into the sentence (50,000, 650, 15,000, 5, 10, 25,00,000). A parameter change would leave the text wrong, so section 3 uses placeholders.
4. Formula F1 divides by monthly net income, which the fact schema allows to be 0. I have assumed the fact builder then records `existing_foir` as unknown. The Lending Calculations Specification instead says zero income returns REFER through V01. Rule K05 fires INELIGIBLE for zero income, and INELIGIBLE wins, so the decision is the same, but the trace differs. I keep my assumption and add no V01, and I have aligned the edge-case line in that specification.
5. The catalog gives X01 and X02 no position in the layer order. Section 4 proposes one; both rules are disabled in the baseline.

6) The catalog says A04 fires when the recommended amount is below the requested amount. The Lending Calculations Specification (edge cases) says a reduced offer is reported only when the result is below the request by at least one step, because a request that is not a multiple of 5,000 is floored. The rule file follows the calculation specification: no\_blocking\_outcome and `recommended_amount + amount_step <= requested_amount`. The first condition stops an A03 rejection from also producing a reduced-offer reason (without it, TV6 and TV8 would report two reason codes). Without the second, a request of 777,777 would fire A04 with no reason code that fits. I have aligned the catalog row.

## 2. Parameter file: params/params.toml

The parameter file holds every number the policy uses, in one place, and nothing else holds one. Rules refer to a parameter by name (`min_credit_score`), never by value. Parameter names are unique across the whole file; the section headings only group them for the reader.

**Conventions**

- Money is a whole-rupee integer. Tenures, ages, counts and scores are integers.
- A ratio is a decimal fraction in a quoted string: `"0.50"` means 50%.
- A rate is a percentage per year in a quoted string: `"12.0"` means 12.0%.
- A decimal string is digits, an optional point and more digits: no sign, no exponent, no spaces, a digit before the point (`"0.5"` yes; `".5"`, `"5e-1"`, `"0,5"` and `"+0.5"` no).
- The loader returns integers as `int`, decimals as exact `Decimal`, and booleans as `bool`. It never returns a float.

**Scalar parameters**

| Name | Type | Unit | Valid range | Catalog ref | Read by |
| --- | --- | --- | --- | --- | --- |
| `min_amount` | int | INR | 1 or more | CP-1.1 | V03, A03 |
| `max_amount` | int | INR | at least `min_amount` | CP-1.1 | V03, A02 |
| `amount_step` | int | INR | 1 or more | CP-1.2 | A02 |
| `min_tenure_months` | int | months | 1 or more | CP-1.3 | V04 |
| `max_tenure_months` | int | months | at least `min_tenure_months` | CP-1.3 | V04 |
| `processing_fee_rate` | decimal | fraction | above 0, at most 1 | CP-6.1 | P01 |
| `income_multiple_cap` | int | times monthly income | 1 or more | CP-3.1 | A02 |
| `min_age` | int | years | 1 to 120 | CP-2.1 | K01 |
| `min_monthly_income` | int | INR | 0 or more | CP-2.2 | K05 |
| `min_credit_score` | int | points | 300 to 900 | CP-2.3 | K04 |
| `min_employment_months_salaried` | int | months | 0 to 600 | CP-2.4 | K06 |
| `min_employment_months_self_employed` | int | months | 0 to 600 | CP-2.4 | K06 |
| `max_existing_foir` | decimal | fraction | above 0, at most 1 | CP-3.2 | E01 |
| `max_enquiries_6m` | int | count | 0 or more | CP-5.1 | R02 |
| `x01_enabled` | bool | switch | true or false | experimental | X01 |
| `x02_enabled` | bool | switch | true or false | experimental | X02 |
| `max_age_at_maturity` | int | years | 18 to 120 | experimental | X01 |
| `high_risk_region_tier` | int | tier | 1 to 3 | experimental | X02 |

The `meta` section also carries `schema_version` (an integer, 1 for this specification), `params_version` (a semantic version string), `currency` (`"INR"`) and `description`.

**Pricing bands.** Each `[[band]]` entry is one row of the catalog's band table. The order in the file is the order the bands are tried, best first, and the first match wins.

| Key | Type | Unit | Valid range |
| --- | --- | --- | --- |
| `id` | string |  | one uppercase letter, unique |
| `min_score` | int | points | 300 to 900 |
| `max_foir` | decimal | fraction | above 0, at most 1 |
| `rate_low`, `rate_high` | decimal | percent a year | above 0, at most 100, `rate_low` at most `rate_high` |
| `indicative_rate` | decimal | percent a year | the exact midpoint of `rate_low` and `rate_high` |
| `post_loan_foir_cap` | decimal | fraction | above 0, at most 1 |

**The file as it should stand for the baseline policy**

```toml
[meta]
schema_version = 1
params_version = "0.1.0"
currency = "INR"
description = "Illustrative personal loan policy, Credit Policy and Rule Catalog v0.1"

[product]
min_amount = 50000
max_amount = 2500000
amount_step = 5000
min_tenure_months = 12
max_tenure_months = 60
processing_fee_rate = "0.02"
income_multiple_cap = 10

[eligibility]
min_age = 18
min_monthly_income = 15000
min_credit_score = 650
min_employment_months_salaried = 6
min_employment_months_self_employed = 24
max_existing_foir = "0.50"
max_enquiries_6m = 5

[experimental]
x01_enabled = false
x02_enabled = false
max_age_at_maturity = 65
high_risk_region_tier = 3

[[band]]
id = "A"
min_score = 750
max_foir = "0.30"
rate_low = "11.0"
rate_high = "13.0"
indicative_rate = "12.0"
post_loan_foir_cap = "0.55"

[[band]]
id = "B"
min_score = 700
max_foir = "0.40"
rate_low = "13.0"
rate_high = "16.0"
indicative_rate = "14.5"
post_loan_foir_cap = "0.50"

[[band]]
id = "C"
min_score = 650
max_foir = "0.50"
rate_low = "16.0"
rate_high = "20.0"
indicative_rate = "18.0"
post_loan_foir_cap = "0.45"
```

**Checks the parameter loader makes.** A failure of an error check stops the load; a warning is printed and does not.

| Check | Severity | What it catches |
| --- | --- | --- |
| Every parameter above is present and no other parameter exists | Error | A missing threshold or a misspelt name |
| Names are unique across all sections | Error | The same name in two sections |
| Types are exact: integers are native integers, decimals match the pattern, booleans are booleans | Error | `min_age = true`, `"0,5"`, `"1e-1"` |
| No TOML float anywhere | Error | `max_existing_foir = 0.5` |
| Each value is inside its valid range | Error | A score of 1000 |
| `min_amount` is at most `max_amount`; both are multiples of `amount_step` | Error | An amount the step could never reach |
| Tenure minimum is at most the maximum | Error | Reversed limits |
| Bands are ordered best first: `min_score` never rises and `max_foir` never falls from one band to the next | Error | A band that can never be reached |
| Coverage: the last band has `min_score` at most `min_credit_score` and `max_foir` at least `max_existing_foir` | Error | An applicant who clears K04 and E01 yet gets no band |
| `indicative_rate` is the exact midpoint of its range | Error | A rate that disagrees with the catalog rule for P01 |
| `indicative_rate` rises and `post_loan_foir_cap` falls from one band to the next | Warning | A pricing order that looks wrong |

If a lender later chooses to draw a point rate inside the band instead of the midpoint (an open item in the catalog), the midpoint check is the one to change, and only after I update the catalog.

## 3. Field registry and reason code file

The registry tells the loader which names a rule condition may use and what type each has; the reason code file holds every applicant-facing text. Both are data, so the loader can check rules and texts against them.

### Field registry: rules/fields.toml

Each `[[field]]` entry has these keys: `name`, `kind` (`input` or `derived`), `type` (`int`, `decimal`, `bool`, `enum` or `string`), `unit` (`INR`, `fraction`, `percent`, `years`, `months`, `count`, `points` or empty), `min` and `max` where they apply, `values` for an enum, `required`, `nullable`, `predicate` (the Prolog name from the Predicate and Fact Schema), `produced_by` for a derived field, and `readable_from` (the first layer a rule may read it in, or `never`).

```toml
[[field]]
name = "credit_score"
kind = "input"
type = "int"
unit = "points"
min = 300
max = 900
required = false
nullable = true
predicate = "credit_score"
readable_from = "validation"

[[field]]
name = "recommended_amount"
kind = "derived"
type = "int"
unit = "INR"
produced_by = "A02"
predicate = "recommended_amount"
readable_from = "amount"
```

**The registry content**

| Name | Kind | Type and range | Unit | Required | Nullable | Produced by | Readable from |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `applicant_id` | input | string, unique |  | yes | no |  | never |
| `age` | input | int 0 to 120 | years | yes | no |  | validation |
| `employment_type` | input | enum `salaried`, `self_employed`, `other` |  | yes | no |  | validation |
| `employment_months` | input | int 0 to 600 | months | yes | no |  | validation |
| `monthly_net_income` | input | int 0 or more | INR | yes | no |  | validation |
| `monthly_obligations` | input | int 0 or more | INR | yes | no |  | validation |
| `credit_score` | input | int 300 to 900 | points | no | yes |  | validation |
| `enquiries_6m` | input | int 0 or more | count | yes | no |  | validation |
| `severe_delinquency_36m` | input | bool |  | yes | no |  | validation |
| `written_off` | input | bool |  | yes | no |  | validation |
| `kyc_verified` | input | bool |  | yes | no |  | validation |
| `consent_given` | input | bool |  | yes | no |  | validation |
| `requested_amount` | input | int 1 or more | INR | yes | no |  | validation |
| `requested_tenure_months` | input | int 1 or more | months | yes | no |  | validation |
| `region_tier` | input | int 1 to 3 |  | no | yes |  | experimental |
| `existing_foir` | derived | decimal, 4 places | fraction |  |  | fact builder, F1 | validation |
| `band` | derived | enum `A`, `B`, `C` |  |  |  | E02 | amount |
| `max_emi` | derived | decimal | INR |  |  | A01, F4 | amount |
| `max_principal_emi` | derived | decimal | INR |  |  | A01, F5 | amount |
| `recommended_amount` | derived | int | INR |  |  | A02, F6 | amount |
| `binding_limit` | derived | enum `requested`, `capacity`, `income_multiple`, `product_maximum` |  |  |  | A02, F6 | amount |
| `indicative_rate` | derived | decimal | percent |  |  | P01 | pricing |
| `fee` | derived | decimal | INR |  |  | P01, F7 | pricing |
| `emi` | derived | decimal | INR |  |  | offer builder, F3 | never |
| `post_loan_foir` | derived | decimal | fraction |  |  | offer builder, F8 | never |
| `apr` | derived | decimal | percent |  |  | offer builder, F9 | never |
| `age_at_maturity` | derived | decimal, years | years |  |  | fact builder, experimental | experimental |

Notes on the table:

- The input field `requested_tenure_months` becomes the predicate `requested_tenure`, as in the fact schema. Rule conditions use the field name; the generated Prolog uses the predicate name.
- A derived field is unknown when an input it needs is unknown, or when its formula is undefined (assumed for `existing_foir` at zero income; see section 1, point 4). A rule that reads an unknown derived field is not evaluated.
- `emi`, `post_loan_foir` and `apr` are outputs. They belong in the trace but no rule may read them.
- The definition of `age_at_maturity` is not fixed yet. I will add it to the Lending Calculations Specification before X01 is enabled in Phase 5. Until then X01 stays disabled.
- The `fields.toml` file and the input JSON Schema in `schemas/` describe the same input fields. A test compares them and fails if they differ.

### Reason code file: rules/reason\_codes.toml

Each `[[code]]` entry has `code`, `rule` (the rule that raises it, or `default`), `text` (the applicant-facing template), and optionally `allow_literals`, a list of numbers allowed to appear in the text as written.

```toml
[[code]]
code = "CREDIT_SCORE_BELOW_MINIMUM"
rule = "K04"
text = "Your credit score ({credit_score}) is below our minimum of {param.min_credit_score}."
```

**Placeholders.** A text may use only these, so that every value comes from the recorded trace and none from a second calculation:

- `{field}`: an input or derived field the rule reads, or a derived value recorded in the trace
- `{param.name}`: a parameter, for example `{param.min_amount}`
- `{name_pct}`: any fraction-valued name multiplied by 100 and printed exactly, for example `{existing_foir_pct}` or `{param.max_existing_foir_pct}`; `existing_foir` is held to four decimal places, so two places are exact
- `{missing_fields}`: the unknown required fields, comma separated, in registry order
- `{min_months}`: the employment minimum for the applicant's type, from `min_employment_months_salaried` or `min_employment_months_self_employed`

Amounts in rupees (unit `INR`) are printed with Indian digit grouping and no symbol, for example 50,000 and 25,00,000. Other numbers are printed plainly.

**The 21 reason codes.** The first column is the code, then the rule that raises it, then the text with the corrections from section 1, points 2 and 3.

| Code | Rule | Text |
| --- | --- | --- |
| `INCOMPLETE_APPLICATION` | V01 | We could not decide because these details are missing: {missing\_fields}. |
| `CONSENT_NOT_GIVEN` | V02 | We cannot process your application without your recorded consent to use your data. |
| `AMOUNT_OUTSIDE_PRODUCT_LIMITS` | V03 | The amount requested ({requested\_amount}) is outside our limits of {param.min\_amount} to {param.max\_amount}. |
| `TENURE_OUTSIDE_PRODUCT_LIMITS` | V04 | The tenure requested ({requested\_tenure\_months} months) is outside our range of {param.min\_tenure\_months} to {param.max\_tenure\_months} months. |
| `LEGAL_CAPACITY_NOT_MET` | K01 | Applicants must be at least {param.min\_age} years old. |
| `KYC_NOT_VERIFIED` | K02 | Your identity verification is not complete. |
| `ADVERSE_REPAYMENT_HISTORY` | K03 | Your credit record shows a payment 90 or more days overdue in the last 36 months, or a written-off account. |
| `CREDIT_SCORE_BELOW_MINIMUM` | K04 | Your credit score ({credit\_score}) is below our minimum of {param.min\_credit\_score}. |
| `INCOME_BELOW_MINIMUM` | K05 | Your monthly net income ({monthly\_net\_income}) is below our minimum of {param.min\_monthly\_income}. |
| `EMPLOYMENT_TENURE_TOO_SHORT` | K06 | Your time in current employment ({employment\_months} months) is below our minimum of {min\_months} months for your employment type. |
| `NO_CREDIT_HISTORY` | R01 | We found no credit score for you, so a reviewer will assess your application. |
| `HIGH_RECENT_ENQUIRIES` | R02 | You have {enquiries\_6m} credit enquiries in the last 6 months, above our limit of {param.max\_enquiries\_6m}, so a reviewer will assess your application. |
| `EMPLOYMENT_TYPE_REQUIRES_REVIEW` | R03 | Your employment type needs a reviewer's assessment. |
| `HIGH_EXISTING_OBLIGATIONS` | E01 | Your existing monthly loan payments are {existing\_foir\_pct}% of your income, above our limit of {param.max\_existing\_foir\_pct}%. |
| `INSUFFICIENT_REPAYMENT_CAPACITY` | A03 | Based on your income and existing payments, the most we can offer is {recommended\_amount}, below our minimum loan of {param.min\_amount}. |
| `AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY` | A04 | We can offer {recommended\_amount} instead of {requested\_amount} because your income and existing payments limit the monthly instalment you can afford. |
| `AMOUNT_LIMITED_BY_INCOME_MULTIPLE` | A04 | We can offer {recommended\_amount} instead of {requested\_amount} because our limit is {param.income\_multiple\_cap} times your monthly income. |
| `AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM` | A04 | We can offer {recommended\_amount} instead of {requested\_amount} because {param.max\_amount} is the maximum for this loan. |
| `AGE_AT_MATURITY_LIMIT` | X01 | Experimental rule X01 only. Text to be drafted if the rule is ever enabled in a real notice. |
| `REGIONAL_RISK_ADJUSTMENT` | X02 | Experimental rule X02 only. Text to be drafted if the rule is ever enabled in a real notice. |
| `NO_RULE_APPLICABLE` | default | A reviewer will assess your application. |

The `HIGH_RECENT_ENQUIRIES` text contains the 6 of "6 months", which equals a parameter value by coincidence (the field is `enquiries_6m`, so the 6 is part of the fact's definition); its entry therefore carries `allow_literals = ["6"]`. The 90 and 36 in `ADVERSE_REPAYMENT_HISTORY` define the fact `severe_delinquency_36m` and match no parameter.

## 4. Rule files and the condition language

There is one rule file per layer, and each file starts with its layer name. The rules inside are `[[rule]]` entries. The layers run in the order the manifest lists them: validation, knockout, referral, eligibility, amount, pricing, experimental. Within a layer, rules run in ID order.

```toml
layer = "knockout"

[[rule]]
id = "K04"
layer = "knockout"
description = "Credit score is known and below the minimum"
clause = "CP-2.3"
when = "credit_score < min_credit_score"
outcome = "ineligible"
reason_code = "CREDIT_SCORE_BELOW_MINIMUM"
owner = "credit-policy"
effective_date = "2026-11-05"
version = "0.1.0"
status = "active"
```

**Keys of a rule entry**

| Key | Needed for | Meaning |
| --- | --- | --- |
| `id` | every rule | One layer letter and two digits (V, K, R, E, A, P or X), matching the file's layer. IDs are permanent; a retired ID is never reused. |
| `layer` | every rule | Must equal the file's `layer`. |
| `description` | every rule | The rule in plain words, readable by someone who has not seen the code. |
| `clause` | every rule | The catalog clause or clauses that justify it. |
| `when` | every rule | The condition, in the language below. |
| `outcome` | every rule | `ineligible`, `refer`, `derive` or `reduced_offer`. |
| `reason_code` | `ineligible`, `refer`, `reduced_offer` | A code from `reason_codes.toml`, or a table that picks one by a derived enum (below). Not allowed for `derive`. |
| `calc` | `derive` | The calculations the rule runs, by ID: F1 to F9 from the Lending Calculations Specification, plus `band_lookup` and `rate_lookup` for the band table. |
| `computes` | `derive` | The derived fields the rule produces. They must match what the calculations return and what the registry says each field's `produced_by` is. |
| `after` | experimental rules | The rule after which it runs when switched on. |
| `owner` | every rule | A non-empty string naming the accountable person or role. |
| `effective_date` | every rule | An ISO date. |
| `version` | every rule | A semantic version for this entry. |
| `status` | every rule | `active`, `disabled` or `retired`. |

A `disabled` or `retired` rule is read and checked for structure, ID, layer and reason code, but it is never run, and its calculations and derived-field reads are not resolved. A rule in the experimental layer must be `disabled` or `retired`; it runs only when its parameter switch (`x01_enabled` for X01, `x02_enabled` for X02) is true, and the switch is part of the rule-set version.

A reason code that depends on which limit applied is written as a table, and the table must name a code for every value of that enum the rule can meet:

```toml
[[rule]]
id = "A04"
layer = "amount"
description = "The recommended amount is at least one step below the requested amount"
clause = "CP-3.1, CP-4, CP-1.1"
when = "no_blocking_outcome and recommended_amount + amount_step <= requested_amount"
outcome = "reduced_offer"
reason_code = { by = "binding_limit", capacity = "AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY", income_multiple = "AMOUNT_LIMITED_BY_INCOME_MULTIPLE", product_maximum = "AMOUNT_LIMITED_BY_PRODUCT_MAXIMUM" }
owner = "credit-policy"
effective_date = "2026-11-05"
version = "0.1.0"
status = "active"
```

A derivation rule names its calculations instead of a reason code:

```toml
[[rule]]
id = "A02"
layer = "amount"
description = "Recommended amount is the lowest of the requested amount, the EMI-based maximum, the income multiple cap and the product maximum, rounded down to the amount step"
clause = "CP-1.1, CP-1.2, CP-3.1"
when = "no_blocking_outcome"
outcome = "derive"
calc = ["F6"]
computes = ["recommended_amount", "binding_limit"]
owner = "credit-policy"
effective_date = "2026-11-05"
version = "0.1.0"
status = "active"
```

The `src/calc` module keeps a registry of calculations. Each entry lists the fields and parameters it reads and the derived fields it returns, so the loader can check `calc` and `computes` and the layer order without running anything.

### The condition language

A condition is a short expression. It has no numbers in it: every threshold is a parameter name, so a number can never hide in rule text. The loader rejects any numeric literal with `MAGIC_NUMBER`.

```text
condition  = or_expr
or_expr    = and_expr { "or" and_expr }
and_expr   = not_expr { "and" not_expr }
not_expr   = "not" not_expr | "(" condition ")" | builtin | comparison
comparison = value [ compare_op value ]
compare_op = "<" | "<=" | ">" | ">=" | "==" | "!="
value      = operand { ("+" | "-") operand }
operand    = name | enum_value | "true" | "false"
builtin    = "known(" name ")" | "unknown(" name ")" | "any_required_unknown" | "no_blocking_outcome"
```

- A `name` is a field from the registry or a parameter from the parameter file. An enum value is written bare, for example `salaried`.
- Types are checked. Integers and decimals compare exactly with each other. An enum accepts only `==` and `!=`, against a value that belongs to it. A boolean on its own is a complete comparison (`not kyc_verified`). `+` and `-` work on numbers only.
- `any_required_unknown` is true when any field the registry marks `required` is unknown.
- `no_blocking_outcome` is true when no earlier rule in the run has fired with the outcome `ineligible` or `refer`.

**Three states of a value.** A field is *known*, *unknown* or *absent*.

- Unknown: an input is missing or null, or a derived value cannot be computed because of it.
- Absent: the rule that produces a derived value did not run, for example because an earlier rule blocked the amount step.
- A rule that reads an unknown field is not evaluated, and the trace records `not_evaluated` with the missing field. The exception is `known()` and `unknown()`, which exist to read that state.
- A rule that reads an absent field is skipped, and the trace records `skipped` with the reason.
- A rule whose `when` is `no_blocking_outcome`, or has no\_blocking\_outcome as its first condition joined by and (as A04 does), is skipped when no\_blocking\_outcome is false.

This gives the trace its four statuses: `fired`, `not_fired`, `not_evaluated` and `skipped`. If E02 finds no band, `band` stays absent, A01 and A02 are skipped, and no rule decides the case. The decision then defaults to REFER with `NO_RULE_APPLICABLE` (CP-8.1). The band coverage check in section 2 exists so that this cannot happen with the baseline parameters.

### The 20 active rules and the 2 experimental ones

This table is the catalog written in the condition language. The coding agent encodes it as given.

| ID | `when` | Outcome | Reason code, or calculations |
| --- | --- | --- | --- |
| V01 | `any_required_unknown` | refer | `INCOMPLETE_APPLICATION` |
| V02 | `not consent_given` | ineligible | `CONSENT_NOT_GIVEN` |
| V03 | `requested_amount < min_amount or requested_amount > max_amount` | ineligible | `AMOUNT_OUTSIDE_PRODUCT_LIMITS` |
| V04 | `requested_tenure_months < min_tenure_months or requested_tenure_months > max_tenure_months` | ineligible | `TENURE_OUTSIDE_PRODUCT_LIMITS` |
| K01 | `age < min_age` | ineligible | `LEGAL_CAPACITY_NOT_MET` |
| K02 | `not kyc_verified` | ineligible | `KYC_NOT_VERIFIED` |
| K03 | `severe_delinquency_36m or written_off` | ineligible | `ADVERSE_REPAYMENT_HISTORY` |
| K04 | `credit_score < min_credit_score` | ineligible | `CREDIT_SCORE_BELOW_MINIMUM` |
| K05 | `monthly_net_income < min_monthly_income` | ineligible | `INCOME_BELOW_MINIMUM` |
| K06 | `(employment_type == salaried and employment_months < min_employment_months_salaried) or (employment_type == self_employed and employment_months < min_employment_months_self_employed)` | ineligible | `EMPLOYMENT_TENURE_TOO_SHORT` |
| R01 | `unknown(credit_score)` | refer | `NO_CREDIT_HISTORY` |
| R02 | `enquiries_6m > max_enquiries_6m` | refer | `HIGH_RECENT_ENQUIRIES` |
| R03 | `employment_type == other` | refer | `EMPLOYMENT_TYPE_REQUIRES_REVIEW` |
| E01 | `existing_foir > max_existing_foir` | ineligible | `HIGH_EXISTING_OBLIGATIONS` |
| E02 | `no_blocking_outcome` | derive | calc `band_lookup`, computes `band` |
| A01 | `no_blocking_outcome` | derive | calc `F4`, `F5`, computes `max_emi`, `max_principal_emi` |
| A02 | `no_blocking_outcome` | derive | calc `F6`, computes `recommended_amount`, `binding_limit` |
| A03 | `recommended_amount < min_amount` | ineligible | `INSUFFICIENT_REPAYMENT_CAPACITY` |
| A04 | no\_blocking\_outcome and `recommended_amount + amount_step <= requested_amount` | reduced\_offer | by `binding_limit`: the three `AMOUNT_LIMITED_BY_...` codes |
| P01 | `no_blocking_outcome` | derive | calc `rate_lookup`, `F7`, computes `indicative_rate`, `fee` |
| X01 (disabled) | `age_at_maturity > max_age_at_maturity` | ineligible | `AGE_AT_MATURITY_LIMIT`; `after = "K06"` |
| X02 (disabled) | `region_tier == high_risk_region_tier` | placeholder | `REGIONAL_RISK_ADJUSTMENT`; `after = "E02"` |

The `order` number in a trace counts the active rules in this sequence: V01 to V04 are 1 to 4, K01 to K06 are 5 to 10, R01 to R03 are 11 to 13, E01 and E02 are 14 and 15, A01 to A04 are 16 to 19, and P01 is 20. A switched-on experimental rule takes the next number at its `after` position, and the rules after it move down by one.

X01 and X02 are disabled in the baseline. X02 changes a band or makes the case ineligible, which fits neither `derive` nor the other outcomes cleanly, so its entry is a placeholder until I define it for Phase 5, and the loader does not resolve a disabled rule's calculations. The positions in `after` are my proposal; the catalog gives none.

### Generated artifacts

From each active rule the loader generates a Prolog clause in the shape the Predicate and Fact Schema sketches, with the unknown-value guard, and a first-order formula for the report. For K04 the clause is:

```prolog
fired(A, k04, ineligible, credit_score_below_minimum) :-
    \+ unknown(A, credit_score),
    credit_score(A, S), param(min_credit_score, Min), S < Min.
```

Generated files are build output. They are not edited by hand and they are not part of the rule-set hash (section 6); the source files are.

## 5. Loader behaviour

A loader either returns a complete, checked object or fails with every problem it found. It never returns part of a policy, never fills in a missing value, and never converts one type to another. A policy that loads is therefore one that was checked.

**Rules for every loader**

- Collect all errors in one pass instead of stopping at the first, so one run shows the whole list.
- Each error has a code, the file, the place (a key, a rule ID or a field name) and a message. Example: `FLOAT_FORBIDDEN params/params.toml [eligibility] max_existing_foir: value 0.5 is a float; write "0.5"`.
- The command exits with a non-zero status if there is any error. Warnings are printed and do not change the status.
- No default values. A missing key is an error, not a guess.
- No coercion. The text `"650"` is not the integer 650, `1` is not `true`, and an integer is not accepted where a decimal string is required.
- Unknown keys are errors, so a misspelt name cannot be silently ignored.
- The result is read-only after loading: integers as `int`, decimals as `Decimal`, booleans as `bool`.

Phase 0 builds the parameter loader and `make check-params`. Phase 1 adds the field registry loader. Phase 2 adds the rule, reason code and manifest loaders and `make check-rules`, which runs everything.

**Error codes.** An error stops the load.

| Code | Raised when |
| --- | --- |
| `PARSE_ERROR` | A file is not valid TOML |
| `MISSING_KEY` | A required key or parameter is absent |
| `UNKNOWN_KEY` | A key or parameter is not in this specification |
| `TYPE_ERROR` | A value is not of the exact type or pattern required |
| `FLOAT_FORBIDDEN` | A TOML float appears anywhere |
| `RANGE_ERROR` | A value is outside its valid range |
| `DUPLICATE_NAME` | A parameter name, field name, code or band ID appears twice |
| `ORDER_ERROR` | A minimum exceeds its maximum, or a value is not a multiple of `amount_step` |
| `BAND_ORDER` | Bands are not ordered best first |
| `BAND_COVERAGE_GAP` | The last band does not cover everything that clears K04 and E01 |
| `RATE_NOT_MIDPOINT` | `indicative_rate` is not the midpoint of its range |
| `REGISTRY_ERROR` | A registry entry is incomplete or inconsistent, for example a derived field with no `produced_by` |
| `CYCLE` | Derived fields depend on each other in a loop |
| `MANIFEST_ERROR` | The manifest lists a missing file, repeats a layer, or gives the wrong order |
| `BAD_RULE_ID` | A rule ID has the wrong shape or its letter does not match the layer |
| `DUPLICATE_RULE_ID` | A rule ID appears twice in any file or any status |
| `LAYER_MISMATCH` | A rule's `layer` differs from its file's `layer` |
| `EXPERIMENTAL_STATUS` | An experimental rule is `active` |
| `CONDITION_SYNTAX` | A `when` does not parse |
| `MAGIC_NUMBER` | A `when` contains a numeric literal |
| `UNKNOWN_NAME` | A `when` uses a name that is not a field, a parameter or an enum value |
| `TYPE_MISMATCH` | A `when` compares values of incompatible types |
| `FUTURE_READ` | A rule reads a derived field before the layer in `readable_from`, or before the rule that produces it |
| `UNKNOWN_CALC` | A `calc` ID is not in the calculation registry |
| `COMPUTES_MISMATCH` | `computes` differs from what the calculations return or from the registry |
| `REASON_CODE_MISSING` | An `ineligible`, `refer` or `reduced_offer` rule has no reason code |
| `REASON_CODE_NOT_ALLOWED` | A `derive` rule has one |
| `UNKNOWN_REASON_CODE` | A rule names a code that is not in `reason_codes.toml` |
| `REASON_MAP_INCOMPLETE` | A `by` table misses a value of its enum |
| `ORPHAN_CODE` | A code in `reason_codes.toml` is raised by no rule, or names a rule that does not raise it |
| `TEMPLATE_PLACEHOLDER` | A text uses a placeholder that is not allowed or not recorded in the trace for that rule |

**Warnings.** A warning is printed and does not stop the load.

| Code | Raised when |
| --- | --- |
| `WARN_PRICING_ORDER` | `indicative_rate` falls, or `post_loan_foir_cap` rises, from one band to the next |
| `WARN_LITERAL_IN_TEXT` | A reason code text contains a number equal to a parameter value, so the text may go stale; `allow_literals` silences it for a number that is meant |

**The hygiene checks.** The Credit Policy and Rule Catalog (FR-18) requires five checks. The loader runs two itself: orphans (`ORPHAN_CODE`, `UNKNOWN_REASON_CODE`) and cycles (`CYCLE`). It keeps every condition as a parsed tree and hands the trees to the hygiene analyser, which does completeness, contradiction and redundancy. Those three are specified in the Decision Tables, which I write before WP-07.

## 6. Versioning and hashing

Every decision records which exact rule set produced it, in two forms: a readable tag and a content hash. The tag is for people; the hash is the proof, because it changes whenever a byte of policy changes.

**The manifest: rules/manifest.toml**

```toml
rules_version = "0.1.0"
layers = ["validation", "knockout", "referral", "eligibility", "amount", "pricing", "experimental"]
fields = "fields.toml"
reason_codes = "reason_codes.toml"
```

Each layer in `layers` names a file `rules/<layer>.toml`. The list gives the run order; a layer missing from the list, or listed twice, is `MANIFEST_ERROR`.

**The tag.** `rule_set_version` is `rules-<rules_version>+params-<params_version>`, for example `rules-0.1.0+params-0.1.0`, as in the trace example.

**The hash.** `rule_set_hash` is `sha256:` followed by 64 hexadecimal characters, computed like this:

1. Take these files in this fixed order: `params/params.toml`, `rules/manifest.toml`, `rules/fields.toml`, `rules/reason_codes.toml`, then the seven layer files in manifest order. The experimental file is included even when every rule in it is disabled, because the switches that turn them on are in the parameter file.
2. Read each file as UTF-8, remove any byte order mark, and turn every CRLF or lone CR into LF. The file is otherwise unchanged, so a change to a comment or a space changes the hash.
3. For each file, form the text of its relative path, a newline, the length in bytes of the normalised content, a newline, and the normalised content itself.
4. Join those pieces in order and take the SHA-256 of the whole.

The generated Prolog is build output and is not hashed. It must still be deterministic: generating it twice from the same files gives identical text.

**When to change which version**

- A change under `params/` changes `params_version`. A change under `rules/` changes `rules_version`. A change to both bumps both.
- Major: any change that could alter a decision for some applicant: a parameter value, a condition, an outcome, a reason code, a band.
- Minor: a new disabled rule, or a new reason code no active rule uses.
- Patch: a change to wording only, such as a description, an owner or an applicant text.

**The pin test.** The file `tests/golden/rule_set_pin.json` holds the current tag and hash. `make test` fails in two cases: the hash differs from the pin, or the hash differs while the tag is unchanged (a version that was not bumped). Updating the pin is a deliberate edit, so it shows in the review diff of every policy change.

**Replay.** A stored decision carries `rule_set_version` and `rule_set_hash`. If the loaded set has the same tag but a different hash, replay stops with `REPLAY_VERSION_MISMATCH`. If the tag differs, replay needs the older files; each released tag must therefore be kept retrievable, for example as a git tag named `rules-<tag>`. The Audit Log Specification decides how this works in practice.

**Not in the hash.** Results also depend on the code in `src/calc` and `src/engine`. The audit record stores the code version (the commit hash) beside the rule-set hash; the Audit Log Specification defines that field. The trace needs a new field `rule_set_hash` next to `rule_set_version`; I have added it to the Predicate and Fact Schema, and the trace JSON Schema will include it.

## 7. Tests the loaders must pass

Each test starts from the baseline files in this specification and changes one thing. The test passes when the loader reports exactly the stated code, and for the valid cases when it loads with no error. The tests in the first table are Phase 0 exit criteria; the second table is for Phase 2.

**Parameter loader (Phase 0)**

| ID | Change to the baseline | Expected |
| --- | --- | --- |
| PT-01 | None | Loads. `min_credit_score` is the `int` 650, `max_existing_foir` equals `Decimal("0.50")`, band A has `min_score` 750, and a walk of the loaded object finds no float |
| PT-02 | `max_existing_foir = 0.5` as a TOML float | `FLOAT_FORBIDDEN` |
| PT-03 | A decimal written as `"0,5"`, `"5e-1"`, `".5"`, `"+0.5"`, `" 0.5"` or `"0.5 "`, one per run | `TYPE_ERROR` each time |
| PT-04 | Remove `min_credit_score` | `MISSING_KEY` |
| PT-05 | Add `min_cibil = 650` | `UNKNOWN_KEY` |
| PT-06 | Put the same parameter name in two sections | `DUPLICATE_NAME` |
| PT-07 | `min_age = true`, then `min_age = "18"` | `TYPE_ERROR` each time |
| PT-08 | `min_credit_score = 1000` | `RANGE_ERROR` |
| PT-09 | `min_amount` above `max_amount`, then `max_amount = 2500001` | `ORDER_ERROR` each time |
| PT-10 | Swap bands A and C | `BAND_ORDER` |
| PT-11 | Last band `min_score = 700` | `BAND_COVERAGE_GAP` |
| PT-12 | Band A `indicative_rate = "12.5"` | `RATE_NOT_MIDPOINT` |
| PT-13 | Three of the faults above in one file | All three reported in a single run |
| PT-14 | Band C `rate_low = "10.0"`, `rate_high = "12.0"`, `indicative_rate = "11.0"` | Loads, with `WARN_PRICING_ORDER` |
| PT-15 | Hash the baseline files with LF line ends, then with CRLF | Same hash. Changing one character gives a different hash |

**Rule loaders (Phase 2)**

| ID | Change to the baseline | Expected |
| --- | --- | --- |
| RT-01 | None | Loads: 20 active rules, 2 disabled, 21 reason codes, each code raised by exactly the rule the catalog names |
| RT-02 | K04 appears twice | `DUPLICATE_RULE_ID` |
| RT-03 | A rule `K04` placed in `validation.toml` | `BAD_RULE_ID` |
| RT-04 | `when = "credit_score < 650"` | `MAGIC_NUMBER` |
| RT-05 | `when = "credit_scor < min_credit_score"` | `UNKNOWN_NAME` |
| RT-06 | `when = "employment_type < salaried"` | `TYPE_MISMATCH` |
| RT-07 | A knockout rule that reads `recommended_amount` | `FUTURE_READ` |
| RT-08 | A02 with `computes = ["recommended_amount"]` only | `COMPUTES_MISMATCH` |
| RT-09 | An `ineligible` rule with no `reason_code`, then a `derive` rule with one | `REASON_CODE_MISSING`, then `REASON_CODE_NOT_ALLOWED` |
| RT-10 | The A04 table without `product_maximum` | `REASON_MAP_INCOMPLETE` |
| RT-11 | Delete rule R03 and leave its code | `ORPHAN_CODE` |
| RT-12 | A text that uses `{income}` | `TEMPLATE_PLACEHOLDER` |
| RT-13 | The K04 text uses `{enquiries_6m}`, which K04 does not read | `TEMPLATE_PLACEHOLDER` |
| RT-14 | Remove `allow_literals` from `HIGH_RECENT_ENQUIRIES` | Loads, with `WARN_LITERAL_IN_TEXT` |
| RT-15 | X01 set to `status = "active"` | `EXPERIMENTAL_STATUS` |
| RT-16 | Two runs of the generator | Identical Prolog text, and the K04 clause equals the example in section 4 apart from white space |
| RT-17 | Change a parameter value and nothing else | The rule-set hash changes and the pin test fails until the pin and the version are updated |

**Behaviour the engine tests must confirm in Phase 2.** These are not loader errors but follow from section 4, and the engine tests cover them:

- `credit_score` null: K04 is `not_evaluated` with `credit_score` missing, R01 fires, V01 does not.
- `requested_amount` missing: V01 fires, V03 is `not_evaluated`.
- Any earlier INELIGIBLE or REFER outcome: E02, A01, A02 and P01 are `skipped`, and so are A03 and A04, whose derived fields are then absent.
- No band found (use a test-only parameter set that switches off the coverage check): A01 and A02 are skipped, and the decision is REFER with `NO_RULE_APPLICABLE`.
- A request of 777,777 with room for the full amount: the recommended amount is 775,000 and A04 does not fire, because the shortfall is less than one step.
- A request of 800,000 as in TV2: A04 fires with `AMOUNT_LIMITED_BY_REPAYMENT_CAPACITY`.
