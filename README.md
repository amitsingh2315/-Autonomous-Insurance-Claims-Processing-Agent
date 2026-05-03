# 🏥 Autonomous Insurance Claims Processing Agent

An end-to-end AI-powered system for processing First Notice of Loss (FNOL) insurance documents. Uses a **hybrid architecture** combining rule-based automation with LLM-powered intelligence via **LangGraph** and **Groq AI**.

---

## 🏗️ Architecture

```
PDF Input → Text Extraction → Field Extraction → Validation → Routing → Reasoning → JSON Output
              (pdfplumber)       (Groq LLM)      (rule-based)  (rule-based)  (Groq LLM)
```

| Component | Type | Technology |
|-----------|------|-----------|
| Text Extraction | Deterministic | pdfplumber |
| Field Extraction | Agentic (LLM) | Groq (Llama 3.3 70B) |
| Field Validation | Rule-based | Python |
| Claim Routing | Rule-based | Python |
| Reasoning | Agentic (LLM) | Groq (Llama 3.3 70B) |

### LangGraph Workflow

```
START → extract_text → extract_fields → validate_fields → route_claim → generate_reasoning → END
```

---

## 📁 Project Structure

```
insurance-agent/
├── data/
│   ├── generate_sample_pdf.py   # Generate sample FNOL PDF
│   └── sample_fnol.pdf          # Generated sample document
├── src/
│   ├── __init__.py
│   ├── state.py                 # Shared state definition (TypedDict)
│   ├── prompts.py               # LLM prompt templates
│   ├── extractor.py             # PDF text + LLM field extraction
│   ├── validator.py             # Rule-based field validation
│   ├── router.py                # Rule-based claim routing
│   ├── reasoning.py             # LLM reasoning generation
│   ├── graph.py                 # LangGraph workflow definition
│   ├── main.py                  # CLI entry point
│   └── api.py                   # FastAPI REST API (bonus)
├── tests/
│   └── test_pipeline.py         # Unit + integration tests
├── .env.example                 # Environment variable template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Groq API key (free at [console.groq.com](https://console.groq.com/keys))

### Steps

```bash
# 1. Clone / navigate to the project
cd insurance-agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# 5. Add your Groq API key to .env
# Edit .env and set: GROQ_API_KEY=your-actual-key

# 6. Generate sample PDF (for testing)
python data/generate_sample_pdf.py
```

---

## 📋 Usage

### CLI

```bash
# Process a PDF document
python -m src.main --pdf data/sample_fnol.pdf

# Save output to file
python -m src.main --pdf data/sample_fnol.pdf --output result.json

# Verbose logging
python -m src.main --pdf data/sample_fnol.pdf --verbose
```

### FastAPI Server

```bash
# Start the server
uvicorn src.api:app --reload --port 8000

# Process a PDF via API
curl -X POST "http://localhost:8000/process" \
  -F "file=@data/sample_fnol.pdf"

# Health check
curl http://localhost:8000/health
```

---

## 📤 Output Format

```json
{
  "extractedFields": {
    "policy_info": {
      "policy_number": "AUTO-2024-78432",
      "policyholder_name": "Robert James Mitchell",
      "effective_date_start": "2024-01-15",
      "effective_date_end": "2025-01-15"
    },
    "incident_info": {
      "incident_date": "2024-03-15",
      "incident_time": "14:35",
      "incident_location": "Intersection of Main St and Oak Ave, Springfield, IL",
      "incident_description": "..."
    },
    "involved_parties": { ... },
    "asset_details": { ... },
    "other": { ... }
  },
  "missingFields": [],
  "recommendedRoute": "Fast-track",
  "confidenceScore": 0.89,
  "reasoning": "This claim qualifies for Fast-track processing..."
}
```

---

## 🔀 Routing Rules

| Priority | Condition | Route |
|----------|-----------|-------|
| 1 (Highest) | Description contains "fraud", "inconsistent", "staged" | **Investigation** |
| 2 | Mandatory fields missing | **Manual Review** |
| 3 | Claim type = "injury" | **Specialist Queue** |
| 4 | Estimated damage < $25,000 | **Fast-track** |
| 5 (Default) | No special flags | **Standard Processing** |

---

## 🧪 Testing

```bash
# Run unit tests (no API key needed)
python -m pytest tests/ -v

# Run integration tests (requires GROQ_API_KEY)
python -m pytest tests/ -v --tb=short
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **LangGraph** | Agent workflow orchestration |
| **LangChain** | LLM abstraction layer |
| **Groq AI** | Fast LLM inference (Llama 3.3 70B) |
| **pdfplumber** | PDF text extraction |
| **FastAPI** | REST API server |
| **python-dotenv** | Environment management |

---

## 🔑 Key Design Decisions

1. **Hybrid Architecture**: Routing is purely rule-based (deterministic), while extraction and reasoning use LLM (cognitive). This ensures reliable, auditable routing decisions.

2. **Fallback Reasoning**: If the LLM fails during reasoning generation, template-based fallback ensures the pipeline never crashes.

3. **Confidence Scoring**: Based on field completeness (extraction) and rule clarity (routing).

4. **Priority-based Routing**: Rules are evaluated in strict priority order to prevent ambiguous decisions.

---

## 📄 License

MIT
