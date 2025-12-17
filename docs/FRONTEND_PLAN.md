# 🖥️ Frontend Implementation Plan

> Streamlit UI for the Smart Grading Assistant

## 📋 Overview

This document outlines the phased implementation of a Streamlit frontend that connects to the existing Smart Grading Assistant backend (ADK agents, tools, and grading pipeline).

### Current State (Post-Implementation)

- **Backend:** Multi-agent grading pipeline ready (Validator, ParallelGraders, Aggregator, Approval, Feedback, RubricGuardrail, DatabaseSessionService).
- **UI (implemented):**
  - `ui/app.py` refactored with sidebar + main area, full session-state init.
  - Components: `sidebar.py`, `chat.py`, `results.py`.
  - Services: `ui/services/grading.py` (currently simulating pipeline; ready to swap to ADK Runner).
  - Utilities: `ui/utils/formatters.py`.
  - Docs updated: `specs/1-streamlit-grading-ui/quickstart.md`, README Streamlit section, tasks.md all done.

**Next delta:** replace simulated grading in `ui/services/grading.py` with real ADK Runner events (see Backend Integration below).

### Goal

Build a production-ready Streamlit UI that:
1. Connects to the existing grading backend
2. Provides intuitive UX for teachers
3. Supports future RAG-based rubric assistant

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Sidebar    │  │  Main Chat  │  │  Results    │                 │
│  │  (Setup)    │  │  (Grading)  │  │  (Feedback) │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
│        │                │                │                          │
│        └────────────────┼────────────────┘                          │
│                         │                                            │
│                         ▼                                            │
│              ┌─────────────────────┐                                │
│              │  st.session_state   │                                │
│              │  (UI state only)    │                                │
│              └─────────────────────┘                                │
│                         │                                            │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │  services/          │    │  ADK Runner         │                │
│  │  gemini_client.py   │    │  (grading_app)      │                │
│  │  (chat helpers)     │    │                     │                │
│  └─────────────────────┘    └─────────────────────┘                │
│           │                          │                              │
│           ▼                          ▼                              │
│  ┌─────────────────────────────────────────────────┐               │
│  │              Gemini API                          │               │
│  │  (google-genai SDK for chat + ADK for agents)   │               │
│  └─────────────────────────────────────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📐 UI Layout Design

```
┌──────────────────────────────────────────────────────────────────────┐
│  🎓 Smart Grading Assistant                              [Settings]  │
├──────────────┬───────────────────────────────────────────────────────┤
│              │                                                        │
│  SIDEBAR     │                    MAIN AREA                          │
│              │                                                        │
│  ┌────────┐  │  ┌──────────────────────────────────────────────────┐│
│  │ Setup  │  │  │                                                  ││
│  │        │  │  │  📋 Rubric Status: ✅ Valid (3 criteria)        ││
│  │ Rubric │  │  │  📝 Submission: ✅ Loaded (45 lines)            ││
│  │ Upload │  │  │                                                  ││
│  │   📁   │  │  └──────────────────────────────────────────────────┘│
│  │        │  │                                                        │
│  │ ─────  │  │  ┌──────────────────────────────────────────────────┐│
│  │        │  │  │                                                  ││
│  │ Quick  │  │  │  💬 CHAT / GRADING INTERFACE                    ││
│  │ Actions│  │  │                                                  ││
│  │        │  │  │  [User]: Please grade this submission           ││
│  │ [Grade]│  │  │                                                  ││
│  │ [Reset]│  │  │  [Assistant]: Validating rubric...              ││
│  │        │  │  │  ✅ Rubric valid: 3 criteria, 100 points        ││
│  │ ─────  │  │  │                                                  ││
│  │        │  │  │  [Assistant]: Grading in progress...            ││
│  │ History│  │  │  📊 Code Quality: 25/30                         ││
│  │        │  │  │  📊 Functionality: 35/40                        ││
│  │ Session│  │  │  📊 Documentation: 28/30                        ││
│  │ #1234  │  │  │                                                  ││
│  │        │  │  │  🎯 Final Score: 88/100 (B)                     ││
│  └────────┘  │  │                                                  ││
│              │  │  [Input: Ask a question or request grading...]  ││
│              │  └──────────────────────────────────────────────────┘│
│              │                                                        │
│              │  ┌──────────────────────────────────────────────────┐│
│              │  │  📝 FEEDBACK PANEL (expandable)                  ││
│              │  │                                                  ││
│              │  │  Strengths: Clean implementation, good docs...  ││
│              │  │  Areas for improvement: Consider memoization... ││
│              │  │  Suggestions: Add type hints, unit tests...     ││
│              │  └──────────────────────────────────────────────────┘│
└──────────────┴───────────────────────────────────────────────────────┘
```

---

## 🚀 Implementation Phases

### Phase 1: Core Grading UI (MVP) — ✅ Complete (UI built; backend hook still simulated)
**Goal:** Functional UI wired to grading pipeline  
**Status:** UI done; replace simulated pipeline with ADK Runner to finish.

#### 1.1 Sidebar Setup — ✅
- [x] Rubric upload (JSON file or paste)
- [x] Submission upload (text file or paste)
- [x] Quick action buttons: "Start Grading", "Reset"
- [x] Session info display

#### 1.2 Main Chat Interface — ✅
- [x] Chat-style progress display (validating → grading → aggregating → feedback)
- [x] Per-criterion scores as they complete
- [x] Messages/history persisted in session state

#### 1.3 Backend Integration — ⏳ (Simulated; swap to Runner)
- [ ] Connect UI to ADK `Runner` for grading workflow (replace simulation in `ui/services/grading.py`)
- [ ] Use existing `DatabaseSessionService`
- [ ] Stream agent responses/events to UI

#### 1.4 Results Display — ✅
- [x] Feedback panel (structured)
- [x] Download results as JSON
- [x] Copy feedback to clipboard

**Files to create/modify:**
```
ui/
├── app.py              # Main Streamlit app (refactor existing)
├── components/
│   ├── sidebar.py      # Sidebar components
│   ├── chat.py         # Chat interface
│   └── results.py      # Results/feedback display
├── services/
│   └── grading.py      # Bridge to ADK runner
└── utils/
    └── formatters.py   # Format grades, feedback for display
```

---

### Phase 2: Enhanced UX
**Goal:** Polish and improve user experience (pending)

#### 2.1 Rubric Management
- [ ] Rubric preview with validation status
- [ ] Edit rubric inline (add/remove criteria)
- [ ] Save rubrics to library (local storage or DB)
- [ ] Load rubrics from `examples/rubrics/`

#### 2.2 Submission Handling
- [ ] Syntax highlighting for code submissions
- [ ] Support multiple file types (`.py`, `.txt`, `.md`)
- [ ] Submission preview with line numbers

#### 2.3 Human-in-the-Loop UI
- [ ] Modal/dialog for approval requests
- [ ] Show approval reason (score < 50% or > 90%)
- [ ] Allow teacher to adjust grade before finalizing

#### 2.4 Session Management
- [ ] List past grading sessions
- [ ] Resume incomplete sessions
- [ ] Compare grades across sessions

---

### Phase 3: RAG Rubric Assistant
**Goal:** AI-powered rubric creation and improvement (future)

#### 3.1 Knowledge Base
- [ ] Index existing rubrics from `examples/rubrics/`
- [ ] Add pedagogical guidelines and best practices
- [ ] Store successful grading examples

#### 3.2 Rubric Assistant Chat
- [ ] Separate chat mode for rubric creation
- [ ] RAG retrieval for relevant examples
- [ ] Suggestions based on subject/level

#### 3.3 Rubric Generation
- [ ] Generate rubric from description
- [ ] Improve existing rubric with AI suggestions
- [ ] Validate generated rubrics automatically

**New files:**
```
services/
├── rag/
│   ├── indexer.py      # Index rubrics and examples
│   ├── retriever.py    # RAG retrieval
│   └── assistant.py    # Rubric assistant agent
```

---

### Phase 4: Production Ready
**Goal:** Deploy and scale (future)

#### 4.1 Authentication
- [ ] Teacher login (Google OAuth or simple auth)
- [ ] Per-teacher session isolation
- [ ] Role-based access (teacher vs admin)

#### 4.2 Persistence
- [ ] PostgreSQL for production sessions
- [ ] Cloud storage for rubrics/submissions
- [ ] Export/import functionality

#### 4.3 Deployment
- [ ] Dockerize application
- [ ] Deploy to Cloud Run
- [ ] Set up CI/CD pipeline

#### 4.4 Analytics
- [ ] Grading statistics dashboard
- [ ] Common feedback patterns
- [ ] Time tracking per grading session

---

## 🔌 Backend Integration Details

### Option A: Direct ADK Runner (Recommended next step)

Replace the simulated pipeline in `ui/services/grading.py` with calls to `runner`/`grading_app`:

```python
from capstone.agent import runner, grading_app
from google.adk import types as adk_types

async def run_grading_session(rubric_json: str, submission_text: str, session_id: str | None = None):
    # 1) Ensure session
    session = await runner.session_service.get_session(
        app_name=grading_app.name,
        user_id="teacher",
        session_id=session_id,
    )

    # 2) Send rubric (validate)
    async for event in runner.run_async(
        user_id="teacher",
        session_id=session.id,
        new_message=adk_types.Content(role="user", parts=[adk_types.Part(text=rubric_json)]),
    ):
        yield {"type": "event", "data": event}

    # 3) Send submission (grade)
    async for event in runner.run_async(
        user_id="teacher",
        session_id=session.id,
        new_message=adk_types.Content(role="user", parts=[adk_types.Part(text=submission_text)]),
    ):
        yield {"type": "event", "data": event}
```

### Option B: HTTP API (For Future Scaling)

If you later want to separate frontend and backend:

```python
# api/main.py (FastAPI)

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/grading/start")
async def start_grading(rubric: str, submission: str):
    session_id = create_session()
    return {"session_id": session_id}

@app.post("/grading/{session_id}/message")
async def send_message(session_id: str, message: str):
    return StreamingResponse(
        stream_grading_response(session_id, message),
        media_type="text/event-stream",
    )
```

---

## 📊 Session State Design

### UI State (`st.session_state`)

```python
# What the UI keeps locally
st.session_state = {
    # Setup state
    "setup_complete": False,
    "rubric_json": None,
    "rubric_valid": False,
    "submission_text": None,
    
    # Grading state
    "grading_session_id": None,
    "grading_in_progress": False,
    "current_step": "idle",  # idle | validating | grading | aggregating | feedback
    
    # Results
    "grades": {},           # {criterion: {score, max_score, notes}}
    "final_score": None,
    "feedback": None,
    
    # Chat history (for display only)
    "messages": [],
    
    # Human-in-the-loop
    "pending_approval": False,
    "approval_reason": None,
}
```

### Backend State (ADK Session)

The ADK session (managed by `DatabaseSessionService`) stores:
- `rubric` → parsed rubric dict
- `rubric_validation` → validation result
- `submission_text` → student submission
- `grade_*` → per-criterion grades
- `aggregation_result` → final score
- `final_feedback` → generated feedback

The UI should **not** duplicate this; it reads from the backend when needed.

---

## 🎯 Key Decisions

### 1. Chat vs. Wizard UI

**Decision:** Hybrid approach
- **Sidebar:** Wizard-style setup (upload rubric, submission)
- **Main area:** Chat for interaction and results

**Rationale:** Teachers want quick setup but also conversational interaction for questions/clarifications.

### 2. Streaming vs. Polling

**Decision:** Streaming (where possible)
- Use `st.write_stream` for Gemini responses
- Use `st.status` for grading progress
- Fall back to polling for ADK events if needed

### 3. Session Ownership

**Decision:** Backend owns grading state, UI owns display state
- UI sends rubric/submission to backend
- Backend runs pipeline, stores results
- UI reads results for display
- UI keeps only what's needed for rendering

---

## 📝 Next Steps (Updated)

1. Swap simulated grading in `ui/services/grading.py` for real ADK Runner calls (see Option A).
2. Add syntax highlighting + line numbers for submission preview (Phase 2).
3. Add approval modal/flow for <50% or >90% scores (Phase 2).
4. Optional polish: session history/resume; rubric preview enhancements.

---

## 📚 References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google ADK Documentation](https://google.github.io/adk/)
- [Gemini API (google-genai)](https://ai.google.dev/gemini-api/docs)
- [README.md](../README.md) - Project overview
- [PLAN.md](./PLAN.md) - Original implementation plan
