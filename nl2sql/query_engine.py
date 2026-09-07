import os
import json
import re
import pandas as pd
from typing import Dict, Tuple, Optional, List
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from nl2sql.validator import validate_sql_query
from nl2sql.prompts import (
    build_sql_generation_prompt,
    build_answer_summary_prompt,
    SQL_SCHEMA_PROMPT
)
from sql.db_manager import execute_raw_sql

# Import official Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

SCHEMA_DESCRIPTION = SQL_SCHEMA_PROMPT

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

def is_gemini_configured() -> bool:
    """
    Return True if google-genai SDK is installed and valid GEMINI_API_KEY is configured.
    """
    return bool(GENAI_AVAILABLE and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")

def clean_sql_output(raw_text: str) -> str:
    """
    Extract pure SQL string from Gemini response text (stripping markdown code blocks).
    """
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def generate_sql_with_gemini(user_question: str, conversation_history: Optional[List[Dict]] = None) -> Tuple[bool, str, str]:
    """
    Call Gemini API to generate SQL query for natural language question.
    Returns (success, sql_or_error_message, raw_response).
    """
    if not is_gemini_configured():
        return False, "Gemini API key is not configured.", ""

    prompt = build_sql_generation_prompt(user_question, conversation_history)
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model_name = GEMINI_MODEL or "gemini-2.5-flash"
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=300
            )
        )
        
        raw_text = response.text or ""
        sql_query = clean_sql_output(raw_text)
        return True, sql_query, raw_text
    except Exception as e:
        return False, f"Gemini API Error: {str(e)}", ""

def summarize_answer_with_gemini(user_question: str, sql_query: str, df_result: pd.DataFrame) -> Optional[str]:
    """
    Call Gemini API to generate a grounded, natural-language business answer strictly from returned SQL dataframe.
    """
    if not is_gemini_configured() or df_result.empty:
        return None

    records = df_result.to_dict(orient='records')
    prompt = build_answer_summary_prompt(user_question, sql_query, records)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model_name = GEMINI_MODEL or "gemini-2.5-flash"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=400
            )
        )
        return response.text.strip() if response.text else None
    except Exception:
        return None

def format_grounded_answer(sql_query: str, df_result: pd.DataFrame, question: str) -> str:
    """
    Generate a deterministic grounded summary from returned SQL dataframe (fallback).
    """
    if df_result.empty:
        return "No matching records were found in the database for your query."
        
    num_rows = len(df_result)
    cols = df_result.columns.tolist()
    
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

def match_fallback_pattern(user_question: str) -> Dict:
    """
    Deterministic keyword pattern matcher fallback.
    """
    q_lower = user_question.lower().strip()
    for pattern in PRESET_PATTERNS:
        if any(kw in q_lower for kw in pattern["keywords"]):
            return pattern
    return PRESET_PATTERNS[0]

def process_natural_language_query(user_question: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
    """
    Process NL question via Gemini API -> SQL Validation -> Execution -> Grounded Answer.
    Falls back gracefully to deterministic query patterns if API key is missing or call fails.
    """
    # 1. Attempt Gemini LLM Generation if configured
    if is_gemini_configured():
        gemini_success, gen_sql_or_err, raw_resp = generate_sql_with_gemini(user_question, conversation_history)
        
        if gemini_success:
            sql_query = gen_sql_or_err
            is_valid, val_msg = validate_sql_query(sql_query)
            
            if is_valid:
                try:
                    df_res, duration_ms = execute_raw_sql(sql_query)
                    
                    # Generate Gemini grounded answer, or fallback to deterministic summary
                    llm_ans = summarize_answer_with_gemini(user_question, sql_query, df_res)
                    grounded_ans = llm_ans if llm_ans else format_grounded_answer(sql_query, df_res, user_question)
                    
                    return {
                        "question": user_question,
                        "status": "SUCCESS",
                        "sql": sql_query,
                        "execution_time_ms": duration_ms,
                        "row_count": len(df_res),
                        "data": df_res.to_dict(orient='records'),
                        "data_df": df_res,
                        "grounded_answer": grounded_ans,
                        "llm_mode": f"Gemini LLM ({GEMINI_MODEL})",
                        "is_llm": True,
                        "pattern_title": "Gemini Dynamic NL-to-SQL Query"
                    }
                except Exception as e:
                    fallback = match_fallback_pattern(user_question)
                    fallback_sql = fallback["sql"]
                    df_res, duration_ms = execute_raw_sql(fallback_sql)
                    
                    return {
                        "question": user_question,
                        "status": "SUCCESS",
                        "sql": fallback_sql,
                        "execution_time_ms": duration_ms,
                        "row_count": len(df_res),
                        "data": df_res.to_dict(orient='records'),
                        "data_df": df_res,
                        "grounded_answer": format_grounded_answer(fallback_sql, df_res, user_question),
                        "llm_mode": "Deterministic Fallback (Gemini SQL Execution Error)",
                        "is_llm": False,
                        "pattern_title": fallback["title"],
                        "warning": f"Gemini SQL Execution Error: {str(e)}. Used fallback pattern."
                    }
            else:
                fallback = match_fallback_pattern(user_question)
                fallback_sql = fallback["sql"]
                df_res, duration_ms = execute_raw_sql(fallback_sql)
                
                return {
                    "question": user_question,
                    "status": "SUCCESS",
                    "sql": fallback_sql,
                    "execution_time_ms": duration_ms,
                    "row_count": len(df_res),
                    "data": df_res.to_dict(orient='records'),
                    "data_df": df_res,
                    "grounded_answer": format_grounded_answer(fallback_sql, df_res, user_question),
                    "llm_mode": "Deterministic Fallback (Gemini SQL Validation Error)",
                    "is_llm": False,
                    "pattern_title": fallback["title"],
                    "warning": f"Gemini SQL Validation Failed: {val_msg}. Used fallback pattern."
                }
        else:
            fallback = match_fallback_pattern(user_question)
            fallback_sql = fallback["sql"]
            df_res, duration_ms = execute_raw_sql(fallback_sql)
            
            return {
                "question": user_question,
                "status": "SUCCESS",
                "sql": fallback_sql,
                "execution_time_ms": duration_ms,
                "row_count": len(df_res),
                "data": df_res.to_dict(orient='records'),
                "data_df": df_res,
                "grounded_answer": format_grounded_answer(fallback_sql, df_res, user_question),
                "llm_mode": "Deterministic Fallback (Gemini API Call Error)",
                "is_llm": False,
                "pattern_title": fallback["title"],
                "warning": f"{gen_sql_or_err}. Used fallback pattern."
            }

    # 2. Deterministic Pattern Processing (when GEMINI_API_KEY is not configured)
    fallback = match_fallback_pattern(user_question)
    sql_query = fallback["sql"]
    
    is_valid, val_msg = validate_sql_query(sql_query)
    if not is_valid:
        return {
            "question": user_question,
            "status": "REJECTED",
            "error": val_msg,
            "sql": sql_query,
            "data": None,
            "grounded_answer": f"⚠️ SQL Validation Failed: {val_msg}",
            "llm_mode": "Deterministic Verified Pattern (Gemini Key Not Set)",
            "is_llm": False
        }
        
    try:
        df_res, duration_ms = execute_raw_sql(sql_query)
        grounded_ans = format_grounded_answer(sql_query, df_res, user_question)
        
        return {
            "question": user_question,
            "pattern_title": fallback["title"],
            "status": "SUCCESS",
            "sql": sql_query,
            "execution_time_ms": duration_ms,
            "row_count": len(df_res),
            "data": df_res.to_dict(orient='records'),
            "data_df": df_res,
            "grounded_answer": grounded_ans,
            "llm_mode": "Deterministic Verified Pattern (Gemini Key Not Set)",
            "is_llm": False,
            "info": "💡 To enable AI-powered SQL generation, configure GEMINI_API_KEY in your .env file."
        }
    except Exception as e:
        return {
            "question": user_question,
            "status": "ERROR",
            "error": str(e),
            "sql": sql_query,
            "data": None,
            "grounded_answer": f"❌ SQL Execution Error: {str(e)}",
            "llm_mode": "Deterministic Verified Pattern",
            "is_llm": False
        }

if __name__ == '__main__':
    print("Testing NL2SQL Query Engine...")
    print("Is Gemini Configured?:", is_gemini_configured())
    res = process_natural_language_query("What is the default rate by education level?")
    print("Query Mode:", res.get("llm_mode"))
    print("SQL:", res.get("sql"))
    print("Grounded Answer:\n", res.get("grounded_answer"))
