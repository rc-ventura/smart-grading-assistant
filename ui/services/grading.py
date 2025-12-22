"""Grading service - Facade for backward compatibility.

This module re-exports functions from specialized modules:
- grading_lifecycle: Runner/App/Session management
- grading_validation: Rubric/Submission validation  
- grading_execution: Grading execution and results
- grading_mapper: Event mapping utilities
"""

# Re-export lifecycle functions
from ui.services.grading_lifecycle import (
    invalidate_runner,
    get_app,
    get_runner,
    start_grading_session,
    runner,
    ADK_AVAILABLE,
    grading_app,
    types,
)

# Re-export validation functions
from ui.services.grading_validation import (
    send_rubric,
    send_submission,
)

# Re-export execution functions
from ui.services.grading_execution import (
    run_runner_events,
    run_grading,
    get_results,
)

# Re-export mapper utilities
from ui.services.grading_mapper import map_runner_event


__all__ = [
    # Lifecycle
    "invalidate_runner",
    "get_app",
    "get_runner",
    "start_grading_session",
    "runner",
    "grading_app",
    "types",
    "ADK_AVAILABLE",
    # Validation
    "send_rubric",
    "send_submission",
    # Execution
    "run_runner_events",
    "run_grading",
    "get_results",
    # Mapper
    "map_runner_event",
]

