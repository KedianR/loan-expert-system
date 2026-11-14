# Fairness Tables — D3 (Treatment A: refer = not approved)

> Limits from docs/fairness-audit-plan.md section 1 apply to all findings.
> Groups shown as 'too_small' (< 100) or 'unstable' (< 20 events) are not findings.

| System | Attribute | Metric | Group | Size | Status | Rate | Ref Rate | Diff | CI Low | CI High | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_system | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_difference | F | 1487 | scored | 0.4620 | 0.4825 | -0.0205 | -0.0576 | 0.0159 |  |
| rule_system | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_ratio | F | 1487 | not_computed |  |  |  |  |  | None |
| rule_system | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  | None |
| rule_system | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4657 | 0.4446 | 0.0211 | -0.0472 | 0.0835 |  |
| rule_system | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.4896 | 0.4446 | 0.0450 | -0.0232 | 0.1082 |  |
| rule_system | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.4895 | 0.4446 | 0.0449 | -0.0130 | 0.1095 |  |
| rule_system | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | 21-29 | 670 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 30-39 | 723 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 50-59 | 760 | not_computed |  |  |  |  |  | None |
| rule_system | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  | None |
| rule_system | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  | None |
| rule_system | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  | None |
| rule_system | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  | None |
| rule_system | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| rule_system | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  | None |
| rule_system | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  | None |
| rule_system | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  | None |
| rule_system | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  | None |
| rule_system | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_difference | 1 | 938 | scored | 0.4893 | 0.4579 | 0.0315 | -0.0098 | 0.0787 |  |
| rule_system | region_tier | selection_rate_difference | 3 | 579 | scored | 0.4819 | 0.4579 | 0.0240 | -0.0365 | 0.0763 |  |
| rule_system | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_ratio | 1 | 938 | not_computed |  |  |  |  |  | None |
| rule_system | region_tier | selection_rate_ratio | 3 | 579 | not_computed |  |  |  |  |  | None |
| rule_system | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  | None |
| rule_system | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  | None |
| rule_system | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  | None |
| rule_system | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  | None |
| rule_system | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5324 | -0.5324 |  |  | None |
| rule_system | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.3926 | 0.5323 | -0.1397 | -0.1876 | -0.0912 | 🚩 |
| rule_system | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_ratio | other | 139 | not_computed |  |  |  |  |  | None |
| rule_system | employment_type | selection_rate_ratio | self_employed | 759 | not_computed |  |  |  |  |  | None |
| rule_system | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  | None |
| rule_system | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  | None |
| rule_system | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  | None |
| rule_system | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | Q1 | 735 | scored | 0.3687 | 0.4808 | -0.1121 | -0.1724 | -0.0556 | 🚩 |
| rule_system | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5354 | 0.4808 | 0.0546 | -0.0082 | 0.1168 |  |
| rule_system | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5021 | 0.4808 | 0.0213 | -0.0392 | 0.0809 |  |
| rule_system | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q1 | 735 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_ratio | Q2 | 762 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | selection_rate_ratio | Q4 | 721 | not_computed |  |  |  |  |  | None |
| rule_system | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  | None |
| rule_system | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  | None |
| rule_system | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  | None |
| rule_system | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  | None |
| rule_system | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  | None |
| rule_system | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  | None |
| lr | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | F | 1487 | scored | 0.5037 | 0.4779 | 0.0258 | -0.0108 | 0.0600 |  |
| lr | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_ratio | F | 1487 | not_computed |  |  |  |  |  | None |
| lr | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  | None |
| lr | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  | None |
| lr | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.5433 | 0.4897 | 0.0536 | -0.0118 | 0.1177 |  |
| lr | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.4689 | 0.4897 | -0.0208 | -0.0897 | 0.0425 |  |
| lr | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.4645 | 0.4897 | -0.0252 | -0.0936 | 0.0310 |  |
| lr | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | 21-29 | 670 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 30-39 | 723 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 50-59 | 760 | not_computed |  |  |  |  |  | None |
| lr | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  | None |
| lr | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  | None |
| lr | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  | None |
| lr | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  | None |
| lr | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| lr | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  | None |
| lr | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  | None |
| lr | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  | None |
| lr | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  | None |
| lr | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_difference | 1 | 938 | scored | 0.4776 | 0.5037 | -0.0261 | -0.0722 | 0.0193 |  |
| lr | region_tier | selection_rate_difference | 3 | 579 | scored | 0.4784 | 0.5037 | -0.0253 | -0.0782 | 0.0300 |  |
| lr | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_ratio | 1 | 938 | not_computed |  |  |  |  |  | None |
| lr | region_tier | selection_rate_ratio | 3 | 579 | not_computed |  |  |  |  |  | None |
| lr | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  | None |
| lr | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  | None |
| lr | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  | None |
| lr | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  | None |
| lr | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | other | 139 | scored | 1.0000 | 0.4110 | 0.5890 | 0.5644 | 0.6134 | 🚩 |
| lr | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.6179 | 0.4110 | 0.2069 | 0.1629 | 0.2520 | 🚩 |
| lr | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_ratio | other | 139 | not_computed |  |  |  |  |  | None |
| lr | employment_type | selection_rate_ratio | self_employed | 759 | not_computed |  |  |  |  |  | None |
| lr | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  | None |
| lr | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  | None |
| lr | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  | None |
| lr | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  | None |
| lr | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | Q1 | 735 | scored | 0.5578 | 0.5064 | 0.0514 | -0.0127 | 0.1145 |  |
| lr | income_band | selection_rate_difference | Q2 | 762 | scored | 0.4856 | 0.5064 | -0.0208 | -0.0841 | 0.0396 |  |
| lr | income_band | selection_rate_difference | Q4 | 721 | scored | 0.4105 | 0.5064 | -0.0959 | -0.1539 | -0.0329 | 🚩 |
| lr | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_ratio | Q1 | 735 | not_computed |  |  |  |  |  | None |
| lr | income_band | selection_rate_ratio | Q2 | 762 | not_computed |  |  |  |  |  | None |
| lr | income_band | selection_rate_ratio | Q4 | 721 | not_computed |  |  |  |  |  | None |
| lr | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  | None |
| lr | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  | None |
| lr | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  | None |
| lr | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  | None |
| lr | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  | None |
| lr | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  | None |
| gb | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | F | 1487 | scored | 0.5239 | 0.5116 | 0.0123 | -0.0245 | 0.0480 |  |
| gb | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_ratio | F | 1487 | not_computed |  |  |  |  |  | None |
| gb | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  | None |
| gb | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  | None |
| gb | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.5299 | 0.5438 | -0.0140 | -0.0750 | 0.0520 |  |
| gb | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.4979 | 0.5438 | -0.0459 | -0.1132 | 0.0225 |  |
| gb | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5000 | 0.5438 | -0.0438 | -0.1070 | 0.0133 |  |
| gb | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | 21-29 | 670 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 30-39 | 723 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 50-59 | 760 | not_computed |  |  |  |  |  | None |
| gb | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  | None |
| gb | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  | None |
| gb | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  | None |
| gb | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  | None |
| gb | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  | None |
| gb | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  | None |
| gb | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  | None |
| gb | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  | None |
| gb | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  | None |
| gb | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_difference | 1 | 938 | scored | 0.4936 | 0.5361 | -0.0425 | -0.0882 | -0.0003 | 🚩 |
| gb | region_tier | selection_rate_difference | 3 | 579 | scored | 0.5095 | 0.5361 | -0.0266 | -0.0811 | 0.0337 |  |
| gb | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_ratio | 1 | 938 | not_computed |  |  |  |  |  | None |
| gb | region_tier | selection_rate_ratio | 3 | 579 | not_computed |  |  |  |  |  | None |
| gb | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  | None |
| gb | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  | None |
| gb | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  | None |
| gb | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  | None |
| gb | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | other | 139 | scored | 1.0000 | 0.4572 | 0.5428 | 0.5188 | 0.5677 | 🚩 |
| gb | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.5968 | 0.4572 | 0.1397 | 0.0907 | 0.1865 | 🚩 |
| gb | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_ratio | other | 139 | not_computed |  |  |  |  |  | None |
| gb | employment_type | selection_rate_ratio | self_employed | 759 | not_computed |  |  |  |  |  | None |
| gb | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  | None |
| gb | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  | None |
| gb | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  | None |
| gb | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  | None |
| gb | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | Q1 | 735 | scored | 0.6204 | 0.5153 | 0.1051 | 0.0438 | 0.1672 | 🚩 |
| gb | income_band | selection_rate_difference | Q2 | 762 | scored | 0.4567 | 0.5153 | -0.0587 | -0.1178 | 0.0026 |  |
| gb | income_band | selection_rate_difference | Q4 | 721 | scored | 0.4799 | 0.5153 | -0.0355 | -0.0947 | 0.0225 |  |
| gb | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_ratio | Q1 | 735 | not_computed |  |  |  |  |  | None |
| gb | income_band | selection_rate_ratio | Q2 | 762 | not_computed |  |  |  |  |  | None |
| gb | income_band | selection_rate_ratio | Q4 | 721 | not_computed |  |  |  |  |  | None |
| gb | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  | None |
| gb | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  | None |
| gb | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  | None |
| gb | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  | None |
| gb | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  | None |
| gb | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  | None |
