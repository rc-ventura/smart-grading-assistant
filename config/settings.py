"""Configuration settings for the Smart Grading Assistant."""

import os
import logging
from dotenv import load_dotenv
from google.genai import types

load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_PATH = os.path.join(BASE_DIR, "logs", "grading_agent.log")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Create directories
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Models
MODEL_LITE = os.getenv("MODEL_LITE", "gemini-2.5-flash-lite")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# LLM provider (Gemini/OpenAI via LiteLLM)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # LiteLLM proxy or Azure endpoint
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GRADER_CONCURRENCY_LIMIT = max(1, int(os.getenv("GRADER_CONCURRENCY_LIMIT", "2")))
GRADER_TEMPERATURE = float(os.getenv("GRADER_TEMPERATURE", "0.1"))
GRADER_MAX_OUTPUT_TOKENS = int(os.getenv("GRADER_MAX_OUTPUT_TOKENS", "384"))
FEEDBACK_TEMPERATURE = float(os.getenv("FEEDBACK_TEMPERATURE", "0.5"))
FEEDBACK_MAX_OUTPUT_TOKENS = int(os.getenv("FEEDBACK_MAX_OUTPUT_TOKENS", "2048"))
OPENAI_GPT5_MIN_OUTPUT_TOKENS = int(os.getenv("OPENAI_GPT5_MIN_OUTPUT_TOKENS", "2048"))

# Defaults
DEFAULT_MODEL = OPENAI_MODEL

# App configuration
APP_NAME = "capstone"
USER_ID = "teacher_01"

# Grading thresholds
FAILING_THRESHOLD = 60
EXCEPTIONAL_THRESHOLD = 90

# Retry configuration for LLM calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
)

print(f"✅ Configuration loaded")
print(f"   LOG_PATH: {LOG_PATH}")
print(f"   DATA_DIR: {DATA_DIR}")
print(f"   LLM_PROVIDER: {LLM_PROVIDER}")
