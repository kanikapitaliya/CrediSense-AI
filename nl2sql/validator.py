import re
from typing import Tuple
from config.settings import FORBIDDEN_SQL_KEYWORDS, READ_ONLY_ALLOWED_KEYWORDS

ALLOWED_TABLES = {"applications", "bureau_summary", "previous_applications_summary"}

def validate_sql_query(sql_query: str) -> Tuple[bool, str]:
    """
    Validate that an SQL query is strictly a read-only SELECT statement,
    disallow dangerous modifications or multi-statement injections, and check table references.
    """
    if not sql_query or not sql_query.strip():
        return False, "Empty SQL query provided."
        
    cleaned_query = sql_query.strip()
    
    # Check for multiple statements separated by semicolon
    if ";" in cleaned_query[:-1]:
        return False, "Security Violation: Multiple SQL statements separated by semicolon ';' are prohibited."
        
    # Remove trailing semicolon
    cleaned_query = cleaned_query.rstrip(";").strip()
    
    # Tokens extraction (uppercase)
    tokens = [t.upper() for t in re.findall(r'\b[A-Za-z0-9_]+\b', cleaned_query)]
    if not tokens:
        return False, "Invalid SQL syntax: No command keywords found."
        
    first_keyword = tokens[0]
    if first_keyword not in READ_ONLY_ALLOWED_KEYWORDS:
        return False, f"Forbidden command: SQL query must start with SELECT, WITH, or EXPLAIN (found '{first_keyword}')."
        
    # Check for forbidden destructive keywords anywhere in query
    for token in tokens:
        if token in FORBIDDEN_SQL_KEYWORDS:
            return False, f"Security Violation: Query contains forbidden destructive keyword '{token}'."

    # Validate table references in FROM / JOIN clauses
    lower_query = cleaned_query.lower()
    matches = re.findall(r'\b(?:from|join)\s+([a-z0-9_]+)', lower_query)
    for table_ref in matches:
        if table_ref not in ALLOWED_TABLES and not table_ref.startswith('('):
            # Check if it's a subquery or known table
            if table_ref not in ALLOWED_TABLES:
                return False, f"Schema Error: Query references unknown table '{table_ref}'. Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}"
            
    return True, "Valid read-only SELECT query."

if __name__ == '__main__':
    print("Testing SQL Validator...")
    valid_sql = "SELECT * FROM applications WHERE TARGET = 1 LIMIT 10;"
    invalid_sql = "DROP TABLE applications;"
    injection_sql = "SELECT * FROM applications; DELETE FROM applications;"
    unknown_table_sql = "SELECT * FROM unknown_table;"
    
    print("Valid SQL test:", validate_sql_query(valid_sql))
    print("Invalid DROP test:", validate_sql_query(invalid_sql))
    print("Multi statement test:", validate_sql_query(injection_sql))
    print("Unknown table test:", validate_sql_query(unknown_table_sql))
