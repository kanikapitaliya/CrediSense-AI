"""
Prompt Engineering Templates & Token Optimization for CrediSense AI NL-to-SQL System.
"""

SQL_SCHEMA_PROMPT = """
DATABASE SCHEMA (SQLite):

Table 1: applications
- SK_ID_CURR (INT, PRIMARY KEY): Unique applicant identifier
- TARGET (INT): 0 = Non-Default (Paid on time), 1 = Default (Payment difficulty)
- TARGET_LABEL (TEXT): 'Non-Default' or 'Default'
- NAME_CONTRACT_TYPE (TEXT): 'Cash loans' or 'Revolving loans'
- CODE_GENDER (TEXT): 'M' or 'F'
- FLAG_OWN_CAR (TEXT): 'Y' or 'N'
- FLAG_OWN_REALTY (TEXT): 'Y' or 'N'
- CNT_CHILDREN (INT): Number of children
- AMT_INCOME_TOTAL (FLOAT): Annual income in USD
- AMT_CREDIT (FLOAT): Requested credit amount in USD
- AMT_ANNUITY (FLOAT): Loan annuity payment in USD
- AMT_GOODS_PRICE (FLOAT): Price of goods financed in USD
- NAME_INCOME_TYPE (TEXT): 'Working', 'Commercial associate', 'Pensioner', 'State servant'
- NAME_EDUCATION_TYPE (TEXT): 'Higher education', 'Secondary / secondary special', 'Incomplete higher', 'Lower secondary', 'Academic degree'
- NAME_FAMILY_STATUS (TEXT): Marital status
- NAME_HOUSING_TYPE (TEXT): Housing situation
- AGE_YEARS (FLOAT): Applicant age in years
- EMPLOYMENT_YEARS (FLOAT): Employment duration in years
- ANNUITY_TO_INCOME (FLOAT): Ratio of AMT_ANNUITY / AMT_INCOME_TOTAL
- EXT_SOURCE_MEAN (FLOAT): Composite external risk score (0.0 to 1.0, higher is better creditworthiness)

Table 2: bureau_summary
- SK_ID_CURR (INT, PRIMARY KEY): Foreign key to applications.SK_ID_CURR
- total_bureau_loans (INT): Count of credit bureau records
- active_loans (INT): Count of currently active credit loans
- closed_loans (INT): Count of closed loans
- total_credit_sum (FLOAT): Total credit sum across external bureau loans
- total_debt_sum (FLOAT): Total debt sum across external bureau loans
- max_days_overdue (INT): Maximum overdue days reported across bureau loans

Table 3: previous_applications_summary
- SK_ID_CURR (INT, PRIMARY KEY): Foreign key to applications.SK_ID_CURR
- prev_app_count (INT): Total count of past Home Credit applications
- approved_count (INT): Count of past approved applications
- refused_count (INT): Count of past refused applications
- total_prev_credit (FLOAT): Sum of past approved credit amounts
- avg_prev_credit (FLOAT): Average past credit amount
"""

SYSTEM_NL2SQL_PROMPT = """
You are an expert SQL Translator for CrediSense AI credit risk intelligence platform.
Your ONLY task is to translate natural language user questions into a single valid, read-only SQLite query.

RULES FOR GENERATING SQL:
1. Return ONLY the raw SQL query. Do NOT include markdown code blocks, explanation text, or preambles.
2. The query MUST start with SELECT or WITH.
3. NEVER use destructive commands: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, RENAME, REPLACE, EXEC.
4. Do NOT output multiple SQL statements separated by semicolons.
5. Calculate default rate percentage using `ROUND(AVG(TARGET)*100, 2)` or `ROUND(AVG(a.TARGET)*100, 2)`.
6. Always use valid table names (`applications`, `bureau_summary`, `previous_applications_summary`) and valid column names.
7. Use LIMIT (e.g. LIMIT 10 or LIMIT 20) when requesting individual applicant records or top rankings.
8. If recent conversation context is provided, resolve follow-up references (e.g. "which group", "among those", "show top 5") based on the prior context.
"""

SYSTEM_ANSWER_SUMMARY_PROMPT = """
You are a Credit Risk Analytics Assistant for CrediSense AI.
Your task is to summarize the SQL query results into a concise, professional business insight.

RULES:
1. Base your answer STRICTLY on the provided user question, SQL query, and returned data.
2. Do NOT invent or hallucinate any numbers or facts not present in the returned data.
3. Be concise and structured (2-4 bullet points or short paragraphs).
4. Highlight key figures (default rates, average credit amounts, key category differences).
5. If no records are returned, clearly state that no matching records were found.
"""

def build_sql_generation_prompt(user_question: str, conversation_history: list = None) -> str:
    """
    Formulate concise prompt for Gemini SQL translation incorporating schema and history context.
    """
    history_str = ""
    if conversation_history:
        history_lines = []
        for turn in conversation_history[-3:]:  # Keep last 3 turns for token efficiency
            q = turn.get('question', '')
            sql = turn.get('sql', '')
            history_lines.append(f"User: {q}\nGenerated SQL: {sql}")
        history_str = f"\nRECENT CONVERSATION CONTEXT:\n" + "\n---\n".join(history_lines) + "\n"

    return f"""{SYSTEM_NL2SQL_PROMPT}

{SQL_SCHEMA_PROMPT}
{history_str}
USER QUESTION: {user_question}

SQL QUERY:"""

def build_answer_summary_prompt(user_question: str, sql_query: str, df_data: list) -> str:
    """
    Formulate prompt for Gemini business answer summarization grounded strictly in returned data.
    """
    # Truncate dataset preview to top 15 rows for token control
    sample_data = df_data[:15] if isinstance(df_data, list) else []
    
    return f"""{SYSTEM_ANSWER_SUMMARY_PROMPT}

USER QUESTION: {user_question}
SQL QUERY EXECUTED: {sql_query}

RETURNED DATA (JSON format):
{sample_data}

BUSINESS SUMMARY:"""
