"""
Smart Grading Assistant - Main Application Entry Point

This is a multi-agent system for academic grading using Google ADK.
Architecture: Root Agent -> Rubric Validator -> Grading Pipeline -> Feedback
"""

import os

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.plugins import LoggingPlugin
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService

# Import configuration
from config import APP_NAME, USER_ID, DATA_DIR

# Import agents
from agents import root_agent, build_graders_from_rubric

# Import plugins
from plugins import RubricGuardrailPlugin

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
db_path = os.path.join(DATA_DIR, "grading_sessions.db")
db_url = f"sqlite:///{db_path}"
session_service = DatabaseSessionService(db_url=db_url)

# Create runner with DatabaseSessionService
runner = Runner(
    app=grading_app,
    session_service=session_service,
)

print(f"✅ Runner configured with DatabaseSessionService")
print(f"   Database: {db_path}")

# =============================================================================
# DEMO FUNCTION (for testing)
# =============================================================================


def demo():
    """Run a demo grading session."""
    import json
    from pathlib import Path

    print("\n" + "=" * 80)
    print("DEMO: Smart Grading Assistant")
    print("=" * 80 + "\n")

    # Load example rubric
    rubric_path = Path(__file__).parent / "examples" / "rubrics" / "python_code_rubric.json"
    with open(rubric_path) as f:
        rubric = json.load(f)

    # Load example submission
    submission_path = Path(__file__).parent / "examples" / "submissions" / "sample_code.py"
    with open(submission_path) as f:
        submission = f.read()

    print("📋 Rubric loaded:", rubric["name"])
    print("📄 Submission loaded: sample_code.py")
    print("\nStarting grading session...\n")

    # Run the grading workflow
    session = runner.create_session(user_id=USER_ID)

    # Step 1: Validate rubric
    print("Step 1: Validating rubric...")
    result1 = runner.run(
        session_id=session.id,
        user_id=USER_ID,
        user_message=json.dumps(rubric, indent=2),
    )
    print(f"Response: {result1.content}\n")

    # Step 2: Submit student work
    print("Step 2: Submitting student work...")
    result2 = runner.run(
        session_id=session.id,
        user_id=USER_ID,
        user_message=submission,
    )
    print(f"Response: {result2.content}\n")

    print("=" * 80)
    print("Demo completed!")
    print("=" * 80)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        print("\n" + "=" * 80)
        print("Smart Grading Assistant - Ready")
        print("=" * 80)
        print("\nUsage:")
        print("  python -m capstone.agent demo    # Run demo")
        print("  adk web                          # Start web interface")
        print("=" * 80 + "\n")
