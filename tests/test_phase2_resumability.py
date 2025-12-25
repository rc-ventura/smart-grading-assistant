import pytest

from google.adk.agents import ParallelAgent, SequentialAgent

from agents.aggregator import create_aggregator_agent
from agents.approval import create_approval_agent
from agents.feedback import create_feedback_agent
from agents.root import create_grading_pipeline
from tools.finalize_grade import needs_approval


class MockToolContext:
    def __init__(self, state):
        self.state = state


@pytest.mark.asyncio
async def test_needs_approval_uses_requires_human_intervention_flag():
    ctx = MockToolContext(
        {
            "aggregation_result": {
                "requires_human_intervention": True,
            }
        }
    )

    assert (
        await needs_approval(
            final_score=0,
            max_score=100,
            percentage=50,
            letter_grade="F",
            reason="",
            tool_context=ctx,
        )
        is True
    )


def test_grading_pipeline_order_approval_before_feedback():
    fresh_graders = ParallelAgent(name="ParallelGraders", sub_agents=[])
    aggregator = create_aggregator_agent()
    approval = create_approval_agent()
    feedback = create_feedback_agent()

    pipeline = create_grading_pipeline(aggregator, approval, feedback, graders=fresh_graders)

    assert isinstance(pipeline, SequentialAgent)

    names = [a.name for a in pipeline.sub_agents]
    assert names == [
        "ParallelGraders",
        "AggregatorAgent",
        "ApprovalAgent",
        "FeedbackGeneratorAgent",
    ]
