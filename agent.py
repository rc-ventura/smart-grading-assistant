"""Smart Grading Assistant - Main Application Entry Point.

Multi-agent system for academic grading using Google ADK.
Architecture: Root Agent -> Rubric Validator -> Grading Pipeline -> Feedback
"""

import os
import asyncio

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.plugins import LoggingPlugin
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Import configuration
from .config import APP_NAME, USER_ID, DATA_DIR

# Import agents
from .agents import root_agent, build_graders_from_rubric

# Import plugins
from .plugins import RubricGuardrailPlugin

print("✅ Smart Grading Assistant - Loading...")

# =============================================================================
# APP CONFIGURATION
# =============================================================================

grading_app = App(
    name=APP_NAME,
    root_agent=root_agent,
    plugins=[
        LoggingPlugin(),
        RubricGuardrailPlugin(build_graders_fn=build_graders_from_rubric),
    ],
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=6,  # summarize history every 6 invocations
        overlap_size=2,         # keep last 2 turns verbatim for continuity
    ),
)

print("✅ App configured with context compaction (Resumability disabled)")

# =============================================================================
# SESSION & RUNNER SETUP
# =============================================================================

# Use SQLite for persistent sessions
# db_path = os.path.join(DATA_DIR, "grading_sessions.db")
# db_url = f"sqlite:///{db_path}"
session_service = InMemorySessionService()

# Create runner with DatabaseSessionService
runner = Runner(
    app=grading_app,
    session_service=session_service,
)

print(f"✅ Runner configured with DatabaseSessionService")
#print(f"   Database: {db_path}")

