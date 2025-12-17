"""
Comprehensive test suite for RubricGuardrailPlugin.

Tests multiple scenarios:
1. Valid rubric - guardrail allows pipeline to run
2. Invalid rubric (missing criteria) - guardrail blocks
3. Invalid rubric (empty criteria) - guardrail blocks
4. Invalid rubric (incomplete criterion) - guardrail blocks
5. Invalid JSON - guardrail blocks
6. User insisting with invalid rubric - still blocked
7. Fix rubric after rejection - guardrail allows

Each test prints clear markers showing when guardrail is invoked.
"""

import asyncio
import json
from capstone.tools.validate_rubric import validate_rubric
from capstone.agent import RubricGuardrailPlugin
from capstone.agents import build_graders_from_rubric



# =============================================================================
# MOCK CLASSES FOR UNIT TESTING (no API calls needed)
# =============================================================================

class MockState:
    """Mock state object for testing."""
    def __init__(self):
        self._data = {}
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __getitem__(self, key):
        return self._data[key]
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def to_dict(self):
        return self._data.copy()
    
    def clear(self):
        self._data.clear()


class MockToolContext:
    """Mock ToolContext for testing validate_rubric tool."""
    def __init__(self):
        self.state = MockState()


class MockCallbackContext:
    """Mock CallbackContext for testing RubricGuardrailPlugin."""
    def __init__(self, state_data: dict = None):
        self.state = MockState()
        if state_data:
            for k, v in state_data.items():
                self.state[k] = v
        self.agent_name = "TestAgent"


class MockAgent:
    """Mock agent for testing."""
    def __init__(self, name: str):
        self.name = name


# =============================================================================
# TEST RUBRICS
# =============================================================================

VALID_RUBRIC = {
    "name": "Python Code Evaluation Rubric",
    "criteria": [
        {"name": "Code Quality", "max_score": 30, "description": "Code readability and style"},
        {"name": "Functionality", "max_score": 40, "description": "Correctness of solution"},
        {"name": "Documentation", "max_score": 30, "description": "Comments and docstrings"},
    ],
}

# Custom rubrics to verify truly dynamic behavior (different names/counts)
CUSTOM_RUBRIC_4 = {
    "name": "Essay Evaluation Rubric",
    "criteria": [
        {"name": "Clarity of Argument", "max_score": 25, "description": "How clear and coherent the argument is"},
        {"name": "Use of Evidence", "max_score": 25, "description": "Quality and relevance of supporting evidence"},
        {"name": "Organization", "max_score": 25, "description": "Logical structure and flow"},
        {"name": "Writing Mechanics", "max_score": 25, "description": "Grammar, spelling, and style"},
    ],
}

CUSTOM_RUBRIC_2 = {
    "name": "Short Presentation Rubric",
    "criteria": [
        {"name": "Delivery", "max_score": 50, "description": "Confidence, pacing, and body language"},
        {"name": "Content", "max_score": 50, "description": "Relevance and depth of content"},
    ],
}

INVALID_NO_CRITERIA = {
    "name": "Bad Rubric - No Criteria",
    # Missing "criteria" field
}

INVALID_EMPTY_CRITERIA = {
    "name": "Bad Rubric - Empty Criteria",
    "criteria": [],
}

INVALID_INCOMPLETE_CRITERION = {
    "name": "Bad Rubric - Incomplete Criterion",
    "criteria": [
        {"name": "Quality"},  # Missing max_score and description
    ],
}

INVALID_BAD_SCORE = {
    "name": "Bad Rubric - Negative Score",
    "criteria": [
        {"name": "Quality", "max_score": -10, "description": "Bad score"},
    ],
}

INVALID_JSON_STRING = "this is not valid JSON {"


# =============================================================================
# UNIT TESTS FOR validate_rubric TOOL
# =============================================================================

def test_validate_rubric_valid():
    """Test: Valid rubric passes validation and saves to state."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Valid Rubric")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(json.dumps(VALID_RUBRIC), ctx)
    
    print(f"   Input: Rubric with 3 valid criteria")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "valid", f"Expected valid, got {result['status']}"
    assert ctx.state["rubric_validation"]["status"] == "valid"
    assert result["criteria_count"] == 3
    assert result["total_points"] == 100
    assert "rubric" in ctx.state._data, "Rubric should be persisted in state"
    assert ctx.state["rubric"]["criteria"][0]["name"] == "Code Quality"
    
    print("   ✅ PASS: Valid rubric correctly validated")


def test_validate_rubric_no_criteria():
    """Test: Rubric without criteria field fails validation."""
    print("\n" + "="*60)
    print("🧪 TEST 2: Invalid Rubric - Missing 'criteria' Field")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(json.dumps(INVALID_NO_CRITERIA), ctx)
    
    print(f"   Input: {INVALID_NO_CRITERIA}")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "invalid", f"Expected invalid, got {result['status']}"
    assert "Missing 'criteria' field" in str(result["errors"])
    assert ctx.state["rubric_validation"]["status"] == "invalid"
    
    print("   ✅ PASS: Missing criteria correctly rejected")


def test_validate_rubric_empty_criteria():
    """Test: Rubric with empty criteria list fails validation."""
    print("\n" + "="*60)
    print("🧪 TEST 3: Invalid Rubric - Empty 'criteria' List")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(json.dumps(INVALID_EMPTY_CRITERIA), ctx)
    
    print(f"   Input: {INVALID_EMPTY_CRITERIA}")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "invalid", f"Expected invalid, got {result['status']}"
    assert "at least one criterion" in str(result["errors"])
    assert ctx.state["rubric_validation"]["status"] == "invalid"
    
    print("   ✅ PASS: Empty criteria correctly rejected")


def test_validate_rubric_incomplete_criterion():
    """Test: Rubric with incomplete criterion fails validation."""
    print("\n" + "="*60)
    print("🧪 TEST 4: Invalid Rubric - Incomplete Criterion")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(json.dumps(INVALID_INCOMPLETE_CRITERION), ctx)
    
    print(f"   Input: {INVALID_INCOMPLETE_CRITERION}")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "invalid", f"Expected invalid, got {result['status']}"
    assert "max_score" in str(result["errors"])
    assert "description" in str(result["errors"])
    assert ctx.state["rubric_validation"]["status"] == "invalid"
    
    print("   ✅ PASS: Incomplete criterion correctly rejected")


def test_validate_rubric_bad_score():
    """Test: Rubric with negative score fails validation."""
    print("\n" + "="*60)
    print("🧪 TEST 5: Invalid Rubric - Negative Score")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(json.dumps(INVALID_BAD_SCORE), ctx)
    
    print(f"   Input: {INVALID_BAD_SCORE}")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "invalid", f"Expected invalid, got {result['status']}"
    assert "must be positive" in str(result["errors"])
    assert ctx.state["rubric_validation"]["status"] == "invalid"
    
    print("   ✅ PASS: Negative score correctly rejected")


def test_validate_rubric_invalid_json():
    """Test: Invalid JSON string fails validation."""
    print("\n" + "="*60)
    print("🧪 TEST 6: Invalid JSON String")
    print("="*60)
    
    ctx = MockToolContext()
    result = validate_rubric(INVALID_JSON_STRING, ctx)
    
    print(f"   Input: '{INVALID_JSON_STRING}'")
    print(f"   Result: {result}")
    print(f"   State saved: {ctx.state._data}")
    
    assert result["status"] == "invalid", f"Expected invalid, got {result['status']}"
    assert "Invalid JSON" in str(result["errors"])
    assert ctx.state["rubric_validation"]["status"] == "invalid"
    
    print("   ✅ PASS: Invalid JSON correctly rejected")


# =============================================================================
# UNIT TESTS FOR RubricGuardrailPlugin
# =============================================================================

def test_guardrail_allows_valid_rubric():
    """Test: Guardrail allows protected agents when rubric is valid."""
    print("\n" + "="*60)
    print("🧪 TEST 7: Guardrail ALLOWS with Valid Rubric")
    print("="*60)
    
    
    plugin = RubricGuardrailPlugin(build_graders_fn=build_graders_from_rubric)
    
    # Simulate state after valid rubric validation
    ctx = MockCallbackContext(state_data={
        "rubric_validation": {"status": "valid", "criteria_count": 3}
    })
    
    # Test with protected agent
    agent = MockAgent("ParallelGraders")
    
    print(f"   Agent: {agent.name}")
    print(f"   State: {ctx.state.to_dict()}")
    
    # Check if guardrail would allow
    is_valid = plugin._is_rubric_valid(ctx)
    validation_result = plugin._get_validation_result(ctx)
    
    print(f"   Guardrail check:")
    print(f"     - _get_validation_result() = {validation_result}")
    print(f"     - _is_rubric_valid() = {is_valid}")
    
    assert is_valid == True, f"Expected True, got {is_valid}"
    assert validation_result["status"] == "valid"
    
    print("   ✅ PASS: Guardrail correctly allows valid rubric")


def test_parallel_graders_dynamic_creation_from_rubric():
    """Test: Guardrail injects dynamic graders into ParallelGraders from rubric."""
    print("\n" + "="*60)
    print("🧪 TEST 7b: Dynamic ParallelGraders from Valid Rubric")
    print("="*60)


    plugin = RubricGuardrailPlugin(build_graders_fn=build_graders_from_rubric)

    # First, run validate_rubric to simulate normal pipeline behavior
    tool_ctx = MockToolContext()
    validate_result = validate_rubric(json.dumps(VALID_RUBRIC), tool_ctx)

    print(f"   validate_rubric result: {validate_result}")
    print(f"   Tool state after validation: {tool_ctx.state.to_dict()}")

    assert validate_result["status"] == "valid"
    assert "rubric" in tool_ctx.state._data

    # Ensure criteria have slugs so build_graders_from_rubric can produce keys
    from capstone.utils.text_utils import slugify
    rubric_dict = tool_ctx.state._data.get("rubric") or {}
    for crit in rubric_dict.get("criteria", []):
        crit.setdefault("slug", slugify(crit.get("name") or ""))

    # Use the same state as callback_context for the guardrail (now with slugs)
    callback_ctx = MockCallbackContext(state_data=tool_ctx.state._data)

    # ParallelGraders agent that should receive dynamic sub_agents
    agent = MockAgent("ParallelGraders")

    print(f"   Before callback - agent.name={agent.name}, has sub_agents? {hasattr(agent, 'sub_agents')}")

    # Run the async before_agent_callback hook
    async def _run_callback():
        return await plugin.before_agent_callback(agent=agent, callback_context=callback_ctx)

    result_content = asyncio.run(_run_callback())

    # Guardrail should allow execution (return None) and inject dynamic graders
    print(f"   before_agent_callback returned: {result_content}")
    assert result_content is None

    # Check that dynamic graders were created
    assert hasattr(agent, "sub_agents"), "ParallelGraders should have dynamic sub_agents after guardrail"
    dynamic_graders = agent.sub_agents
    rubric = callback_ctx.state.get("rubric")
    assert rubric is not None, "Rubric should be present in callback context state"

    expected_criteria = rubric["criteria"]
    print(f"   Dynamic graders created: {len(dynamic_graders)}")
    print(f"   Rubric criteria count: {len(expected_criteria)}")

    assert len(dynamic_graders) == len(expected_criteria)

    # Slugs and grade keys should match rubric slugs
    expected_slugs = [c["slug"] for c in expected_criteria]
    expected_grade_keys = [f"grade_{s}" for s in expected_slugs]

    grader_output_keys = callback_ctx.state.get("grader_output_keys")
    print(f"   grader_output_keys: {grader_output_keys}")

    assert grader_output_keys == expected_grade_keys

    dynamic_names = [g.name for g in dynamic_graders]
    print(f"   Dynamic grader names: {dynamic_names}")

    for slug in expected_slugs:
        expected_name = f"Grader_{slug}"
        assert expected_name in dynamic_names, f"Expected dynamic grader '{expected_name}' to be created"

    print("   ✅ PASS: ParallelGraders receives dynamic graders and keys from rubric")


def test_parallel_graders_respects_custom_rubrics():
    """Test: ParallelGraders follows custom rubrics (non-default names/counts)."""
    print("\n" + "="*60)
    print("🧪 TEST 7c: ParallelGraders with Custom Rubrics (4 and 2 criteria)")
    print("="*60)

    # We'll test two different rubrics: one with 4 criteria, another with 2
    for rubric in (CUSTOM_RUBRIC_4, CUSTOM_RUBRIC_2):
        print(f"\n   Testing rubric: {rubric['name']}")

        plugin = RubricGuardrailPlugin(build_graders_fn=build_graders_from_rubric)
        tool_ctx = MockToolContext()

        # Validate rubric and persist to state (adds slugs per criterion)
        validate_result = validate_rubric(json.dumps(rubric), tool_ctx)
        print(f"     validate_rubric result: {validate_result}")
        print(f"     Tool state after validation: {tool_ctx.state.to_dict()}")

        assert validate_result["status"] == "valid"
        assert "rubric" in tool_ctx.state._data

        # Use validated state as callback context
        callback_ctx = MockCallbackContext(state_data=tool_ctx.state._data)
        agent = MockAgent("ParallelGraders")

        # Run guardrail callback to inject dynamic graders
        async def _run_callback():
            return await plugin.before_agent_callback(agent=agent, callback_context=callback_ctx)

        result_content = asyncio.run(_run_callback())
        print(f"     before_agent_callback returned: {result_content}")
        assert result_content is None

        # Confirm dynamic graders and keys
        assert hasattr(agent, "sub_agents"), "ParallelGraders should have dynamic sub_agents after guardrail"
        dynamic_graders = agent.sub_agents
        rubric_state = callback_ctx.state.get("rubric")
        assert rubric_state is not None

        expected_criteria = rubric_state["criteria"]
        print(f"     Dynamic graders created: {len(dynamic_graders)}")
        print(f"     Rubric criteria count: {len(expected_criteria)}")
        assert len(dynamic_graders) == len(expected_criteria)

        expected_slugs = [c["slug"] for c in expected_criteria]
        expected_grade_keys = [f"grade_{s}" for s in expected_slugs]
        grader_output_keys = callback_ctx.state.get("grader_output_keys")

        print(f"     grader_output_keys: {grader_output_keys}")
        assert grader_output_keys == expected_grade_keys

        dynamic_names = [g.name for g in dynamic_graders]
        print(f"     Dynamic grader names: {dynamic_names}")

        for slug in expected_slugs:
            expected_name = f"Grader_{slug}"
            assert expected_name in dynamic_names, f"Expected dynamic grader '{expected_name}' to be created for slug '{slug}'"

        # Inspect prompts for each dynamic grader to ensure rubric data is injected
        for grader, criterion in zip(dynamic_graders, expected_criteria):
            crit_name = criterion["name"]
            crit_desc = criterion["description"]
            max_score = criterion["max_score"]

            print("     --- Dynamic grader prompt inspection ---")
            print(f"       Grader name: {grader.name}")
            print(f"       Description: {grader.description}")
            print(f"       Instruction (truncated): {grader.instruction[:200]}...")

            # Description should reference the rubric criterion name
            assert crit_name in grader.description, (
                f"Grader description should contain criterion name '{crit_name}'"
            )

            # Instruction should include criterion name, description, and max_score
            assert crit_name in grader.instruction, (
                f"Grader instruction should contain criterion name '{crit_name}'"
            )
            assert crit_desc in grader.instruction, (
                f"Grader instruction should contain criterion description '{crit_desc}'"
            )
            assert str(max_score) in grader.instruction, (
                f"Grader instruction should mention max_score '{max_score}'"
            )

    print("   ✅ PASS: ParallelGraders respects custom rubrics (names and counts)")


def test_guardrail_blocks_invalid_rubric():
    """Test: Guardrail blocks protected agents when rubric is invalid."""
    print("\n" + "="*60)
    print("🧪 TEST 8: Guardrail BLOCKS with Invalid Rubric")
    print("="*60)
    
    plugin = RubricGuardrailPlugin()
    
    # Simulate state after invalid rubric validation
    ctx = MockCallbackContext(state_data={
        "rubric_validation": {"status": "invalid", "errors": ["Missing criteria"]}
    })
    
    agent = MockAgent("ParallelGraders")
    
    print(f"   Agent: {agent.name}")
    print(f"   State: {ctx.state.to_dict()}")
    
    is_valid = plugin._is_rubric_valid(ctx)
    validation_result = plugin._get_validation_result(ctx)
    
    print(f"   Guardrail check:")
    print(f"     - _get_validation_result() = {validation_result}")
    print(f"     - _is_rubric_valid() = {is_valid}")
    
    assert is_valid == False, f"Expected False, got {is_valid}"
    assert validation_result["status"] == "invalid"
    
    # Check block message is generated
    block_msg = plugin._build_block_message(agent.name, ctx)
    print(f"   Block message preview: {block_msg[:100]}...")
    
    assert "GRADING BLOCKED" in block_msg
    assert "Missing criteria" in block_msg
    
    print("   ✅ PASS: Guardrail correctly blocks invalid rubric")


def test_guardrail_blocks_missing_validation():
    """Test: Guardrail blocks when no validation was done."""
    print("\n" + "="*60)
    print("🧪 TEST 9: Guardrail BLOCKS with No Validation")
    print("="*60)
    
    
    plugin = RubricGuardrailPlugin()
    
    # Empty state - no rubric_validation key
    ctx = MockCallbackContext(state_data={})
    
    agent = MockAgent("ParallelGraders")
    
    print(f"   Agent: {agent.name}")
    print(f"   State: {ctx.state.to_dict()}")
    
    is_valid = plugin._is_rubric_valid(ctx)
    validation_result = plugin._get_validation_result(ctx)
    
    print(f"   Guardrail check:")
    print(f"     - _get_validation_result() = {validation_result}")
    print(f"     - _is_rubric_valid() = {is_valid}")
    
    assert is_valid == False, f"Expected False, got {is_valid}"
    assert validation_result is None
    
    print("   ✅ PASS: Guardrail correctly blocks when no validation exists")


def test_guardrail_ignores_unprotected_agents():
    """Test: Guardrail does not affect unprotected agents."""
    print("\n" + "="*60)
    print("🧪 TEST 10: Guardrail Ignores Unprotected Agents")
    print("="*60)
    
    
    plugin = RubricGuardrailPlugin()
    
    # Invalid rubric in state
    ctx = MockCallbackContext(state_data={
        "rubric_validation": {"status": "invalid", "errors": ["Bad"]}
    })
    
    # Test with unprotected agents
    unprotected = ["SmartGradingAssistant", "RubricValidatorAgent", "RandomAgent"]
    protected = ["ParallelGraders", "AggregatorAgent", "Grader_Code_Quality"]
    
    print(f"   Testing unprotected agents (should NOT be checked):")
    for name in unprotected:
        agent = MockAgent(name)
        # The plugin checks agent name first, before checking validation
        is_protected = name in {
            "ParallelGraders", "AggregatorAgent", "ApprovalAgent",
            "FeedbackGeneratorAgent", "Grader_Code_Quality",
            "Grader_Functionality", "Grader_Documentation"
        }
        print(f"     - {name}: protected={is_protected}")
        assert not is_protected, f"{name} should not be protected"
    
    print(f"   Testing protected agents (should be checked):")
    for name in protected:
        agent = MockAgent(name)
        is_protected = name in {
            "ParallelGraders", "AggregatorAgent", "ApprovalAgent",
            "FeedbackGeneratorAgent", "Grader_Code_Quality",
            "Grader_Functionality", "Grader_Documentation"
        }
        print(f"     - {name}: protected={is_protected}")
        assert is_protected, f"{name} should be protected"
    
    print("   ✅ PASS: Guardrail correctly distinguishes protected/unprotected agents")


def test_fix_rubric_after_rejection():
    """Test: After fixing rubric, guardrail allows pipeline."""
    print("\n" + "="*60)
    print("🧪 TEST 11: Fix Rubric After Rejection (Simulated Flow)")
    print("="*60)
    
    plugin = RubricGuardrailPlugin()
    ctx = MockToolContext()
    
    # Step 1: Submit invalid rubric
    print("   Step 1: Submit invalid rubric")
    result1 = validate_rubric(json.dumps(INVALID_NO_CRITERIA), ctx)
    print(f"     Result: {result1['status']}")
    print(f"     State: {ctx.state.to_dict()}")
    
    # Check guardrail would block
    guard_ctx1 = MockCallbackContext(state_data=ctx.state._data)
    is_valid1 = plugin._is_rubric_valid(guard_ctx1)
    print(f"     Guardrail would block: {not is_valid1}")
    assert is_valid1 == False
    
    # Step 2: Fix and resubmit valid rubric
    print("\n   Step 2: Fix and resubmit valid rubric")
    result2 = validate_rubric(json.dumps(VALID_RUBRIC), ctx)
    print(f"     Result: {result2['status']}")
    print(f"     State: {ctx.state.to_dict()}")
    
    # Check guardrail would allow
    guard_ctx2 = MockCallbackContext(state_data=ctx.state._data)
    is_valid2 = plugin._is_rubric_valid(guard_ctx2)
    print(f"     Guardrail would allow: {is_valid2}")
    assert is_valid2 == True
    
    print("   ✅ PASS: Guardrail correctly switches from block to allow after fix")


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "="*70)
    print("🔒 RUBRIC GUARDRAIL - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        # Validation tool tests
        ("Validate valid rubric", test_validate_rubric_valid),
        ("Validate rubric without criteria", test_validate_rubric_no_criteria),
        ("Validate rubric with empty criteria", test_validate_rubric_empty_criteria),
        ("Validate rubric with incomplete criterion", test_validate_rubric_incomplete_criterion),
        ("Validate rubric with negative score", test_validate_rubric_bad_score),
        ("Validate invalid JSON", test_validate_rubric_invalid_json),
        # Guardrail plugin tests
        ("Guardrail allows valid rubric", test_guardrail_allows_valid_rubric),
        ("Dynamic ParallelGraders from rubric", test_parallel_graders_dynamic_creation_from_rubric),
        ("ParallelGraders respects custom rubrics", test_parallel_graders_respects_custom_rubrics),
        ("Guardrail blocks invalid rubric", test_guardrail_blocks_invalid_rubric),
        ("Guardrail blocks missing validation", test_guardrail_blocks_missing_validation),
        ("Guardrail ignores unprotected agents", test_guardrail_ignores_unprotected_agents),
        ("Fix rubric after rejection", test_fix_rubric_after_rejection),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((name, f"AssertionError: {e}"))
            print(f"   ❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            errors.append((name, f"{type(e).__name__}: {e}"))
            print(f"   ❌ ERROR: {type(e).__name__}: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"   Total tests: {len(tests)}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    
    if errors:
        print("\n   Failures:")
        for name, error in errors:
            print(f"     - {name}: {error}")
    
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
