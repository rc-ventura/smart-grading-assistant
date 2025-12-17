# Research: Smart Grading Streamlit UI

**Feature**: SmartGradingStreamlitUI  
**Date**: 2025-12-10  
**Status**: Complete

---

## 1. Streamlit + ADK Integration

### Decision
Use direct Python imports to call ADK Runner from Streamlit, not HTTP API.

### Rationale
- Simplest approach for MVP
- No additional infrastructure needed
- ADK Runner already supports async iteration
- Same process = no serialization overhead

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| FastAPI wrapper | Extra complexity, not needed for single-user |
| gRPC | Overkill for local/single-tenant use |
| Message queue | Unnecessary for synchronous grading flow |

---

## 2. Streaming vs Polling for Grading Progress

### Decision
Use Streamlit's `st.status` and `st.empty` for progress updates, with async iteration over ADK Runner events.

### Rationale
- Streamlit doesn't support true WebSocket streaming
- `st.status` provides good UX for multi-step processes
- ADK Runner's `run_async` yields events that can be processed incrementally
- `st.empty().write()` can update in place

### Implementation Pattern
```python
with st.status("Grading in progress...", expanded=True) as status:
    async for event in runner.run_async(...):
        if event.type == "agent_start":
            st.write(f"Running: {event.agent_name}")
        elif event.type == "tool_result":
            st.write(f"Result: {event.data}")
    status.update(label="Grading complete!", state="complete")
```

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Polling endpoint | Adds complexity, worse UX |
| WebSocket | Not natively supported by Streamlit |
| Full page refresh | Poor UX, loses context |

---

## 3. Session State Architecture

### Decision
UI state in `st.session_state`, grading state in ADK session (SQLite/DB).

### Rationale
- Clear separation of concerns
- Backend is source of truth for grades
- UI state is ephemeral (display only)
- Supports session resume from backend

### State Boundaries
| Location | Data |
|----------|------|
| `st.session_state` | UI flags, display messages, form inputs |
| ADK Session | Rubric, submission, grades, feedback |

---

## 4. Component Structure

### Decision
Split UI into `sidebar.py`, `chat.py`, `results.py` components.

### Rationale
- Follows Streamlit best practices
- Each component has single responsibility
- Easier to test and maintain
- Matches spec layout (sidebar + main area)

### File Responsibilities
| File | Responsibility |
|------|----------------|
| `app.py` | Entry point, layout, state init |
| `sidebar.py` | Rubric/submission input, actions |
| `chat.py` | Progress display, messages |
| `results.py` | Scores, feedback, export |
| `services/grading.py` | ADK Runner bridge |

---

## 5. Human-in-the-Loop UI

### Decision
Use `st.dialog` (Streamlit 1.33+) or `st.expander` with confirmation buttons.

### Rationale
- Native Streamlit components
- No JavaScript needed
- Clear modal-like UX for approval flow

### Implementation Pattern
```python
if st.session_state.pending_approval:
    with st.expander("⚠️ Approval Required", expanded=True):
        st.write(f"Reason: {st.session_state.approval_reason}")
        col1, col2 = st.columns(2)
        if col1.button("Approve"):
            approve_grade()
        if col2.button("Adjust"):
            show_adjustment_form()
```

---

## 6. Error Handling

### Decision
Display errors inline with recovery options, log to backend.

### Rationale
- Teacher should never be stuck
- Errors should be actionable
- Backend logging for debugging

### Error Categories
| Category | UI Response |
|----------|-------------|
| Rubric validation | Show errors, allow re-upload |
| Grading failure | Show error, offer retry |
| Network error | Show message, offer retry |
| Session error | Offer reset |

---

## 7. Export Functionality

### Decision
JSON download via `st.download_button`, clipboard via `st.code` with copy.

### Rationale
- Native Streamlit components
- No external dependencies
- JSON is machine-readable for integration

### Export Format
```json
{
  "session_id": "...",
  "rubric": {...},
  "submission_preview": "...",
  "grades": [...],
  "final_score": {...},
  "feedback": {...},
  "timestamp": "..."
}
```

---

## 8. Testing Strategy

### Decision
Unit tests for services, integration tests for components.

### Rationale
- Services have clear inputs/outputs
- Components need Streamlit context
- Mock ADK Runner for unit tests

### Test Structure
| Test Type | Target | Approach |
|-----------|--------|----------|
| Unit | `services/grading.py` | Mock Runner, test logic |
| Unit | `utils/formatters.py` | Pure functions |
| Integration | Components | Streamlit testing utilities |
| E2E | Full flow | Manual or Playwright |

---

## Summary

All technical decisions are resolved. No NEEDS CLARIFICATION items remain. Ready for Phase 1 implementation.
