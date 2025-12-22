"""Smart Grading Assistant - Main Application Entry Point.

Multi-agent system for academic grading using Google ADK.
Architecture: Root Agent -> Rubric Validator -> Grading Pipeline -> Feedback
"""

import os

from google.adk.apps.app import App, EventsCompactionConfig, ResumabilityConfig
from google.adk.plugins import LoggingPlugin
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService 
from google.genai import types

# Import configuration
from config import APP_NAME, USER_ID, DATA_DIR

# Import agents
from agents import root_agent, build_graders_from_rubric

# Import plugins
from plugins import RubricGuardrailPlugin

print("✅ Smart Grading Assistant - Loading...")


def create_grading_runner(*, provider: str = "gemini") -> tuple[Runner, App]:
    """Create a fresh Runner/App pair for the specified LLM provider.
    
    Uses agent factories to create fresh instances with the correct model.
    Thread-safe and production-ready.
    """
    provider = (provider or "gemini").strip().lower()
    
    # Set provider in environment so get_model() picks it up
    os.environ["LLM_PROVIDER"] = provider
    
    # Import agent factories
    from services.llm_provider import get_model
    from agents.rubric_validator import create_rubric_validator_agent
    from agents.aggregator import create_aggregator_agent
    from agents.approval import create_approval_agent
    from agents.feedback import create_feedback_agent
    from agents.root import create_grading_pipeline, create_root_agent
    from agents.graders import build_graders_from_rubric
    from google.adk.agents import ParallelAgent
    
    # Create agents with current provider's model
    model = get_model()
    
    rubric_validator = create_rubric_validator_agent(model)
    aggregator = create_aggregator_agent(model)
    approval = create_approval_agent(model)
    feedback = create_feedback_agent(model)
    
    # Create fresh ParallelGraders to avoid parent conflicts
    # (will be populated dynamically by RubricGuardrailPlugin)
    fresh_graders = ParallelAgent(name="ParallelGraders", sub_agents=[])
    
    grading_pipeline = create_grading_pipeline(aggregator, approval, feedback, graders=fresh_graders)
    
    root = create_root_agent(
        model=model, 
        rubric_validator=rubric_validator, 
        grading_pipeline_agent=grading_pipeline,
    )
    
    # Create App with fresh agents
    grading_app = App(
        name=APP_NAME,
        root_agent=root,
        plugins=[
            LoggingPlugin(),
            RubricGuardrailPlugin(build_graders_fn=build_graders_from_rubric),
        ],
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=6,
            overlap_size=2,
        ),
        resumability_config=ResumabilityConfig(
            is_resumable=True,
        ),
    )

    session_service = InMemorySessionService()
    runner = Runner(app=grading_app, session_service=session_service)

    return runner, grading_app

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
    resumability_config=ResumabilityConfig(
        is_resumable=True,
    ),
)

print("✅ App configured with context compaction (Resumability enabled)")

# =============================================================================
# SESSION & RUNNER SETUP
# =============================================================================

# Use in-memory sessions
session_service = InMemorySessionService()

# Create runner with DatabaseSessionService
runner = Runner(
    app=grading_app,
    session_service=session_service,
)

print(f"✅ Runner configured with InMemorySessionService")

