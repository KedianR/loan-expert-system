# Fairness Tables — D3

> Limits from docs/fairness-audit-plan.md section 1 apply to all findings.
> Groups shown as 'too_small' (< 100) or 'unstable' (< 20 events) are not findings.

## Treatment A (refer = not approved)

| System | Attribute | Metric | Group | Size | Status | Rate | Ref Rate | Diff | CI Low | CI High | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_system | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_difference | F | 1487 | scored | 0.4620 | 0.4825 | -0.0205 | -0.0576 | 0.0159 |  |
| rule_system | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_ratio | F | 1487 | scored | 0.4620 | 0.4825 | 0.9576 |  |  |  |
| rule_system | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4657 | 0.4446 | 0.0211 | -0.0472 | 0.0835 |  |
| rule_system | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.4896 | 0.4446 | 0.0450 | -0.0232 | 0.1082 |  |
| rule_system | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.4895 | 0.4446 | 0.0449 | -0.0130 | 0.1095 |  |
| rule_system | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.4657 | 0.4446 | 1.0474 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.4896 | 0.4446 | 1.1013 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.4895 | 0.4446 | 1.1010 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_difference | 1 | 938 | scored | 0.4893 | 0.4579 | 0.0315 | -0.0098 | 0.0787 |  |
| rule_system | region_tier | selection_rate_difference | 3 | 579 | scored | 0.4819 | 0.4579 | 0.0240 | -0.0365 | 0.0763 |  |
| rule_system | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.4893 | 0.4579 | 1.0688 |  |  |  |
| rule_system | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.4819 | 0.4579 | 1.0524 |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5324 | -0.5324 |  |  |  |
| rule_system | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.3926 | 0.5323 | -0.1397 | -0.1876 | -0.0912 | 🚩 |
| rule_system | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5324 | 0.0000 |  |  |  |
| rule_system | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.3926 | 0.5323 | 0.7375 |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | Q1 | 735 | scored | 0.3687 | 0.4808 | -0.1121 | -0.1724 | -0.0556 | 🚩 |
| rule_system | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5354 | 0.4808 | 0.0546 | -0.0082 | 0.1168 |  |
| rule_system | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5021 | 0.4808 | 0.0213 | -0.0392 | 0.0809 |  |
| rule_system | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.3687 | 0.4808 | 0.7668 |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5354 | 0.4808 | 1.1136 |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5021 | 0.4808 | 1.0442 |  |  |  |
| rule_system | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4557 | 0.4383 | 0.0174 | -0.0947 | 0.1178 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.4680 | 0.4383 | 0.0297 | -0.0650 | 0.1206 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.4827 | 0.4383 | 0.0444 | -0.0581 | 0.1462 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.4746 | 0.4383 | 0.0363 | -0.0679 | 0.1324 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5110 | 0.4383 | 0.0727 | -0.0189 | 0.1715 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.4512 | 0.4383 | 0.0129 | -0.0800 | 0.1138 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.4961 | 0.4383 | 0.0578 | -0.0392 | 0.1616 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4557 | 0.4383 | 1.0397 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.4680 | 0.4383 | 1.0677 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.4827 | 0.4383 | 1.1013 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.4746 | 0.4383 | 1.0828 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5110 | 0.4383 | 1.1659 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.4512 | 0.4383 | 1.0294 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.4961 | 0.4383 | 1.1319 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | F | 1487 | scored | 0.4963 | 0.5221 | -0.0258 | -0.0600 | 0.0108 |  |
| lr | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_ratio | F | 1487 | scored | 0.4963 | 0.5221 | 0.9505 |  |  |  |
| lr | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4567 | 0.5103 | -0.0536 | -0.1177 | 0.0118 |  |
| lr | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.5311 | 0.5103 | 0.0208 | -0.0425 | 0.0897 |  |
| lr | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5355 | 0.5103 | 0.0252 | -0.0310 | 0.0936 |  |
| lr | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.4567 | 0.5103 | 0.8950 |  |  |  |
| lr | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.5311 | 0.5103 | 1.0408 |  |  |  |
| lr | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.5355 | 0.5103 | 1.0494 |  |  |  |
| lr | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_difference | 1 | 938 | scored | 0.5224 | 0.4963 | 0.0261 | -0.0193 | 0.0722 |  |
| lr | region_tier | selection_rate_difference | 3 | 579 | scored | 0.5216 | 0.4963 | 0.0253 | -0.0300 | 0.0782 |  |
| lr | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.5224 | 0.4963 | 1.0526 |  |  |  |
| lr | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.5216 | 0.4963 | 1.0510 |  |  |  |
| lr | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| lr | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5890 | -0.5890 |  |  |  |
| lr | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.3821 | 0.5890 | -0.2069 | -0.2520 | -0.1629 | 🚩 |
| lr | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5890 | 0.0000 |  |  |  |
| lr | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.3821 | 0.5890 | 0.6487 |  |  |  |
| lr | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | Q1 | 735 | scored | 0.4422 | 0.4936 | -0.0514 | -0.1145 | 0.0127 |  |
| lr | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5144 | 0.4936 | 0.0208 | -0.0396 | 0.0841 |  |
| lr | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5895 | 0.4936 | 0.0959 | 0.0329 | 0.1539 | 🚩 |
| lr | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.4422 | 0.4936 | 0.8958 |  |  |  |
| lr | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5144 | 0.4936 | 1.0422 |  |  |  |
| lr | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5895 | 0.4936 | 1.1942 |  |  |  |
| lr | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4557 | 0.5088 | -0.0531 | -0.1596 | 0.0433 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.4958 | 0.5088 | -0.0130 | -0.1122 | 0.0890 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.5147 | 0.5088 | 0.0059 | -0.0867 | 0.1006 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.4576 | 0.5088 | -0.0512 | -0.1505 | 0.0506 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5659 | 0.5088 | 0.0571 | -0.0430 | 0.1496 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.5119 | 0.5088 | 0.0031 | -0.0966 | 0.0953 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.5558 | 0.5088 | 0.0470 | -0.0564 | 0.1405 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4557 | 0.5088 | 0.8956 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.4958 | 0.5088 | 0.9745 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.5147 | 0.5088 | 1.0115 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.4576 | 0.5088 | 0.8994 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5659 | 0.5088 | 1.1123 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.5119 | 0.5088 | 1.0060 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.5558 | 0.5088 | 1.0924 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | F | 1487 | scored | 0.4761 | 0.4884 | -0.0123 | -0.0480 | 0.0245 |  |
| gb | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_ratio | F | 1487 | scored | 0.4761 | 0.4884 | 0.9748 |  |  |  |
| gb | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4701 | 0.4562 | 0.0140 | -0.0520 | 0.0750 |  |
| gb | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.5021 | 0.4562 | 0.0459 | -0.0225 | 0.1132 |  |
| gb | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5000 | 0.4562 | 0.0438 | -0.0133 | 0.1070 |  |
| gb | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.4701 | 0.4562 | 1.0306 |  |  |  |
| gb | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.5021 | 0.4562 | 1.1006 |  |  |  |
| gb | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.5000 | 0.4562 | 1.0960 |  |  |  |
| gb | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_difference | 1 | 938 | scored | 0.5064 | 0.4639 | 0.0425 | 0.0003 | 0.0882 | 🚩 |
| gb | region_tier | selection_rate_difference | 3 | 579 | scored | 0.4905 | 0.4639 | 0.0266 | -0.0337 | 0.0811 |  |
| gb | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.5064 | 0.4639 | 1.0916 |  |  |  |
| gb | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.4905 | 0.4639 | 1.0573 |  |  |  |
| gb | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| gb | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5428 | -0.5428 |  |  |  |
| gb | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.4032 | 0.5428 | -0.1397 | -0.1865 | -0.0907 | 🚩 |
| gb | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5428 | 0.0000 |  |  |  |
| gb | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.4032 | 0.5428 | 0.7427 |  |  |  |
| gb | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | Q1 | 735 | scored | 0.3796 | 0.4847 | -0.1051 | -0.1672 | -0.0438 | 🚩 |
| gb | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5433 | 0.4847 | 0.0587 | -0.0026 | 0.1178 |  |
| gb | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5201 | 0.4847 | 0.0355 | -0.0225 | 0.0947 |  |
| gb | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.3796 | 0.4847 | 0.7832 |  |  |  |
| gb | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5433 | 0.4847 | 1.1210 |  |  |  |
| gb | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5201 | 0.4847 | 1.0732 |  |  |  |
| gb | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4557 | 0.4559 | -0.0002 | -0.1148 | 0.1034 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.4847 | 0.4559 | 0.0288 | -0.0644 | 0.1217 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.5013 | 0.4559 | 0.0454 | -0.0631 | 0.1436 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.4831 | 0.4559 | 0.0271 | -0.0729 | 0.1315 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5192 | 0.4559 | 0.0633 | -0.0277 | 0.1616 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.4565 | 0.4559 | 0.0005 | -0.0897 | 0.1003 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.4987 | 0.4559 | 0.0428 | -0.0542 | 0.1485 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4557 | 0.4559 | 0.9995 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.4847 | 0.4559 | 1.0631 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.5013 | 0.4559 | 1.0996 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.4831 | 0.4559 | 1.0595 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5192 | 0.4559 | 1.1389 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.4565 | 0.4559 | 1.0012 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.4987 | 0.4559 | 1.0938 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |

## Treatment B (refer rows excluded)

> Note: ML baseline models produce binary eligible/ineligible decisions with no referral state, so Treatment B is identical to Treatment A for ML models. Rule system results exclude REFER cases.

| System | Attribute | Metric | Group | Size | Status | Rate | Ref Rate | Diff | CI Low | CI High | Flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rule_system | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_difference | F | 1487 | scored | 0.5022 | 0.5259 | -0.0237 | -0.0631 | 0.0137 |  |
| rule_system | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | selection_rate_ratio | F | 1487 | scored | 0.5022 | 0.5259 | 0.9549 |  |  |  |
| rule_system | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| rule_system | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.5016 | 0.4880 | 0.0136 | -0.0596 | 0.0774 |  |
| rule_system | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.5315 | 0.4880 | 0.0436 | -0.0285 | 0.1109 |  |
| rule_system | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5345 | 0.4880 | 0.0465 | -0.0148 | 0.1124 |  |
| rule_system | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.5016 | 0.4880 | 1.0279 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.5315 | 0.4880 | 1.0893 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.5345 | 0.4880 | 1.0953 |  |  |  |
| rule_system | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| rule_system | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| rule_system | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_difference | 1 | 938 | scored | 0.5319 | 0.4978 | 0.0341 | -0.0123 | 0.0805 |  |
| rule_system | region_tier | selection_rate_difference | 3 | 579 | scored | 0.5274 | 0.4978 | 0.0296 | -0.0339 | 0.0825 |  |
| rule_system | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.5319 | 0.4978 | 1.0684 |  |  |  |
| rule_system | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.5274 | 0.4978 | 1.0595 |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| rule_system | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5632 | -0.5632 |  |  |  |
| rule_system | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.4088 | 0.5632 | -0.1544 | -0.2029 | -0.1043 | 🚩 |
| rule_system | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5632 | 0.0000 |  |  |  |
| rule_system | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.4088 | 0.5632 | 0.7259 |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| rule_system | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_difference | Q1 | 735 | scored | 0.3945 | 0.5288 | -0.1344 | -0.1944 | -0.0720 | 🚩 |
| rule_system | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5804 | 0.5288 | 0.0515 | -0.0090 | 0.1113 |  |
| rule_system | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5527 | 0.5288 | 0.0238 | -0.0348 | 0.0841 |  |
| rule_system | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.3945 | 0.5288 | 0.7459 |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5804 | 0.5288 | 1.0975 |  |  |  |
| rule_system | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5527 | 0.5288 | 1.0451 |  |  |  |
| rule_system | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| rule_system | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| rule_system | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4881 | 0.4754 | 0.0127 | -0.0991 | 0.1159 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.5122 | 0.4754 | 0.0368 | -0.0611 | 0.1307 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.5292 | 0.4754 | 0.0538 | -0.0496 | 0.1638 |  |
| rule_system | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.5138 | 0.4754 | 0.0384 | -0.0684 | 0.1398 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5503 | 0.4754 | 0.0749 | -0.0230 | 0.1791 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.5015 | 0.4754 | 0.0261 | -0.0732 | 0.1328 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.5395 | 0.4754 | 0.0641 | -0.0355 | 0.1699 |  |
| rule_system | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4881 | 0.4754 | 1.0268 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.5122 | 0.4754 | 1.0774 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.5292 | 0.4754 | 1.1132 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.5138 | 0.4754 | 1.0807 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5503 | 0.4754 | 1.1575 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.5015 | 0.4754 | 1.0548 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.5395 | 0.4754 | 1.1349 |  |  |  |
| rule_system | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| rule_system | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_difference | F | 1487 | scored | 0.4963 | 0.5221 | -0.0258 | -0.0600 | 0.0108 |  |
| lr | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | selection_rate_ratio | F | 1487 | scored | 0.4963 | 0.5221 | 0.9505 |  |  |  |
| lr | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| lr | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4567 | 0.5103 | -0.0536 | -0.1177 | 0.0118 |  |
| lr | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.5311 | 0.5103 | 0.0208 | -0.0425 | 0.0897 |  |
| lr | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5355 | 0.5103 | 0.0252 | -0.0310 | 0.0936 |  |
| lr | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.4567 | 0.5103 | 0.8950 |  |  |  |
| lr | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.5311 | 0.5103 | 1.0408 |  |  |  |
| lr | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.5355 | 0.5103 | 1.0494 |  |  |  |
| lr | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| lr | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| lr | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| lr | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_difference | 1 | 938 | scored | 0.5224 | 0.4963 | 0.0261 | -0.0193 | 0.0722 |  |
| lr | region_tier | selection_rate_difference | 3 | 579 | scored | 0.5216 | 0.4963 | 0.0253 | -0.0300 | 0.0782 |  |
| lr | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.5224 | 0.4963 | 1.0526 |  |  |  |
| lr | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.5216 | 0.4963 | 1.0510 |  |  |  |
| lr | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| lr | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| lr | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5890 | -0.5890 |  |  |  |
| lr | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.3821 | 0.5890 | -0.2069 | -0.2520 | -0.1629 | 🚩 |
| lr | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5890 | 0.0000 |  |  |  |
| lr | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.3821 | 0.5890 | 0.6487 |  |  |  |
| lr | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| lr | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| lr | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_difference | Q1 | 735 | scored | 0.4422 | 0.4936 | -0.0514 | -0.1145 | 0.0127 |  |
| lr | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5144 | 0.4936 | 0.0208 | -0.0396 | 0.0841 |  |
| lr | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5895 | 0.4936 | 0.0959 | 0.0329 | 0.1539 | 🚩 |
| lr | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.4422 | 0.4936 | 0.8958 |  |  |  |
| lr | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5144 | 0.4936 | 1.0422 |  |  |  |
| lr | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5895 | 0.4936 | 1.1942 |  |  |  |
| lr | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| lr | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| lr | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4557 | 0.5088 | -0.0531 | -0.1596 | 0.0433 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.4958 | 0.5088 | -0.0130 | -0.1122 | 0.0890 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.5147 | 0.5088 | 0.0059 | -0.0867 | 0.1006 |  |
| lr | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.4576 | 0.5088 | -0.0512 | -0.1505 | 0.0506 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5659 | 0.5088 | 0.0571 | -0.0430 | 0.1496 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.5119 | 0.5088 | 0.0031 | -0.0966 | 0.0953 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.5558 | 0.5088 | 0.0470 | -0.0564 | 0.1405 |  |
| lr | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4557 | 0.5088 | 0.8956 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.4958 | 0.5088 | 0.9745 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.5147 | 0.5088 | 1.0115 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.4576 | 0.5088 | 0.8994 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5659 | 0.5088 | 1.1123 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.5119 | 0.5088 | 1.0060 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.5558 | 0.5088 | 1.0924 |  |  |  |
| lr | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| lr | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_difference | F | 1487 | scored | 0.4761 | 0.4884 | -0.0123 | -0.0480 | 0.0245 |  |
| gb | gender | selection_rate_ratio | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | selection_rate_ratio | F | 1487 | scored | 0.4761 | 0.4884 | 0.9748 |  |  |  |
| gb | gender | false_approval_rate_difference | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | false_approval_rate_difference | F | 1487 | no_target |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | **M** (ref) | 1513 | reference |  |  |  |  |  |  |
| gb | gender | default_rate_among_approved | F | 1487 | no_target |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_difference | 21-29 | 670 | scored | 0.4701 | 0.4562 | 0.0140 | -0.0520 | 0.0750 |  |
| gb | age_band | selection_rate_difference | 30-39 | 723 | scored | 0.5021 | 0.4562 | 0.0459 | -0.0225 | 0.1132 |  |
| gb | age_band | selection_rate_difference | 50-59 | 760 | scored | 0.5000 | 0.4562 | 0.0438 | -0.0133 | 0.1070 |  |
| gb | age_band | selection_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | selection_rate_ratio | 21-29 | 670 | scored | 0.4701 | 0.4562 | 1.0306 |  |  |  |
| gb | age_band | selection_rate_ratio | 30-39 | 723 | scored | 0.5021 | 0.4562 | 1.1006 |  |  |  |
| gb | age_band | selection_rate_ratio | 50-59 | 760 | scored | 0.5000 | 0.4562 | 1.0960 |  |  |  |
| gb | age_band | selection_rate_ratio | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 21-29 | 670 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 30-39 | 723 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 50-59 | 760 | no_target |  |  |  |  |  |  |
| gb | age_band | false_approval_rate_difference | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | **40-49** (ref) | 776 | reference |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 21-29 | 670 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 30-39 | 723 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 50-59 | 760 | no_target |  |  |  |  |  |  |
| gb | age_band | default_rate_among_approved | 60+ | 71 | too_small |  |  |  |  |  |  |
| gb | region_tier | selection_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_difference | 1 | 938 | scored | 0.5064 | 0.4639 | 0.0425 | 0.0003 | 0.0882 | 🚩 |
| gb | region_tier | selection_rate_difference | 3 | 579 | scored | 0.4905 | 0.4639 | 0.0266 | -0.0337 | 0.0811 |  |
| gb | region_tier | selection_rate_ratio | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | selection_rate_ratio | 1 | 938 | scored | 0.5064 | 0.4639 | 1.0916 |  |  |  |
| gb | region_tier | selection_rate_ratio | 3 | 579 | scored | 0.4905 | 0.4639 | 1.0573 |  |  |  |
| gb | region_tier | false_approval_rate_difference | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | false_approval_rate_difference | 1 | 938 | no_target |  |  |  |  |  |  |
| gb | region_tier | false_approval_rate_difference | 3 | 579 | no_target |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | **2** (ref) | 1483 | reference |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | 1 | 938 | no_target |  |  |  |  |  |  |
| gb | region_tier | default_rate_among_approved | 3 | 579 | no_target |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_difference | other | 139 | unstable | 0.0000 | 0.5428 | -0.5428 |  |  |  |
| gb | employment_type | selection_rate_difference | self_employed | 759 | scored | 0.4032 | 0.5428 | -0.1397 | -0.1865 | -0.0907 | 🚩 |
| gb | employment_type | selection_rate_ratio | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | selection_rate_ratio | other | 139 | unstable | 0.0000 | 0.5428 | 0.0000 |  |  |  |
| gb | employment_type | selection_rate_ratio | self_employed | 759 | scored | 0.4032 | 0.5428 | 0.7427 |  |  |  |
| gb | employment_type | false_approval_rate_difference | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | other | 139 | no_target |  |  |  |  |  |  |
| gb | employment_type | false_approval_rate_difference | self_employed | 759 | no_target |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | **salaried** (ref) | 2102 | reference |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | other | 139 | no_target |  |  |  |  |  |  |
| gb | employment_type | default_rate_among_approved | self_employed | 759 | no_target |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_difference | Q1 | 735 | scored | 0.3796 | 0.4847 | -0.1051 | -0.1672 | -0.0438 | 🚩 |
| gb | income_band | selection_rate_difference | Q2 | 762 | scored | 0.5433 | 0.4847 | 0.0587 | -0.0026 | 0.1178 |  |
| gb | income_band | selection_rate_difference | Q4 | 721 | scored | 0.5201 | 0.4847 | 0.0355 | -0.0225 | 0.0947 |  |
| gb | income_band | selection_rate_ratio | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | selection_rate_ratio | Q1 | 735 | scored | 0.3796 | 0.4847 | 0.7832 |  |  |  |
| gb | income_band | selection_rate_ratio | Q2 | 762 | scored | 0.5433 | 0.4847 | 1.1210 |  |  |  |
| gb | income_band | selection_rate_ratio | Q4 | 721 | scored | 0.5201 | 0.4847 | 1.0732 |  |  |  |
| gb | income_band | false_approval_rate_difference | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q1 | 735 | no_target |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q2 | 762 | no_target |  |  |  |  |  |  |
| gb | income_band | false_approval_rate_difference | Q4 | 721 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | **Q3** (ref) | 782 | reference |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q1 | 735 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q2 | 762 | no_target |  |  |  |  |  |  |
| gb | income_band | default_rate_among_approved | Q4 | 721 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | F x 21-29 | 316 | scored | 0.4557 | 0.4559 | -0.0002 | -0.1148 | 0.1034 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 30-39 | 359 | scored | 0.4847 | 0.4559 | 0.0288 | -0.0644 | 0.1217 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 50-59 | 375 | scored | 0.5013 | 0.4559 | 0.0454 | -0.0631 | 0.1436 |  |
| gb | gender_x_age_band | selection_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_difference | M x 21-29 | 354 | scored | 0.4831 | 0.4559 | 0.0271 | -0.0729 | 0.1315 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 30-39 | 364 | scored | 0.5192 | 0.4559 | 0.0633 | -0.0277 | 0.1616 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 40-49 | 379 | scored | 0.4565 | 0.4559 | 0.0005 | -0.0897 | 0.1003 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 50-59 | 385 | scored | 0.4987 | 0.4559 | 0.0428 | -0.0542 | 0.1485 |  |
| gb | gender_x_age_band | selection_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 21-29 | 316 | scored | 0.4557 | 0.4559 | 0.9995 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 30-39 | 359 | scored | 0.4847 | 0.4559 | 1.0631 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 50-59 | 375 | scored | 0.5013 | 0.4559 | 1.0996 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 21-29 | 354 | scored | 0.4831 | 0.4559 | 1.0595 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 30-39 | 364 | scored | 0.5192 | 0.4559 | 1.1389 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 40-49 | 379 | scored | 0.4565 | 0.4559 | 1.0012 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 50-59 | 385 | scored | 0.4987 | 0.4559 | 1.0938 |  |  |  |
| gb | gender_x_age_band | selection_rate_ratio | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | false_approval_rate_difference | M x 60+ | 31 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | **F x 40-49** (ref) | 397 | reference |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 21-29 | 316 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 30-39 | 359 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 50-59 | 375 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | F x 60+ | 40 | too_small |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 21-29 | 354 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 30-39 | 364 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 40-49 | 379 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 50-59 | 385 | no_target |  |  |  |  |  |  |
| gb | gender_x_age_band | default_rate_among_approved | M x 60+ | 31 | too_small |  |  |  |  |  |  |

