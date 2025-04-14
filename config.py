# config.py
import os

from dotenv import load_dotenv

load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"  # Use the most capable model available

# Dataset paths
DATASET_ROOT = "./data/mini_dev_data"
SQLITE_DB_PATH = os.path.join(DATASET_ROOT, "dev_databases")
# MINI_DEV_JSON = os.path.join(DATASET_ROOT, "mini_dev_sqlite.json")
# GOLD_SQL_PATH = os.path.join(DATASET_ROOT, "mini_dev_sqlite_gold.sql")
MINI_DEV_JSON = os.path.join(DATASET_ROOT, "dev.json")
GOLD_SQL_PATH = os.path.join(DATASET_ROOT, "dev.sql")

# Agent configuration
MAX_RETRY_ATTEMPTS = 3
TEMPERATURE_SELECTOR = 0.2
TEMPERATURE_DECOMPOSER = 0.3
TEMPERATURE_GENERATOR = 0.2
TEMPERATURE_REFINER = 0.1

# Database configuration
TIMEOUT_SECONDS = 10  # Timeout for SQL execution
