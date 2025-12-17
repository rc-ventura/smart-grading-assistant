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

| Feature | Description |
|---------|-------------|
| 🔍 **Rubric Validation** | Ensures rubrics are complete before evaluation |
| ⚡ **Parallel Grading** | Multiple criteria evaluated simultaneously |
| 🧮 **Smart Aggregation** | Calculates final scores with letter grades |
| 👤 **Human Oversight** | Teacher approval for edge cases |
| 💬 **Rich Feedback** | Constructive, actionable student feedback |
| 💾 **Persistent Sessions** | SQLite storage for grading history |
| 📊 **Observability** | Comprehensive logging for audit trails |

---

## 📚 Course Concepts Applied

This capstone demonstrates **6+ key concepts** from the 5-Day AI Agents Intensive Course:

| # | Concept | Implementation | Course Day |
|---|---------|----------------|------------|
| 1 | **Multi-agent (Sequential)** | Validator → Graders → Aggregator → Feedback | Day 1 |
| 2 | **Multi-agent (Parallel)** | Multiple criteria graders run simultaneously | Day 1 |
| 3 | **Custom Tools** | `validate_rubric()`, `grade_criterion()`, `calculate_score()` | Day 2 |
| 4 | **Human-in-the-Loop** | `request_confirmation` for edge case grades | Day 2 |
| 5 | **Sessions & Memory** | `DatabaseSessionService` for persistence | Day 3 |
| 6 | **Observability** | `LoggingPlugin` for audit trail | Day 4 |
| 7 | **Gemini Model** | Powered by Gemini 2.5 Flash | Bonus |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Google API Key (for Gemini)

### Setup

```bash
# Clone the repository
cd capstone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

---

## 📖 Usage

### Basic Usage

```bash
python agent.py
```

This runs a demo that:
1. Loads the Python code rubric
2. Evaluates the sample Fibonacci submission
3. Displays the grading results

### Programmatic Usage

```python
import asyncio
from agent import grade_submission

rubric = {
    "name": "My Rubric",
    "criteria": [
        {"name": "Quality", "max_score": 50, "description": "..."},
        {"name": "Completeness", "max_score": 50, "description": "..."}
    ]
}

submission = "Student's work here..."

result = asyncio.run(grade_submission(submission, rubric))
print(result)
```

### Expected Output

```
🎓 SMART GRADING ASSISTANT - DEMO
============================================================

📋 Rubric: Python Code Evaluation Rubric
📝 Submission: Fibonacci Calculator

⏳ Starting evaluation...

============================================================
📊 EVALUATION RESULTS
============================================================

✅ Rubric validated: 3 criteria, 100 total points

📝 Code Quality: 25/30
   Clean recursive implementation with good naming conventions...

📝 Functionality: 35/40
   Correctly calculates Fibonacci numbers, but O(2^n) complexity...

📝 Documentation: 28/30
   Good docstrings, clear comments explaining the logic...

📊 Final Score: 88/100 (88%) - Grade: B

💬 Feedback:
   Great work on this Fibonacci implementation! Your code is clean
   and well-documented. Consider using memoization to improve
   performance for larger inputs...

============================================================
✅ Session ID: grading_a1b2c3d4
============================================================
```

---

## 📁 Project Structure

```
capstone/
├── agent.py                    # Main entry point with all agents
├── tools/
│   ├── __init__.py
│   ├── validate_rubric.py      # Rubric validation tool
│   ├── grade_criterion.py      # Criterion grading tool
│   └── calculate_score.py      # Score calculation tool
├── agents/
│   └── __init__.py
├── examples/
│   ├── rubrics/
│   │   ├── python_code_rubric.json
│   │   └── essay_rubric.json
│   └── submissions/
│       ├── sample_code.py
│       └── sample_essay.txt
├── .env.example
├── requirements.txt
├── PLAN.md                     # Development plan
└── README.md                   # This file
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
  - [x] Implementar pipeline multi-agente para avaliação de submissões usando rúbricas.
  - [x] Validar estrutura de rúbricas e calcular notas finais com feedback detalhado.

- **Phase 2 – Rubric Assistant com RAG (próximo passo)**  
  - [ ] Criar um *Rubric Assistant* baseado em RAG para apoiar professores na criação e revisão de rúbricas:
    - Indexar rúbricas existentes e exemplos de avaliações bem-sucedidas em uma base de conhecimento.
    - Usar RAG para recuperar trechos relevantes de rúbricas, orientações pedagógicas e exemplos de critérios.
    - Permitir que o professor faça perguntas como "como melhorar este critério?" ou "exemplo de rubrica para projeto de código Python".

- **Phase 3 – UX & Deployment**  
  - [ ] Adicionar frontend em Streamlit para upload de rúbricas e submissões, visualização de notas e feedback.
  - [ ] Preparar o projeto para deploy em ambientes como Cloud Run / Agent Engine.

## 🔮 Future Improvements

- [ ] **Streamlit Frontend**: Web interface for easy interaction
- [ ] **Batch Grading**: Process multiple submissions at once
- [ ] **Custom Rubric Builder**: UI for creating rubrics
- [ ] **Analytics Dashboard**: Track grading patterns and statistics
- [ ] **Export Options**: PDF reports, CSV exports
- [ ] **Cloud Deployment**: Deploy on Google Cloud Run

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
