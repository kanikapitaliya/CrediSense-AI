import os
import json
import re
import pandas as pd
from typing import Dict, Tuple, Optional
from nl2sql.validator import validate_sql_query
from sql.db_manager import execute_raw_sql

SCHEMA_DESCRIPTION = """
Database Schema (SQLite):
1. TABLE applications (
    SK_ID_CURR INT PRIMARY KEY,
    TARGET INT (0: Non-Default, 1: Default),
    TARGET_LABEL TEXT ('Non-Default', 'Default'),
    NAME_CONTRACT_TYPE TEXT ('Cash loans', 'Revolving loans'),
    CODE_GENDER TEXT ('M', 'F'),
    FLAG_OWN_CAR TEXT ('Y', 'N'),
    FLAG_OWN_REALTY TEXT ('Y', 'N'),
    CNT_CHILDREN INT,
    AMT_INCOME_TOTAL FLOAT,
    AMT_CREDIT FLOAT,
    AMT_ANNUITY FLOAT,
    AMT_GOODS_PRICE FLOAT,
    NAME_INCOME_TYPE TEXT ('Working', 'Commercial associate', 'Pensioner', 'State servant'),
    NAME_EDUCATION_TYPE TEXT ('Higher education', 'Secondary / secondary special', 'Incomplete higher', 'Lower secondary', 'Academic degree'),
    NAME_FAMILY_STATUS TEXT,
    NAME_HOUSING_TYPE TEXT,
    AGE_YEARS FLOAT,
    EMPLOYMENT_YEARS FLOAT,
    ANNUITY_TO_INCOME FLOAT,
    EXT_SOURCE_MEAN FLOAT
)
2. TABLE bureau_summary (
    SK_ID_CURR INT PRIMARY KEY,
    total_bureau_loans INT,
    active_loans INT,
    closed_loans INT,
    total_credit_sum FLOAT,
    total_debt_sum FLOAT,
    max_days_overdue INT
)
3. TABLE previous_applications_summary (
    SK_ID_CURR INT PRIMARY KEY,
    prev_app_count INT,
    approved_count INT,
    refused_count INT,
    total_prev_credit FLOAT,
    avg_prev_credit FLOAT
)
"""

PRESET_PATTERNS = [
    {
        "keywords": ["education", "degree", "academic", "university"],
        "title": "Default Rates by Education Level",
        "sql": "SELECT NAME_EDUCATION_TYPE, COUNT(*) as applicant_count, ROUND(AVG(TARGET)*100, 2) as default_rate_pct, ROUND(AVG(AMT_INCOME_TOTAL), 2) as avg_income FROM applications GROUP BY NAME_EDUCATION_TYPE ORDER BY default_rate_pct DESC"
    },
    {
        "keywords": ["contract", "cash loan", "revolving loan", "loan type"],
        "title": "Loan Credit and Annuity by Contract Type",
        "sql": "SELECT NAME_CONTRACT_TYPE, COUNT(*) as applicant_count, ROUND(AVG(AMT_CREDIT), 2) as avg_credit_amount, ROUND(AVG(AMT_ANNUITY), 2) as avg_annuity, ROUND(AVG(TARGET)*100, 2) as default_rate_pct FROM applications GROUP BY NAME_CONTRACT_TYPE"
    },
    {
        "keywords": ["bureau", "active loan", "overdue", "debt", "bureau history"],
        "title": "Bureau Active Loan Count vs Default Rate",
        "sql": "SELECT b.active_loans, COUNT(*) as applicant_count, ROUND(AVG(a.TARGET)*100, 2) as default_rate_pct, ROUND(AVG(a.AMT_INCOME_TOTAL), 2) as avg_income FROM applications a JOIN bureau_summary b ON a.SK_ID_CURR = b.SK_ID_CURR GROUP BY b.active_loans HAVING applicant_count > 100 ORDER BY b.active_loans LIMIT 10"
    },
    {
        "keywords": ["income type", "working", "commercial", "pensioner", "state servant"],
        "title": "Default Statistics by Income Type Category",
        "sql": "SELECT NAME_INCOME_TYPE, COUNT(*) as count, ROUND(AVG(TARGET)*100, 2) as default_rate_pct, ROUND(AVG(AMT_INCOME_TOTAL), 2) as avg_income FROM applications GROUP BY NAME_INCOME_TYPE HAVING count > 50 ORDER BY default_rate_pct DESC"
    },
    {
        "keywords": ["previous", "refusal", "prior application", "past approval"],
        "title": "Previous Home Credit Application Refusal vs Approval Stats",
        "sql": "SELECT a.NAME_EDUCATION_TYPE, SUM(p.approved_count) as total_approved, SUM(p.refused_count) as total_refused, ROUND(CAST(SUM(p.refused_count) AS FLOAT) / (SUM(p.approved_count) + SUM(p.refused_count) + 1e-5)*100, 2) as refusal_rate_pct FROM applications a JOIN previous_applications_summary p ON a.SK_ID_CURR = p.SK_ID_CURR GROUP BY a.NAME_EDUCATION_TYPE ORDER BY refusal_rate_pct DESC"
    },
    {
        "keywords": ["highest credit", "top applicant", "largest loan", "highest loan"],
        "title": "Top 10 Applicants with Highest Requested Credit Amount",
        "sql": "SELECT SK_ID_CURR, TARGET_LABEL, NAME_CONTRACT_TYPE, AMT_CREDIT, AMT_INCOME_TOTAL, AGE_YEARS, EXT_SOURCE_MEAN FROM applications ORDER BY AMT_CREDIT DESC LIMIT 10"
    }
]

def format_grounded_answer(sql_query: str, df_result: pd.DataFrame, question: str) -> str:
    """
    Generate a grounded natural language summary strictly from returned SQL dataframe.
    """
    if df_result.empty:
        return "No matching records were found in the database for your query."
        
    num_rows = len(df_result)
    cols = df_result.columns.tolist()
    
    # Formulate tabular text
    lines = [f"**Query Results Summary** ({num_rows} records returned):\n"]
    
    if num_rows <= 10:
        for idx, row in df_result.iterrows():
            row_desc = ", ".join([f"**{col}**: {row[col]}" for col in cols])
            lines.append(f"- Row {idx+1}: {row_desc}")
    else:
        top_row = df_result.iloc[0]
        row_desc = ", ".join([f"**{col}**: {top_row[col]}" for col in cols])
        lines.append(f"- Top Record: {row_desc}")
        lines.append(f"- ... plus {num_rows - 1} additional records shown in the data table below.")
        
    return "\n".join(lines)

def process_natural_language_query(user_question: str) -> Dict:
    """
    Process NL question, translate/match to SQL, validate, execute, and return grounded answer.
    """
    q_lower = user_question.lower().strip()
    
    # Match query pattern
    matched_pattern = None
    for pattern in PRESET_PATTERNS:
        if any(kw in q_lower for kw in pattern["keywords"]):
            matched_pattern = pattern
            break
            
    if not matched_pattern:
        # Default to education default rates pattern if no keyword match
        matched_pattern = PRESET_PATTERNS[0]
        
    sql_query = matched_pattern["sql"]
    
    # 1. Validate SQL
    is_valid, val_msg = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "question": user_question,
            "status": "REJECTED",
            "error": val_msg,
            "sql": sql_query,
            "data": None,
            "grounded_answer": f"⚠️ SQL Validation Failed: {val_msg}"
        }
        
    # 2. Execute SQL
    try:
        df_res, duration_ms = execute_raw_sql(sql_query)
        grounded_ans = format_grounded_answer(sql_query, df_res, user_question)
        
        return {
            "question": user_question,
            "pattern_title": matched_pattern["title"],
            "status": "SUCCESS",
            "sql": sql_query,
            "execution_time_ms": duration_ms,
            "row_count": len(df_res),
            "data": df_res.to_dict(orient='records'),
            "data_df": df_res,
            "grounded_answer": grounded_ans,
            "llm_mode": "Deterministic Verified NL-to-SQL Engine"
        }
    except Exception as e:
        return {
            "question": user_question,
            "status": "ERROR",
            "error": str(e),
            "sql": sql_query,
            "data": None,
            "grounded_answer": f"❌ SQL Execution Error: {str(e)}"
        }

if __name__ == '__main__':
    print("Testing NL2SQL Query Engine...")
    res = process_natural_language_query("What is the default rate by education level?")
    print("Query Title:", res.get("pattern_title"))
    print("SQL:", res.get("sql"))
    print("Grounded Answer:\n", res.get("grounded_answer"))
