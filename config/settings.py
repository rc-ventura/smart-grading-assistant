"""Configuration settings for the Smart Grading Assistant."""

import os
import logging
from dotenv import load_dotenv
from google.genai import types

# Load environment variables
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

# App configuration
APP_NAME = "capstone"
USER_ID = "teacher_01"

# Grading thresholds
FAILING_THRESHOLD = 50
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
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
)

print(f"✅ Configuration loaded")
print(f"   LOG_PATH: {LOG_PATH}")
print(f"   DATA_DIR: {DATA_DIR}")
print(f"   MODEL: {MODEL}")
print(f"   MODEL_LITE: {MODEL_LITE}")
