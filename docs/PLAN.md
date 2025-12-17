# 🎓 Smart Grading Assistant - Capstone Project

## 📋 Project Overview

**Name:** Smart Grading Assistant
**Duration:** 4 days
**Goal:** Multi-agent system for automated academic grading with human oversight

## 🎯 Problem Statement

Teachers spend countless hours grading student submissions manually. This process is:

- Time-consuming and repetitive
- Prone to inconsistency across different submissions
- Lacking in detailed, constructive feedback

## 💡 Solution

A multi-agent AI system that:

1. Validates grading rubrics before evaluation
2. Evaluates submissions against multiple criteria in parallel
3. Consolidates scores with detailed justifications
4. Requests human approval for edge cases
5. Maintains consistency through memory of past evaluations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMART GRADING ASSISTANT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Input: submission (text/code) + rubric                    │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     1. RubricValidatorAgent          │ ← validate_rubric()   │
│  │     (Validates rubric structure)      │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     2. ParallelAgent                  │                       │
│  │     ┌────────────────────────────┐   │                       │
│  │     │ CriterionGrader1           │   │ ← CriterionGrade      │
│  │     │ CriterionGrader2           │   │    (output_schema)    │
│  │     │ CriterionGrader3           │   │                       │
│  │     └────────────────────────────┘   │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     3. AggregatorAgent               │ ← calculate_score()   │
│  │     (Consolidates all grades)         │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     4. Human-in-the-Loop             │ ← request_confirmation│
│  │     (If score < 5 or > 9)            │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     5. FeedbackGeneratorAgent        │                       │
│  │     (Creates detailed feedback)       │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  Output: Grade + Detailed Feedback + Justifications             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🧱 Design Notes: structured outputs

- **Versão inicial:** cada CriterionGrader chamava `grade_criterion()` e o `AggregatorAgent` dependia de `build_grades_payload` → `calculate_score(grades_json)`.
- **Problema:** respostas não estruturadas (texto solto) de alguns graders quebravam o aggregator e tornavam o `SequentialAgent` frágil.
- **Versão atual:** graders usam `output_schema=CriterionGrade` (Pydantic) e salvam `grade_<slug>` no `state`; o aggregator usa apenas `calculate_final_score(tool_context)` lendo diretamente esses objetos.
- **Benefício:** menos acoplamento entre agentes, validação forte de JSON e fluxo mais resiliente a erros de chamada de tool.

## ✅ Course Concepts Covered (6+)

| # | Concept                            | Implementation                                                                           | Points |
| - | ---------------------------------- | ---------------------------------------------------------------------------------------- | ------ |
| 1 | **Multi-agent (Sequential)** | Validator → Graders → Aggregator → Feedback                                           | ✓     |
| 2 | **Multi-agent (Parallel)**   | Multiple criteria evaluated simultaneously                                               | ✓     |
| 3 | **Custom Tools**             | validate_rubric(), save_submission(), calculate_final_score()                            | ✓     |
| 4 | **Human-in-the-Loop**        | Approval for edge cases (score < 5 or > 9)                                               | ✓     |
| 5 | **Sessions & Memory**        | Remember past evaluations for consistency                                                | ✓     |
| 6 | **Observability**            | LoggingPlugin for audit trail                                                            | ✓     |
| 7 | **Plugins & Guardrails**     | RubricGuardrailPlugin (before_agent_callback) enforcing rubric validation before grading | ✓     |
| 8 | **Gemini**                   | Main model (bonus points)                                                                | +5     |

## 📅 4-Day Implementation Plan

### Day 1: Foundation + Validator Agent

- [X] Create project structure
- [X] Implement `validate_rubric()` tool
- [X] Implement `RubricValidatorAgent`
- [X] Test validation flow
- [X] Set up logging

### Day 2: Parallel Grading Agents

- [X] Implement `grade_criterion()` tool
- [X] Create dynamic `CriterionGraderAgent` factory
- [X] Implement `ParallelAgent` for grading
- [X] Test parallel evaluation

### Day 3: Aggregation + Human-in-the-Loop

- [X] Implement `calculate_score()` tool
- [X] Implement `AggregatorAgent`
- [X] Add Human-in-the-Loop with `request_confirmation`
- [X] Implement `FeedbackGeneratorAgent`
- [X] Add Memory (DatabaseSessionService)

### Day 4: Polish + Documentation

- [X] Add Observability (LoggingPlugin)
- [X] Add Rubric Guardrail (RubricGuardrailPlugin) to block grading when rubric is not valid
- [X] Create comprehensive README.md
- [X] Add example rubrics and submissions
- [ ] Create Streamlit frontend (optional)
- [ ] Record demo video (optional)

## 📁 Project Structure

```
capstone/
├── agent.py              # Main entry point with root agent
├── agents/
│   ├── __init__.py
│   ├── rubric_validator.py
│   ├── criterion_grader.py
│   ├── aggregator.py
│   └── feedback_generator.py
├── tools/
│   ├── __init__.py
│   ├── validate_rubric.py
│   ├── grade_criterion.py
│   └── calculate_score.py
├── examples/
│   ├── rubrics/
│   │   ├── python_code_rubric.json
│   │   └── essay_rubric.json
│   └── submissions/
│       ├── sample_code.py
│       └── sample_essay.txt
├── .env
├── requirements.txt
└── README.md
```

## 🔧 Tech Stack

- **Framework:** Google ADK (Agent Development Kit)
- **Model:** Gemini 2.5 Flash
- **Memory:** DatabaseSessionService (SQLite)
- **Observability:** LoggingPlugin
- **Frontend:** Streamlit (optional)

## 📊 Evaluation Criteria Mapping

| Criteria                    | Points | Our Implementation                  |
| --------------------------- | ------ | ----------------------------------- |
| Core Concept & Value        | 15     | Real-world problem, clear agent use |
| Writeup                     | 15     | Comprehensive README                |
| Technical Implementation    | 50     | 6+ concepts, clean architecture     |
| Documentation               | 20     | README + inline comments            |
| **Bonus: Gemini**     | 5      | Using Gemini 2.5 Flash              |
| **Bonus: Deployment** | 5      | (Optional) Cloud Run                |
| **Bonus: Video**      | 10     | (Optional) 3-min demo               |

**Expected Score:** 85-100 points

## 🚀 Quick Start

```bash
cd capstone
pip install -r requirements.txt
cp .env.example .env  # Add your GOOGLE_API_KEY
python agent.py
```

## 📝 Example Usage

```python
# Input
rubric = {
    "criteria": [
        {"name": "Code Quality", "max_score": 30, "description": "Clean, readable code"},
        {"name": "Functionality", "max_score": 40, "description": "Code works correctly"},
        {"name": "Documentation", "max_score": 30, "description": "Well documented"}
    ]
}

submission = """
def fibonacci(n):
    # Returns the nth Fibonacci number
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

# Output
{
    "final_score": 85,
    "grades": {
        "Code Quality": {"score": 25, "justification": "Clean recursive implementation..."},
        "Functionality": {"score": 35, "justification": "Works correctly but inefficient..."},
        "Documentation": {"score": 25, "justification": "Good docstring, could add more..."}
    },
    "feedback": "Good implementation! Consider memoization for efficiency...",
    "approved_by": "human" | "auto"
}
```
