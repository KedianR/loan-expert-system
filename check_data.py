import csv
checks = {
    r"data\raw\application_train.csv": ["SK_ID_CURR", "TARGET", "CODE_GENDER", "DAYS_BIRTH", "DAYS_EMPLOYED", "NAME_INCOME_TYPE", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3", "AMT_REQ_CREDIT_BUREAU_MON", "AMT_REQ_CREDIT_BUREAU_QRT", "REGION_RATING_CLIENT", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS"],
    r"data\raw\bureau.csv": ["CREDIT_ACTIVE", "AMT_ANNUITY"],
    r"data\raw\bureau_balance.csv": ["STATUS", "MONTHS_BALANCE"]
}
for path, expected in checks.items():
    print(f"\nChecking {path}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            missing = [c for c in expected if c not in header]
            print(f"Columns: {len(header)}")
            if missing: print(f"Missing columns: {missing}")
            else: print("All expected columns found.")
            rows = sum(1 for row in reader)
            print(f"Rows: {rows:,}")
    except Exception as e:
        print(f"Error: {e}")
