import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
SAVED_MODELS_DIR = MODELS_DIR / "saved_models"
SQL_DIR = BASE_DIR / "sql"
DB_PATH = DATA_DIR / "credisense.db"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure runtime directories exist
for directory in [DATA_DIR, MODELS_DIR, SAVED_MODELS_DIR, SQL_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Data Constants
KEY_COL = "SK_ID_CURR"
TARGET_COL = "TARGET"

# Analytical Risk Band Thresholds (Empirically derived from dataset probability distribution)
# Note: These are analytical reference thresholds, not official banking policy thresholds.
LOW_RISK_MAX_PROB = 0.07
MEDIUM_RISK_MAX_PROB = 0.18

# Model Constants
RANDOM_SEED = 42
TEST_SIZE = 0.2
LGBM_PARAMS = {
    'objective': 'binary',
    'metric': 'auc',
    'boosting_type': 'gbdt',
    'n_estimators': 300,
    'learning_rate': 0.05,
    'num_leaves': 31,
    'max_depth': 6,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': 11.38, # 282,686 negative / 24,825 positive ~ 11.38 to balance class weights
    'random_state': RANDOM_SEED,
    'verbose': -1,
    'n_jobs': -1
}

# SQL / NL-to-SQL Config
READ_ONLY_ALLOWED_KEYWORDS = {"SELECT", "WITH", "EXPLAIN"}
FORBIDDEN_SQL_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "RENAME", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
}

# Version info
VERSION = "1.0.0"
PLATFORM_NAME = "CrediSense AI"
