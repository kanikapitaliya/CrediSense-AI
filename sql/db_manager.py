import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from config.settings import DB_PATH, DATASETS_DIR
from data.loader import load_application_train, load_bureau, load_previous_application

def get_db_connection() -> sqlite3.Connection:
    """
    Get SQLite database connection.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(sample_rows: int = 50000) -> Dict:
    """
    Initialize queryable SQLite database populated with application and historical metrics.
    """
    print(f"--- Phase 10: Building Database Layer ({DB_PATH}) ---")
    conn = get_db_connection()
    
    # 1. Load Application Train
    print("Loading applications for SQL database...")
    df_app = load_application_train(nrows=sample_rows)
    
    # Pre-calculate derived display columns for SQL queries
    df_app = df_app.assign(
        AGE_YEARS=(np.abs(df_app['DAYS_BIRTH']) / 365.25).round(1),
        EMPLOYMENT_YEARS=np.where(df_app['DAYS_EMPLOYED'] > 0, np.nan, np.abs(df_app['DAYS_EMPLOYED']) / 365.25).round(1),
        ANNUITY_TO_INCOME=(df_app['AMT_ANNUITY'] / (df_app['AMT_INCOME_TOTAL'] + 1e-5)).round(4),
        EXT_SOURCE_MEAN=df_app[['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']].mean(axis=1).round(4),
        TARGET_LABEL=df_app['TARGET'].map({0: 'Non-Default', 1: 'Default'})
    )
    
    # Select key clean columns for applications table
    app_sql_cols = [
        'SK_ID_CURR', 'TARGET', 'TARGET_LABEL', 'NAME_CONTRACT_TYPE', 'CODE_GENDER',
        'FLAG_OWN_CAR', 'FLAG_OWN_REALTY', 'CNT_CHILDREN', 'AMT_INCOME_TOTAL',
        'AMT_CREDIT', 'AMT_ANNUITY', 'AMT_GOODS_PRICE', 'NAME_INCOME_TYPE',
        'NAME_EDUCATION_TYPE', 'NAME_FAMILY_STATUS', 'NAME_HOUSING_TYPE',
        'AGE_YEARS', 'EMPLOYMENT_YEARS', 'ANNUITY_TO_INCOME', 'EXT_SOURCE_MEAN'
    ]
    
    clean_app_df = df_app[app_sql_cols].copy()
    clean_app_df.to_sql('applications', conn, if_exists='replace', index=False)
    
    # 2. Load Bureau Summary
    print("Loading bureau records for SQL database...")
    df_bureau = load_bureau(nrows=100000)
    bureau_summary = df_bureau.groupby('SK_ID_CURR').agg(
        total_bureau_loans=('SK_ID_BUREAU', 'count'),
        active_loans=('CREDIT_ACTIVE', lambda x: (x == 'Active').sum()),
        closed_loans=('CREDIT_ACTIVE', lambda x: (x == 'Closed').sum()),
        total_credit_sum=('AMT_CREDIT_SUM', 'sum'),
        total_debt_sum=('AMT_CREDIT_SUM_DEBT', 'sum'),
        max_days_overdue=('CREDIT_DAY_OVERDUE', 'max')
    ).reset_index()
    bureau_summary.to_sql('bureau_summary', conn, if_exists='replace', index=False)
    
    # 3. Load Previous Applications Summary
    print("Loading previous applications for SQL database...")
    df_prev = load_previous_application(nrows=100000)
    prev_summary = df_prev.groupby('SK_ID_CURR').agg(
        prev_app_count=('SK_ID_PREV', 'count'),
        approved_count=('NAME_CONTRACT_STATUS', lambda x: (x == 'Approved').sum()),
        refused_count=('NAME_CONTRACT_STATUS', lambda x: (x == 'Refused').sum()),
        total_prev_credit=('AMT_CREDIT', 'sum'),
        avg_prev_credit=('AMT_CREDIT', 'mean')
    ).reset_index()
    prev_summary.to_sql('previous_applications_summary', conn, if_exists='replace', index=False)
    
    # Create indexes for high-speed queries
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_curr ON applications(SK_ID_CURR);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_target ON applications(TARGET);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_edu ON applications(NAME_EDUCATION_TYPE);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bureau_curr ON bureau_summary(SK_ID_CURR);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prev_curr ON previous_applications_summary(SK_ID_CURR);")
    conn.commit()
    
    summary = {
        "db_path": str(DB_PATH),
        "tables": {
            "applications": len(clean_app_df),
            "bureau_summary": len(bureau_summary),
            "previous_applications_summary": len(prev_summary)
        }
    }
    conn.close()
    print(f"Database initialized successfully: {summary}")
    return summary

def execute_raw_sql(sql_query: str) -> Tuple[pd.DataFrame, float]:
    """
    Execute read-only SQL query against database and return (DataFrame, duration_ms).
    """
    import time
    conn = get_db_connection()
    start_time = time.time()
    try:
        df = pd.read_sql_query(sql_query, conn)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return df, duration_ms
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()
    df, dur = execute_raw_sql("SELECT NAME_EDUCATION_TYPE, COUNT(*) as count, AVG(TARGET)*100 as default_pct FROM applications GROUP BY NAME_EDUCATION_TYPE ORDER BY default_pct DESC")
    print(f"Sample Query Output ({dur} ms):\n{df}")
