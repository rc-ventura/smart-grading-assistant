# 🎓 Smart Grading Assistant

> A multi-agent AI system for automated academic grading with human oversight

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-0.1.0-green.svg)](https://github.com/google/adk)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange.svg)](https://ai.google.dev)

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution](#-solution)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Course Concepts Applied](#-course-concepts-applied)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Examples](#-examples)
- [Roadmap](#-roadmap)
- [Future Improvements](#-future-improvements)

---

## 🎯 Problem Statement

Teachers and educators spend countless hours grading student submissions manually. This process is:

- **Time-consuming**: Hours spent on repetitive evaluation tasks
- **Inconsistent**: Grading quality varies based on fatigue and workload
- **Lacking feedback**: Students often receive minimal constructive feedback
- **Not scalable**: Difficult to maintain quality with large class sizes

## 💡 Solution

**Smart Grading Assistant** is a multi-agent AI system that automates the grading process while maintaining human oversight for critical decisions. The system:

1. **Validates rubrics** before evaluation begins
2. **Evaluates submissions** against multiple criteria in parallel
3. **Aggregates scores** with detailed justifications
4. **Requests human approval** for edge cases (failing or exceptional grades)
5. **Generates constructive feedback** for students

### Why Agents?

Traditional automation struggles with the nuanced nature of academic evaluation. AI agents excel here because:

- **Reasoning**: Agents can understand context and apply judgment
- **Specialization**: Different agents focus on different criteria
- **Collaboration**: Agents work together like a grading committee
- **Oversight**: Human-in-the-loop ensures quality control

---

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
│  │     Validates rubric structure        │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     2. ParallelAgent                  │                       │
│  │     ┌────────────────────────────┐   │                       │
│  │     │ CriterionGrader1           │   │ ← grade_criterion()   │
│  │     │ CriterionGrader2           │   │                       │
│  │     │ CriterionGrader3           │   │                       │
│  │     └────────────────────────────┘   │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     3. AggregatorAgent               │ ← calculate_score()   │
│  │     Consolidates all grades           │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     4. ApprovalAgent                  │ ← Human-in-the-Loop  │
│  │     (If score < 50% or > 90%)        │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  ┌──────────────────────────────────────┐                       │
│  │     5. FeedbackGeneratorAgent        │                       │
│  │     Creates constructive feedback     │                       │
│  └──────────────────────────────────────┘                       │
│                          ↓                                       │
│  Output: Grade + Detailed Feedback + Justifications             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature                         | Description                                                                      |
| ------------------------------- | -------------------------------------------------------------------------------- |
| 🔍**Rubric Validation**   | Ensures rubrics are complete before evaluation                                   |
| ⚡**Parallel Grading**    | Multiple criteria evaluated simultaneously                                       |
| 🧮**Smart Aggregation**   | Calculates final scores with letter grades                                       |
| 👤**Human Oversight**     | Teacher approval for edge cases                                                  |
| 💬**Rich Feedback**       | Constructive, actionable student feedback                                        |
| 💾**Persistent Sessions** | SQLite storage for grading history                                               |
| 📊**Observability**       | Comprehensive logging for audit trails                                           |
| 🧠**Context Compaction**  | Built-in ADK context manager summarizes older turns without losing critical info |

---

## 📚 Course Concepts Applied

This capstone demonstrates **6+ key concepts** from the 5-Day AI Agents Intensive Course:

| # | Concept                            | Implementation                                                                  | Course Day |
| - | ---------------------------------- | ------------------------------------------------------------------------------- | ---------- |
| 1 | **Multi-agent (Sequential)** | Validator → Graders → Aggregator → Feedback                                  | Day 1      |
| 2 | **Multi-agent (Parallel)**   | Multiple criteria graders run simultaneously                                    | Day 1      |
| 3 | **Custom Tools**             | `validate_rubric()`, `grade_criterion()`, `calculate_score()`             | Day 2      |
| 4 | **Human-in-the-Loop**        | `request_confirmation` for edge case grades                                   | Day 2      |
| 5 | **Sessions & Memory**        | `DatabaseSessionService` + context-compaction for persistent, trimmed history | Day 3      |
| 6 | **Observability**            | `LoggingPlugin` for audit trail                                               | Day 4      |
| 7 | **Gemini Model**             | Powered by Gemini 2.5 Flash-lite                                                | Bonus      |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Google API Key (for Gemini)

### Setup Overview

You can run the Smart Grading Assistant in two ways:

| Mode                 | When to use                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| 🧪**CLI Demo** | Quick local demo that runs `python agent.py` and prints the grading results in the terminal. |
| 🌐**ADK Web**  | Full interactive experience inside the ADK Web UI, mirroring the classroom workflow.           |

#### 1. CLI Demo Setup

```bash
# From the repo root
cd capstone

# Create & activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=<your key>

# Run the demo workflow
python agent.py
```

This prints the grading pipeline output (rubric validation → grading → aggregation → feedback) directly to your terminal.

##### Expected CLI Output

After running `python agent.py`, you should see a transcript similar to the following (abridged for clarity):

```
🎓 SMART GRADING ASSISTANT - DEMO
============================================================
📋 Rubric: Python Code Evaluation Rubric
📝 Submission: Fibonacci Calculator

✅ Rubric validated: 3 criteria, 100 total points
📝 Code Quality: 25/30 — Clean recursive implementation...
📝 Functionality: 35/40 — Correct logic, could optimize...
📝 Documentation: 28/30 — Good docstrings and comments...

📊 Final Score: 88/100 (88%) - Grade: B
💬 Feedback: Great work! Consider memoization for large inputs...
```

If you see rubric validation errors instead, verify that the rubric JSON is valid. If graders do not execute, confirm the submission text is loaded correctly.

#### 2. ADK Web Setup (Interactive)

1. Open a terminal **in the repository root** (`ai_agents-course-sdk-google`).
2. Ensure dependencies are installed (you can reuse the same virtual environment as above):

   ```bash
   pip install -r capstone/requirements.txt
   cp capstone/.env.example capstone/.env  # if you have not done this yet
   # set GOOGLE_API_KEY inside capstone/.env
   ```
3. Start ADK Web from the repo root (note: do **not** `cd capstone` for this mode):

   ```bash
   cd ai-agents_course_sk_google
   ```

   ```bash
   adk web
   ```

   The CLI will display a URL such as `http://127.0.0.1:8000`.
4. In the browser, create a new session for the `capstone` app and follow the assistant’s prompts:

   - **Rubric:** copy a JSON file from `capstone/examples/rubrics/` (e.g., `python_code_rubric.json` or `essay_rubric.json`) and paste it into the chat. The assistant runs `validate_rubric` automatically.
   - **Submission:** paste one of the sample submissions from `capstone/examples/submissions/` (e.g., `sample_code.py` or `sample_essay.txt`). The assistant stores it via `save_submission`.
   - Once both are provided, the assistant transfers to the `GradingPipeline`, which triggers the graders, the aggregator, the human-in-the-loop approval tool, and the feedback generator.
5. Review the results inside the UI. Logs are stored at `capstone/logs/grading_agent.log` if you need to troubleshoot.

Tip: you can replace the sample rubric/submission with your own files to evaluate different scenarios.

##### Expected ADK Web Flow

During a typical session, the Smart Grading Assistant will:

1. **Prompt for the rubric** and, once provided, call the `validate_rubric` tool.
2. **Confirm rubric validity** (or return structured errors if invalid).
3. **Ask for the student submission** and call the `save_submission` tool with the pasted text.
4. **Transfer to `GradingPipeline`**, which triggers the following agents/tools in order:
   - `ParallelGraders` → each criterion-specific `grade_criterion` tool call.
   - `AggregatorAgent` → `build_grades_payload` then `calculate_final_score`.
   - `ApprovalAgent` → `finalize_grade` (with human confirmation if <50% or >90%).
   - `FeedbackGeneratorAgent` → generates the final summary for the student.
5. **Return final results** summarizing per-criterion scores, overall grade, approval status, and feedback.

If the pipeline stops early, check the Logs tab in ADK Web; it will indicate whether a tool call failed or a guardrail blocked execution.

---

---

## 📁 Project Structure

```
capstone/
├── agent.py                  # App entry point (assembles agents/app)
├── __init__.py               # Exposes grading_app
├── agents/                   # Modularized agent definitions
│   ├── __init__.py
│   ├── aggregator.py
│   ├── approval.py
│   ├── feedback.py
│   ├── graders.py
│   ├── root.py
│   └── rubric_validator.py
├── config/                   # Settings and constants
│   ├── __init__.py
│   └── settings.py
├── plugins/                  # Custom ADK plugins
│   ├── __init__.py
│   └── rubric_guardrail.py
├── tools/                    # Function tools used by agents
│   ├── __init__.py
│   ├── build_grades_payload.py
│   ├── calculate_score.py
│   ├── grade_criterion.py
│   ├── save_submission.py
│   └── validate_rubric.py
├── tests/                    # Pytest suites for tools/workflow
│   ├── test_build_grades_payload.py
│   ├── test_calculate_score.py
│   └── test_request_grade_approval.py
├── examples/                 # Sample rubrics & submissions
│   ├── rubrics/
│   │   ├── python_code_rubric.json
│   │   └── essay_rubric.json
│   └── submissions/
│       ├── sample_code.py
│       └── sample_essay.txt
├── data/                     # SQLite session DB (created at runtime)
├── logs/                     # grading_agent.log output
├── utils/
│   ├── __init__.py
│   └── text_utils.py
├── docs/
│   └── PLAN.md
├── README.md
├── requirements.txt
├── environment.yml
├── .env.example
└── .env (local, not committed)
```

---

## 📝 Examples

### Python Code Rubric

```json
{
    "name": "Python Code Evaluation Rubric",
    "criteria": [
        {
            "name": "Code Quality",
            "max_score": 30,
            "description": "Readability, naming, PEP 8 adherence"
        },
        {
            "name": "Functionality",
            "max_score": 40,
            "description": "Correctness, edge cases, bugs"
        },
        {
            "name": "Documentation",
            "max_score": 30,
            "description": "Docstrings, comments, clarity"
        }
    ]
}
```

### Essay Rubric

```json
{
    "name": "Academic Essay Evaluation Rubric",
    "criteria": [
        {
            "name": "Thesis and Argumentation",
            "max_score": 35,
            "description": "Clarity of thesis, argument development"
        },
        {
            "name": "Organization",
            "max_score": 25,
            "description": "Structure, transitions, flow"
        },
        {
            "name": "Language",
            "max_score": 25,
            "description": "Grammar, style, word choice"
        },
        {
            "name": "Critical Thinking",
            "max_score": 15,
            "description": "Depth of analysis, originality"
        }
    ]
}
```

---

## 🗺️ Roadmap

- **Phase 1 – Core Grading (MVP)**

  - [X] Implement a multi-agent pipeline to evaluate submissions using rubrics.
  - [X] Validate rubric structure and compute final grades with detailed feedback.
- **Phase 2 – Rubric Assistant with RAG (next step)**

  - [ ] Build a RAG-powered *Rubric Assistant* to help teachers create and review rubrics:
    - Index existing rubrics and successful evaluation examples in a knowledge base.
    - Use RAG to retrieve relevant rubric excerpts, pedagogical guidance, and sample criteria.
    - Allow teachers to ask questions such as “how can I improve this criterion?” or “example rubric for a Python project?”.
- **Phase 3 – UX & Deployment**

  - [ ] Add a Streamlit frontend for uploading rubrics/submissions and reviewing grades + feedback.
  - [ ] Prepare the project for deployment on Cloud Run / Agent Engine.

## 🔮 Future Improvements

- [ ] **Streamlit Frontend**: Web interface for easy interaction
- [ ] **Batch Grading**: Process multiple submissions at once
- [ ] **Custom Rubric Builder**: UI for creating rubrics
- [ ] **Analytics Dashboard**: Track grading patterns and statistics
- [ ] **Export Options**: PDF reports, CSV exports
- [ ] **Cloud Deployment**: Deploy on Google Cloud Run
- [ ] **Multimodal Input Support**: Accept additional file formats (PDF, images, audio) and route them through specialized evaluators.
- [ ] **Prompt Evaluation & Refinement**: Add evaluation loops for prompts/responses, adjust instructions/output formatting automatically.
- [ ] **Advanced Guardrails**: Expand input/output guardrails to sanitize user uploads and enforce safe, policy-compliant responses.
- [ ] **Enhanced Human-in-the-Loop**: Introduce extra checkpoints (e.g., per-criterion approvals or rubric-change confirmations) before finalizing grades.

---

## 🙏 Acknowledgments

This project was created as part of the **5-Day AI Agents Intensive Course with Google** on Kaggle.

- [Course Page](https://www.kaggle.com/learn-guide/5-day-agents)
- [YouTube Playlist](https://www.youtube.com/playlist?list=PLqFaTIg4myu9r7uRoNfbJhHUbLp-1t1YE)

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) for details.

---

**Built with ❤️ using Google ADK and Gemini**
