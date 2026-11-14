# Fairness Tables — D2 (Treatment A: refer = not approved)

> Limits from docs/fairness-audit-plan.md section 1 apply to all findings.
> Groups shown as 'too_small' (< 100) or 'unstable' (< 20 events) are not findings.

| System | Attribute | Metric | Group | Size | Status | Rate | Ref Rate | Diff | CI Low | CI High | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_system | gender | equal_opportunity_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| rule_system | gender | equal_opportunity_difference | M | 15774 | scored | 0.0222 | 0.0154 | 0.0067 | 0.0036 | 0.0101 | 🚩 |
| rule_system | gender | equal_opportunity_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| rule_system | gender | selection_rate_ratio | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_ratio | M | 15774 | not_computed |  |  |  |  |  | None |
| rule_system | gender | selection_rate_ratio | XNA | 1 | too_small |  |  |  |  |  | None |
| rule_system | gender | selection_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_difference | M | 15774 | scored | 0.0202 | 0.0151 | 0.0052 | 0.0023 | 0.0082 | 🚩 |
| rule_system | gender | selection_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| rule_system | gender | false_approval_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| rule_system | gender | false_approval_rate_difference | M | 15774 | scored | 0.0031 | 0.0100 | -0.0069 | -0.0127 | -0.0015 | 🚩 |
| rule_system | gender | false_approval_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| rule_system | gender | default_rate_among_approved | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | M | 15774 | scored | 0.0157 | 0.0460 | -0.0303 | -0.0581 | -0.0048 | 🚩 |
| rule_system | gender | default_rate_among_approved | XNA | 1 | too_small |  |  |  |  |  | None |
| rule_system | age_band | equal_opportunity_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| rule_system | age_band | equal_opportunity_difference | 21-29 | 6770 | scored | 0.0085 | 0.0187 | -0.0102 | -0.0144 | -0.0060 | 🚩 |
| rule_system | age_band | equal_opportunity_difference | 40-49 | 11488 | scored | 0.0282 | 0.0187 | 0.0095 | 0.0045 | 0.0146 | 🚩 |
| rule_system | age_band | equal_opportunity_difference | 50-59 | 10170 | scored | 0.0175 | 0.0187 | -0.0012 | -0.0058 | 0.0033 |  |
| rule_system | age_band | equal_opportunity_difference | 60+ | 5312 | scored | 0.0046 | 0.0187 | -0.0141 | -0.0180 | -0.0102 | 🚩 |
| rule_system | age_band | selection_rate_ratio | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | 21-29 | 6770 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 40-49 | 11488 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 50-59 | 10170 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 60+ | 5312 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | 21-29 | 6770 | scored | 0.0075 | 0.0176 | -0.0101 | -0.0138 | -0.0062 | 🚩 |
| rule_system | age_band | selection_rate_difference | 40-49 | 11488 | scored | 0.0268 | 0.0176 | 0.0092 | 0.0043 | 0.0141 | 🚩 |
| rule_system | age_band | selection_rate_difference | 50-59 | 10170 | scored | 0.0173 | 0.0176 | -0.0003 | -0.0044 | 0.0039 |  |
| rule_system | age_band | selection_rate_difference | 60+ | 5312 | scored | 0.0043 | 0.0176 | -0.0133 | -0.0169 | -0.0097 | 🚩 |
| rule_system | age_band | false_approval_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 21-29 | 6770 | scored | 0.0000 | 0.0074 | -0.0074 | -0.0141 | -0.0024 | 🚩 |
| rule_system | age_band | false_approval_rate_difference | 40-49 | 11488 | scored | 0.0095 | 0.0074 | 0.0020 | -0.0081 | 0.0127 |  |
| rule_system | age_band | false_approval_rate_difference | 50-59 | 10170 | scored | 0.0147 | 0.0074 | 0.0072 | -0.0056 | 0.0226 |  |
| rule_system | age_band | false_approval_rate_difference | 60+ | 5312 | scored | 0.0000 | 0.0074 | -0.0074 | -0.0142 | -0.0017 | 🚩 |
| rule_system | age_band | default_rate_among_approved | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 21-29 | 6770 | scored | 0.0000 | 0.0413 | -0.0413 | -0.0770 | -0.0126 | 🚩 |
| rule_system | age_band | default_rate_among_approved | 40-49 | 11488 | scored | 0.0260 | 0.0413 | -0.0153 | -0.0581 | 0.0238 |  |
| rule_system | age_band | default_rate_among_approved | 50-59 | 10170 | scored | 0.0511 | 0.0413 | 0.0099 | -0.0387 | 0.0686 |  |
| rule_system | age_band | default_rate_among_approved | 60+ | 5312 | scored | 0.0000 | 0.0413 | -0.0413 | -0.0793 | -0.0097 | 🚩 |
| rule_system | region_rating | equal_opportunity_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| rule_system | region_rating | equal_opportunity_difference | 1 | 4884 | scored | 0.0413 | 0.0160 | 0.0253 | 0.0183 | 0.0319 | 🚩 |
| rule_system | region_rating | equal_opportunity_difference | 3 | 7242 | scored | 0.0089 | 0.0160 | -0.0071 | -0.0102 | -0.0040 | 🚩 |
| rule_system | region_rating | selection_rate_ratio | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| rule_system | region_rating | selection_rate_ratio | 1 | 4884 | not_computed |  |  |  |  |  | None |
| rule_system | region_rating | selection_rate_ratio | 3 | 7242 | not_computed |  |  |  |  |  | None |
| rule_system | region_rating | selection_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| rule_system | region_rating | selection_rate_difference | 1 | 4884 | scored | 0.0401 | 0.0154 | 0.0248 | 0.0180 | 0.0310 | 🚩 |
| rule_system | region_rating | selection_rate_difference | 3 | 7242 | scored | 0.0080 | 0.0154 | -0.0073 | -0.0101 | -0.0046 | 🚩 |
| rule_system | region_rating | false_approval_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| rule_system | region_rating | false_approval_rate_difference | 1 | 4884 | scored | 0.0170 | 0.0079 | 0.0091 | -0.0070 | 0.0284 |  |
| rule_system | region_rating | false_approval_rate_difference | 3 | 7242 | scored | 0.0012 | 0.0079 | -0.0067 | -0.0115 | -0.0024 | 🚩 |
| rule_system | region_rating | default_rate_among_approved | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| rule_system | region_rating | default_rate_among_approved | 1 | 4884 | scored | 0.0204 | 0.0402 | -0.0198 | -0.0488 | 0.0080 |  |
| rule_system | region_rating | default_rate_among_approved | 3 | 7242 | scored | 0.0172 | 0.0402 | -0.0230 | -0.0563 | 0.0284 |  |
| rule_system | employment_type | equal_opportunity_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| rule_system | employment_type | equal_opportunity_difference | other | 8260 | unstable | 0.0000 | 0.0205 | -0.0205 |  |  | None |
| rule_system | employment_type | equal_opportunity_difference | self_employed | 10721 | scored | 0.0247 | 0.0205 | 0.0042 | 0.0004 | 0.0080 | 🚩 |
| rule_system | employment_type | selection_rate_ratio | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_ratio | other | 8260 | not_computed |  |  |  |  |  | None |
| rule_system | employment_type | selection_rate_ratio | self_employed | 10721 | not_computed |  |  |  |  |  | None |
| rule_system | employment_type | selection_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | other | 8260 | unstable | 0.0000 | 0.0192 | -0.0192 |  |  | None |
| rule_system | employment_type | selection_rate_difference | self_employed | 10721 | scored | 0.0237 | 0.0192 | 0.0045 | 0.0008 | 0.0080 | 🚩 |
| rule_system | employment_type | false_approval_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | other | 8260 | scored | 0.0000 | 0.0066 | -0.0066 | -0.0105 | -0.0033 | 🚩 |
| rule_system | employment_type | false_approval_rate_difference | self_employed | 10721 | scored | 0.0120 | 0.0066 | 0.0054 | -0.0034 | 0.0156 |  |
| rule_system | employment_type | default_rate_among_approved | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | other | 8260 | scored | nan | 0.0307 | nan | nan | nan | 🚩 |
| rule_system | employment_type | default_rate_among_approved | self_employed | 10721 | scored | 0.0394 | 0.0307 | 0.0087 | -0.0215 | 0.0448 |  |
| rule_system | income_band | equal_opportunity_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| rule_system | income_band | equal_opportunity_difference | Q2 | 7999 | unstable | 0.0000 | 0.0000 | 0.0000 |  |  | None |
| rule_system | income_band | equal_opportunity_difference | Q3 | 12392 | unstable | 0.0234 | 0.0000 | 0.0234 |  |  | None |
| rule_system | income_band | equal_opportunity_difference | Q4 | 10780 | unstable | 0.0482 | 0.0000 | 0.0482 |  |  | None |
| rule_system | income_band | selection_rate_ratio | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q2 | 7999 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_ratio | Q3 | 12392 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_ratio | Q4 | 10780 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | Q2 | 7999 | unstable | 0.0000 | 0.0000 | 0.0000 |  |  | None |
| rule_system | income_band | selection_rate_difference | Q3 | 12392 | unstable | 0.0224 | 0.0000 | 0.0224 |  |  | None |
| rule_system | income_band | selection_rate_difference | Q4 | 10780 | unstable | 0.0462 | 0.0000 | 0.0462 |  |  | None |
| rule_system | income_band | false_approval_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q2 | 7999 | scored | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| rule_system | income_band | false_approval_rate_difference | Q3 | 12392 | scored | 0.0120 | 0.0000 | 0.0120 | 0.0047 | 0.0213 | 🚩 |
| rule_system | income_band | false_approval_rate_difference | Q4 | 10780 | scored | 0.0180 | 0.0000 | 0.0180 | 0.0079 | 0.0317 | 🚩 |
| rule_system | income_band | default_rate_among_approved | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q2 | 7999 | scored | nan | nan | nan | nan | nan | 🚩 |
| rule_system | income_band | default_rate_among_approved | Q3 | 12392 | scored | 0.0468 | nan | nan | nan | nan | 🚩 |
| rule_system | income_band | default_rate_among_approved | Q4 | 10780 | scored | 0.0261 | nan | nan | nan | nan | 🚩 |
| lr | gender | equal_opportunity_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| lr | gender | equal_opportunity_difference | M | 15774 | scored | 0.0113 | 0.0195 | -0.0082 | -0.0107 | -0.0054 | 🚩 |
| lr | gender | equal_opportunity_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| lr | gender | selection_rate_ratio | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_ratio | M | 15774 | not_computed |  |  |  |  |  | None |
| lr | gender | selection_rate_ratio | XNA | 1 | too_small |  |  |  |  |  | None |
| lr | gender | selection_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | M | 15774 | scored | 0.0102 | 0.0184 | -0.0082 | -0.0106 | -0.0056 | 🚩 |
| lr | gender | selection_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| lr | gender | false_approval_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| lr | gender | false_approval_rate_difference | M | 15774 | scored | 0.0006 | 0.0043 | -0.0037 | -0.0073 | -0.0006 | 🚩 |
| lr | gender | false_approval_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| lr | gender | default_rate_among_approved | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | M | 15774 | scored | 0.0062 | 0.0161 | -0.0099 | -0.0269 | 0.0094 |  |
| lr | gender | default_rate_among_approved | XNA | 1 | too_small |  |  |  |  |  | None |
| lr | age_band | equal_opportunity_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| lr | age_band | equal_opportunity_difference | 21-29 | 6770 | unstable | 0.0000 | 0.0021 | -0.0021 |  |  | None |
| lr | age_band | equal_opportunity_difference | 40-49 | 11488 | scored | 0.0120 | 0.0021 | 0.0100 | 0.0075 | 0.0130 | 🚩 |
| lr | age_band | equal_opportunity_difference | 50-59 | 10170 | scored | 0.0335 | 0.0021 | 0.0314 | 0.0266 | 0.0362 | 🚩 |
| lr | age_band | equal_opportunity_difference | 60+ | 5312 | scored | 0.0475 | 0.0021 | 0.0455 | 0.0380 | 0.0531 | 🚩 |
| lr | age_band | selection_rate_ratio | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | 21-29 | 6770 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 40-49 | 11488 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 50-59 | 10170 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 60+ | 5312 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | 21-29 | 6770 | unstable | 0.0000 | 0.0019 | -0.0019 |  |  | None |
| lr | age_band | selection_rate_difference | 40-49 | 11488 | scored | 0.0113 | 0.0019 | 0.0095 | 0.0071 | 0.0123 | 🚩 |
| lr | age_band | selection_rate_difference | 50-59 | 10170 | scored | 0.0318 | 0.0019 | 0.0299 | 0.0254 | 0.0345 | 🚩 |
| lr | age_band | selection_rate_difference | 60+ | 5312 | scored | 0.0459 | 0.0019 | 0.0441 | 0.0368 | 0.0513 | 🚩 |
| lr | age_band | false_approval_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 21-29 | 6770 | scored | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| lr | age_band | false_approval_rate_difference | 40-49 | 11488 | scored | 0.0024 | 0.0000 | 0.0024 | 0.0000 | 0.0069 |  |
| lr | age_band | false_approval_rate_difference | 50-59 | 10170 | scored | 0.0049 | 0.0000 | 0.0049 | 0.0000 | 0.0131 |  |
| lr | age_band | false_approval_rate_difference | 60+ | 5312 | scored | 0.0177 | 0.0000 | 0.0177 | 0.0000 | 0.0394 |  |
| lr | age_band | default_rate_among_approved | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 21-29 | 6770 | scored | nan | 0.0000 | nan | nan | nan | 🚩 |
| lr | age_band | default_rate_among_approved | 40-49 | 11488 | scored | 0.0154 | 0.0000 | 0.0154 | 0.0000 | 0.0434 |  |
| lr | age_band | default_rate_among_approved | 50-59 | 10170 | scored | 0.0093 | 0.0000 | 0.0093 | 0.0000 | 0.0247 |  |
| lr | age_band | default_rate_among_approved | 60+ | 5312 | scored | 0.0205 | 0.0000 | 0.0205 | 0.0000 | 0.0460 |  |
| lr | region_rating | equal_opportunity_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| lr | region_rating | equal_opportunity_difference | 1 | 4884 | scored | 0.0417 | 0.0155 | 0.0263 | 0.0197 | 0.0336 | 🚩 |
| lr | region_rating | equal_opportunity_difference | 3 | 7242 | scored | 0.0048 | 0.0155 | -0.0106 | -0.0129 | -0.0080 | 🚩 |
| lr | region_rating | selection_rate_ratio | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| lr | region_rating | selection_rate_ratio | 1 | 4884 | not_computed |  |  |  |  |  | None |
| lr | region_rating | selection_rate_ratio | 3 | 7242 | not_computed |  |  |  |  |  | None |
| lr | region_rating | selection_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| lr | region_rating | selection_rate_difference | 1 | 4884 | scored | 0.0405 | 0.0144 | 0.0261 | 0.0198 | 0.0334 | 🚩 |
| lr | region_rating | selection_rate_difference | 3 | 7242 | scored | 0.0043 | 0.0144 | -0.0102 | -0.0123 | -0.0079 | 🚩 |
| lr | region_rating | false_approval_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| lr | region_rating | false_approval_rate_difference | 1 | 4884 | scored | 0.0170 | 0.0023 | 0.0148 | -0.0017 | 0.0351 |  |
| lr | region_rating | false_approval_rate_difference | 3 | 7242 | scored | 0.0000 | 0.0023 | -0.0023 | -0.0043 | -0.0004 | 🚩 |
| lr | region_rating | default_rate_among_approved | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| lr | region_rating | default_rate_among_approved | 1 | 4884 | scored | 0.0202 | 0.0122 | 0.0080 | -0.0156 | 0.0344 |  |
| lr | region_rating | default_rate_among_approved | 3 | 7242 | scored | 0.0000 | 0.0122 | -0.0122 | -0.0236 | -0.0021 | 🚩 |
| lr | employment_type | equal_opportunity_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| lr | employment_type | equal_opportunity_difference | other | 8260 | scored | 0.0335 | 0.0100 | 0.0235 | 0.0185 | 0.0277 | 🚩 |
| lr | employment_type | equal_opportunity_difference | self_employed | 10721 | scored | 0.0203 | 0.0100 | 0.0103 | 0.0071 | 0.0139 | 🚩 |
| lr | employment_type | selection_rate_ratio | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_ratio | other | 8260 | not_computed |  |  |  |  |  | None |
| lr | employment_type | selection_rate_ratio | self_employed | 10721 | not_computed |  |  |  |  |  | None |
| lr | employment_type | selection_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | other | 8260 | scored | 0.0320 | 0.0092 | 0.0227 | 0.0180 | 0.0267 | 🚩 |
| lr | employment_type | selection_rate_difference | self_employed | 10721 | scored | 0.0191 | 0.0092 | 0.0099 | 0.0068 | 0.0132 | 🚩 |
| lr | employment_type | false_approval_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | other | 8260 | scored | 0.0063 | 0.0012 | 0.0051 | -0.0016 | 0.0141 |  |
| lr | employment_type | false_approval_rate_difference | self_employed | 10721 | scored | 0.0048 | 0.0012 | 0.0036 | -0.0010 | 0.0095 |  |
| lr | employment_type | default_rate_among_approved | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | other | 8260 | scored | 0.0114 | 0.0120 | -0.0006 | -0.0205 | 0.0198 |  |
| lr | employment_type | default_rate_among_approved | self_employed | 10721 | scored | 0.0195 | 0.0120 | 0.0076 | -0.0179 | 0.0360 |  |
| lr | income_band | equal_opportunity_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| lr | income_band | equal_opportunity_difference | Q2 | 7999 | scored | 0.0169 | 0.0119 | 0.0051 | 0.0011 | 0.0097 | 🚩 |
| lr | income_band | equal_opportunity_difference | Q3 | 12392 | scored | 0.0176 | 0.0119 | 0.0057 | 0.0020 | 0.0096 | 🚩 |
| lr | income_band | equal_opportunity_difference | Q4 | 10780 | scored | 0.0223 | 0.0119 | 0.0104 | 0.0064 | 0.0146 | 🚩 |
| lr | income_band | selection_rate_ratio | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_ratio | Q2 | 7999 | not_computed |  |  |  |  |  | None |
| lr | income_band | selection_rate_ratio | Q3 | 12392 | not_computed |  |  |  |  |  | None |
| lr | income_band | selection_rate_ratio | Q4 | 10780 | not_computed |  |  |  |  |  | None |
| lr | income_band | selection_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | Q2 | 7999 | scored | 0.0155 | 0.0110 | 0.0045 | 0.0009 | 0.0088 | 🚩 |
| lr | income_band | selection_rate_difference | Q3 | 12392 | scored | 0.0167 | 0.0110 | 0.0057 | 0.0023 | 0.0092 | 🚩 |
| lr | income_band | selection_rate_difference | Q4 | 10780 | scored | 0.0209 | 0.0110 | 0.0099 | 0.0062 | 0.0138 | 🚩 |
| lr | income_band | false_approval_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q2 | 7999 | scored | 0.0000 | 0.0008 | -0.0008 | -0.0033 | 0.0000 |  |
| lr | income_band | false_approval_rate_difference | Q3 | 12392 | scored | 0.0074 | 0.0008 | 0.0066 | 0.0010 | 0.0134 | 🚩 |
| lr | income_band | false_approval_rate_difference | Q4 | 10780 | scored | 0.0014 | 0.0008 | 0.0006 | -0.0026 | 0.0054 |  |
| lr | income_band | default_rate_among_approved | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q2 | 7999 | scored | 0.0000 | 0.0061 | -0.0061 | -0.0244 | 0.0000 |  |
| lr | income_band | default_rate_among_approved | Q3 | 12392 | scored | 0.0386 | 0.0061 | 0.0326 | 0.0004 | 0.0677 | 🚩 |
| lr | income_band | default_rate_among_approved | Q4 | 10780 | scored | 0.0044 | 0.0061 | -0.0017 | -0.0228 | 0.0158 |  |
| gb | gender | equal_opportunity_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| gb | gender | equal_opportunity_difference | M | 15774 | scored | 0.0184 | 0.0183 | 0.0001 | -0.0031 | 0.0033 |  |
| gb | gender | equal_opportunity_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| gb | gender | selection_rate_ratio | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_ratio | M | 15774 | not_computed |  |  |  |  |  | None |
| gb | gender | selection_rate_ratio | XNA | 1 | too_small |  |  |  |  |  | None |
| gb | gender | selection_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | M | 15774 | scored | 0.0167 | 0.0173 | -0.0006 | -0.0036 | 0.0023 |  |
| gb | gender | selection_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| gb | gender | false_approval_rate_difference | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| gb | gender | false_approval_rate_difference | M | 15774 | scored | 0.0019 | 0.0033 | -0.0015 | -0.0054 | 0.0019 |  |
| gb | gender | false_approval_rate_difference | XNA | 1 | too_small |  |  |  |  |  | None |
| gb | gender | default_rate_among_approved | **F** (ref) | 30352 | reference |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | M | 15774 | scored | 0.0114 | 0.0133 | -0.0020 | -0.0198 | 0.0167 |  |
| gb | gender | default_rate_among_approved | XNA | 1 | too_small |  |  |  |  |  | None |
| gb | age_band | equal_opportunity_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| gb | age_band | equal_opportunity_difference | 21-29 | 6770 | unstable | 0.0032 | 0.0115 | -0.0084 |  |  | None |
| gb | age_band | equal_opportunity_difference | 40-49 | 11488 | scored | 0.0194 | 0.0115 | 0.0078 | 0.0041 | 0.0119 | 🚩 |
| gb | age_band | equal_opportunity_difference | 50-59 | 10170 | scored | 0.0302 | 0.0115 | 0.0187 | 0.0139 | 0.0241 | 🚩 |
| gb | age_band | equal_opportunity_difference | 60+ | 5312 | scored | 0.0270 | 0.0115 | 0.0155 | 0.0093 | 0.0217 | 🚩 |
| gb | age_band | selection_rate_ratio | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | 21-29 | 6770 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 40-49 | 11488 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 50-59 | 10170 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 60+ | 5312 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | 21-29 | 6770 | scored | 0.0030 | 0.0105 | -0.0075 | -0.0104 | -0.0053 | 🚩 |
| gb | age_band | selection_rate_difference | 40-49 | 11488 | scored | 0.0182 | 0.0105 | 0.0077 | 0.0042 | 0.0114 | 🚩 |
| gb | age_band | selection_rate_difference | 50-59 | 10170 | scored | 0.0286 | 0.0105 | 0.0181 | 0.0136 | 0.0232 | 🚩 |
| gb | age_band | selection_rate_difference | 60+ | 5312 | scored | 0.0262 | 0.0105 | 0.0157 | 0.0096 | 0.0216 | 🚩 |
| gb | age_band | false_approval_rate_difference | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 21-29 | 6770 | scored | 0.0013 | 0.0008 | 0.0005 | -0.0025 | 0.0051 |  |
| gb | age_band | false_approval_rate_difference | 40-49 | 11488 | scored | 0.0035 | 0.0008 | 0.0027 | -0.0018 | 0.0090 |  |
| gb | age_band | false_approval_rate_difference | 50-59 | 10170 | scored | 0.0033 | 0.0008 | 0.0024 | -0.0025 | 0.0094 |  |
| gb | age_band | false_approval_rate_difference | 60+ | 5312 | scored | 0.0106 | 0.0008 | 0.0098 | -0.0008 | 0.0262 |  |
| gb | age_band | default_rate_among_approved | **30-39** (ref) | 12387 | reference |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 21-29 | 6770 | scored | 0.0500 | 0.0077 | 0.0423 | -0.0245 | 0.2145 |  |
| gb | age_band | default_rate_among_approved | 40-49 | 11488 | scored | 0.0144 | 0.0077 | 0.0067 | -0.0214 | 0.0367 |  |
| gb | age_band | default_rate_among_approved | 50-59 | 10170 | scored | 0.0069 | 0.0077 | -0.0008 | -0.0275 | 0.0171 |  |
| gb | age_band | default_rate_among_approved | 60+ | 5312 | scored | 0.0216 | 0.0077 | 0.0139 | -0.0162 | 0.0487 |  |
| gb | region_rating | equal_opportunity_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| gb | region_rating | equal_opportunity_difference | 1 | 4884 | scored | 0.0527 | 0.0154 | 0.0373 | 0.0304 | 0.0460 | 🚩 |
| gb | region_rating | equal_opportunity_difference | 3 | 7242 | scored | 0.0080 | 0.0154 | -0.0075 | -0.0104 | -0.0045 | 🚩 |
| gb | region_rating | selection_rate_ratio | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| gb | region_rating | selection_rate_ratio | 1 | 4884 | not_computed |  |  |  |  |  | None |
| gb | region_rating | selection_rate_ratio | 3 | 7242 | not_computed |  |  |  |  |  | None |
| gb | region_rating | selection_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| gb | region_rating | selection_rate_difference | 1 | 4884 | scored | 0.0510 | 0.0144 | 0.0366 | 0.0300 | 0.0448 | 🚩 |
| gb | region_rating | selection_rate_difference | 3 | 7242 | scored | 0.0072 | 0.0144 | -0.0072 | -0.0098 | -0.0045 | 🚩 |
| gb | region_rating | false_approval_rate_difference | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| gb | region_rating | false_approval_rate_difference | 1 | 4884 | scored | 0.0170 | 0.0019 | 0.0151 | -0.0009 | 0.0368 |  |
| gb | region_rating | false_approval_rate_difference | 3 | 7242 | scored | 0.0012 | 0.0019 | -0.0007 | -0.0034 | 0.0031 |  |
| gb | region_rating | default_rate_among_approved | **2** (ref) | 34001 | reference |  |  |  |  |  |  |
| gb | region_rating | default_rate_among_approved | 1 | 4884 | scored | 0.0161 | 0.0102 | 0.0058 | -0.0124 | 0.0287 |  |
| gb | region_rating | default_rate_among_approved | 3 | 7242 | scored | 0.0192 | 0.0102 | 0.0090 | -0.0186 | 0.0696 |  |
| gb | employment_type | equal_opportunity_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| gb | employment_type | equal_opportunity_difference | other | 8260 | scored | 0.0163 | 0.0166 | -0.0003 | -0.0041 | 0.0037 |  |
| gb | employment_type | equal_opportunity_difference | self_employed | 10721 | scored | 0.0244 | 0.0166 | 0.0078 | 0.0039 | 0.0118 | 🚩 |
| gb | employment_type | selection_rate_ratio | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_ratio | other | 8260 | not_computed |  |  |  |  |  | None |
| gb | employment_type | selection_rate_ratio | self_employed | 10721 | not_computed |  |  |  |  |  | None |
| gb | employment_type | selection_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | other | 8260 | scored | 0.0154 | 0.0154 | -0.0000 | -0.0037 | 0.0038 |  |
| gb | employment_type | selection_rate_difference | self_employed | 10721 | scored | 0.0228 | 0.0154 | 0.0074 | 0.0039 | 0.0112 | 🚩 |
| gb | employment_type | false_approval_rate_difference | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | other | 8260 | scored | 0.0000 | 0.0029 | -0.0029 | -0.0054 | -0.0008 | 🚩 |
| gb | employment_type | false_approval_rate_difference | self_employed | 10721 | scored | 0.0036 | 0.0029 | 0.0007 | -0.0038 | 0.0064 |  |
| gb | employment_type | default_rate_among_approved | **salaried** (ref) | 27146 | reference |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | other | 8260 | scored | 0.0000 | 0.0167 | -0.0167 | -0.0313 | -0.0049 | 🚩 |
| gb | employment_type | default_rate_among_approved | self_employed | 10721 | scored | 0.0123 | 0.0167 | -0.0045 | -0.0246 | 0.0176 |  |
| gb | income_band | equal_opportunity_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| gb | income_band | equal_opportunity_difference | Q2 | 7999 | scored | 0.0109 | 0.0097 | 0.0012 | -0.0021 | 0.0047 |  |
| gb | income_band | equal_opportunity_difference | Q3 | 12392 | scored | 0.0091 | 0.0097 | -0.0006 | -0.0035 | 0.0022 |  |
| gb | income_band | equal_opportunity_difference | Q4 | 10780 | scored | 0.0460 | 0.0097 | 0.0363 | 0.0315 | 0.0412 | 🚩 |
| gb | income_band | selection_rate_ratio | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_ratio | Q2 | 7999 | not_computed |  |  |  |  |  | None |
| gb | income_band | selection_rate_ratio | Q3 | 12392 | not_computed |  |  |  |  |  | None |
| gb | income_band | selection_rate_ratio | Q4 | 10780 | not_computed |  |  |  |  |  | None |
| gb | income_band | selection_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | Q2 | 7999 | scored | 0.0100 | 0.0090 | 0.0010 | -0.0021 | 0.0042 |  |
| gb | income_band | selection_rate_difference | Q3 | 12392 | scored | 0.0086 | 0.0090 | -0.0004 | -0.0030 | 0.0021 |  |
| gb | income_band | selection_rate_difference | Q4 | 10780 | scored | 0.0433 | 0.0090 | 0.0343 | 0.0298 | 0.0392 | 🚩 |
| gb | income_band | false_approval_rate_difference | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q2 | 7999 | scored | 0.0000 | 0.0016 | -0.0016 | -0.0048 | 0.0000 |  |
| gb | income_band | false_approval_rate_difference | Q3 | 12392 | scored | 0.0037 | 0.0016 | 0.0021 | -0.0030 | 0.0076 |  |
| gb | income_band | false_approval_rate_difference | Q4 | 10780 | scored | 0.0055 | 0.0016 | 0.0039 | -0.0025 | 0.0130 |  |
| gb | income_band | default_rate_among_approved | **Q1** (ref) | 14956 | reference |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q2 | 7999 | scored | 0.0000 | 0.0148 | -0.0148 | -0.0425 | 0.0000 |  |
| gb | income_band | default_rate_among_approved | Q3 | 12392 | scored | 0.0374 | 0.0148 | 0.0226 | -0.0286 | 0.0798 |  |
| gb | income_band | default_rate_among_approved | Q4 | 10780 | scored | 0.0086 | 0.0148 | -0.0063 | -0.0398 | 0.0153 |  |
