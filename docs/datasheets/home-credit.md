# Home Credit Default Risk: Dataset Datasheet

## Source

The dataset originates from the Home Credit Default Risk competition hosted on Kaggle (https://www.kaggle.com/competitions/home-credit-default-risk), published by Home Credit Group to challenge the data science community to unlock the full potential of their credit data. It comprises historical loan applications and credit bureau records.

## Motivation

Home Credit strives to broaden financial inclusion for the unbanked population by providing a positive and safe borrowing experience. The dataset was published to benchmark statistical and machine learning methods for predicting repayment abilities of clients with little or no credit history.

## Composition

The dataset contains tabular records across several relational files: `application_train.csv` (307,511 applicant rows with 122 features including TARGET), `bureau.csv` (1,716,428 historical credit records from external credit bureaus), and `bureau_balance.csv` (27,299,926 monthly status records). The target represents payment difficulty or default (1 if client had payment difficulties, 0 otherwise).

## Known limits

Data reflects an unbanked/underbanked consumer loan portfolio outside India, denominated in local currency without currency conversion to INR. Loan amounts and incomes do not match Indian personal loan policy bounds directly. External credit scores (`EXT_SOURCE_1/2/3`) and bureau variables require domain assumptions (ASM-D1 to ASM-D13) to map to an Indian banking fact schema.

## Licence and terms

Source page: https://www.kaggle.com/competitions/home-credit-default-risk/rules. Rules accepted on: 2026-11-11. Use for coursework or non-commercial research: allowed. Clause quoted: "After your acceptance of these Rules, you may access and use the Competition Data" and "solely for academic research and education programs, or for the purpose of participating in the Competition." Redistribution of the data: Prohibited. You may not share, publish, or redistribute the Competition Data without prior written consent of Kaggle and the Competition Sponsor. Other restrictions: Non-commercial academic research and coursework only. Data must not be copied or distributed to third parties. Citation to Home Credit Default Risk competition on Kaggle required in publications.

## Intended use

Used exclusively as an academic comparison benchmark (dataset D2) to evaluate the expert system rules and machine learning baselines on realistic credit bureau structures, and to assess alignment with default risk without using protected attributes in decisioning.

