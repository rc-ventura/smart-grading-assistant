# Quickstart: Smart Grading Streamlit UI

**Feature**: SmartGradingStreamlitUI  
**Version**: 1.0.0 (MVP)  
**Last Updated**: 2025-12-10

---

## Prerequisites

- Python 3.11+
- Conda environment `capstone-env` (or virtualenv)
- Google API key with Gemini access
- Streamlit installed

---

## 1. Environment Setup

```bash
# Navigate to project
cd capstone

# Activate environment
conda activate capstone-env

# Install dependencies (if needed)
pip install streamlit google-genai

# Set up Streamlit secrets
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
GOOGLE_API_KEY = "your-api-key-here"
EOF
```

---

## 2. Project Structure

```
ui/
├── app.py                    # Streamlit entrypoint
├── components/
│   ├── __init__.py
│   ├── sidebar.py            # Rubric & submission input
│   ├── chat.py               # Progress & messages
│   └── results.py            # Scores & feedback
├── services/
│   ├── __init__.py
│   └── grading.py            # Grading pipeline bridge
└── utils/
    ├── __init__.py
    └── formatters.py         # Display helpers
```

---

## 3. Run the Application

```bash
# From capstone directory
streamlit run ui/app.py

# Opens browser at http://localhost:8501
```

For development with auto-reload:
```bash
streamlit run ui/app.py --server.runOnSave true
```

---

## 4. Usage Guide

### Step 1: Upload Rubric

In the sidebar, use either tab:
- **Upload**: Click to upload a `.json` file
- **Paste**: Paste rubric JSON directly

**Example rubric format:**
```json
{
  "name": "Python Code Rubric",
  "criteria": [
    {
      "name": "Code Quality",
      "max_score": 30,
      "description": "Clean, readable, well-organized code"
    },
    {
      "name": "Functionality",
      "max_score": 40,
      "description": "Code works correctly and handles edge cases"
    },
    {
      "name": "Documentation",
      "max_score": 30,
      "description": "Clear comments and docstrings"
    }
  ]
}
```

Wait for validation: ✅ Valid or ❌ Invalid with errors

### Step 2: Upload Submission

In the sidebar, use either tab:
- **Upload**: Click to upload `.py`, `.txt`, or `.md` file
- **Paste**: Paste student code/text directly

Preview appears showing first 500 characters.

### Step 3: Start Grading

1. Click **🚀 Start Grading** button (enabled when rubric valid + submission loaded)
2. Watch progress in main area:
   - 🔍 Validating rubric...
   - 📊 Grading each criterion...
   - 🧮 Aggregating scores...
   - 💬 Generating feedback...
   - ✅ Complete!

### Step 4: Review Results

When grading completes:
1. **Final Score Card**: Total, percentage, letter grade
2. **Per-Criterion Table**: Score breakdown with notes
3. **Feedback Panel**: Strengths, improvements, suggestions
4. **Export Options**:
   - 📥 Download JSON
   - 📋 Copy feedback text

### Step 5: Reset or Grade Again

- Click **🔄 Reset** to clear everything and start over
- Upload new rubric/submission to grade another student

---

## 5. Sample Rubric

Copy this to test the UI:

```json
{
  "name": "Python Assignment Rubric",
  "criteria": [
    {
      "name": "Code Quality",
      "max_score": 25,
      "description": "Code is clean, readable, follows PEP 8"
    },
    {
      "name": "Functionality",
      "max_score": 35,
      "description": "All requirements met, handles edge cases"
    },
    {
      "name": "Documentation",
      "max_score": 20,
      "description": "Clear docstrings and inline comments"
    },
    {
      "name": "Testing",
      "max_score": 20,
      "description": "Includes unit tests with good coverage"
    }
  ]
}
```

---

## 6. Troubleshooting

### "GOOGLE_API_KEY not found"

```bash
# Check secrets file
cat .streamlit/secrets.toml

# Or set environment variable
export GOOGLE_API_KEY="your-key"
```

### "Module not found: ui.components"

```bash
# Run from capstone directory
cd /path/to/capstone
streamlit run ui/app.py
```

### "Rubric validation failed"

- Check JSON syntax at jsonlint.com
- Required fields: `name`, `criteria[]`
- Each criterion needs: `name`, `max_score`, `description`

### "Start Grading button disabled"

- Ensure rubric shows ✅ Valid
- Ensure submission shows ✅ Loaded
- Both must be valid to enable grading

---

## 7. Configuration

### Streamlit config (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#212121"

[server]
runOnSave = true
maxUploadSize = 10
```

---

## 8. Next Steps

See [plan.md](./plan.md) for the full roadmap:

1. **Phase 2**: Rubric preview, syntax highlighting, session history
2. **Phase 3**: RAG rubric assistant
3. **Phase 4**: Authentication, PostgreSQL, Cloud Run deployment
