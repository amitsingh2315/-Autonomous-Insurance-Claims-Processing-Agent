# 🚀 Autonomous Insurance Claims Processing Agent

🔗 **Live Demo:** https://autonomous-insurance-claims-processing.onrender.com/
📦 **GitHub Repo:** (https://github.com/amitsingh2315/-Autonomous-Insurance-Claims-Processing-Agent)

---

## 📌 Overview

This project is an **AI-powered autonomous insurance claims processing system** that analyzes FNOL (First Notice of Loss) documents and automatically:

* Extracts key claim information
* Identifies missing or inconsistent fields
* Classifies claims
* Routes them to the correct workflow
* Assigns claims to relevant employees
* Provides human-readable reasoning

---

## 🎯 Problem Statement

As per assignment :

Build an intelligent system that:

* Extracts structured data from FNOL documents
* Detects missing fields
* Applies business rules
* Routes claims intelligently
* Generates explanation for decisions

---

## 🧠 Key Features

### ✅ 1. Smart Data Extraction

* Extracts:

  * Policy details
  * Incident info
  * Parties involved
  * Asset details
  * Claim metadata

---

### ✅ 2. Missing Field Detection

* Automatically detects incomplete claims
* Flags missing mandatory fields

---

### ✅ 3. Rule-Based Claim Routing

| Condition       | Route            |
| --------------- | ---------------- |
| Damage < 25,000 | Fast-track       |
| Missing fields  | Manual Review    |
| Fraud keywords  | Investigation    |
| Injury claim    | Specialist Queue |

---

### ✅ 4. AI Reasoning (LLM)

* Uses Groq LLM
* Generates human-readable explanation

---

### ✅ 5. Employee Assignment System (🔥 Bonus)

* Claims auto-assigned based on:

  * Route type
  * Employee role
  * Current workload

---

### ✅ 6. Decision Flow Visualization

* Flowchart-style explanation
* Easy to understand UI/UX

---

### ✅ 7. Confidence Score

* Smart confidence based on:

  * Data completeness
  * Rule certainty
  * Fraud signals

---

## 🏗️ Architecture

```text
PDF Upload → Text Extraction → Field Extraction (LLM)
→ Validation → Routing Engine → Assignment
→ Reasoning (LLM) → Output UI
```

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* Python
* LangGraph
* LangChain
* Groq LLM

### Frontend

* HTML, CSS, JavaScript

### Deployment

* Render (Full-stack deployment)

---

## 📂 Project Structure

```
backend/
  ├── api.py
  ├── extractor.py
  ├── router.py
  ├── validator.py
  ├── reasoning.py
  ├── graph.py

frontend/
  ├── index.html
  ├── static/
       ├── app.js
       ├── style.css

render.yaml
requirements.txt
```

---

## ⚙️ How to Run Locally

```bash
git clone <repo-link>
cd project-folder

pip install -r requirements.txt

uvicorn backend.api:app --reload
```

👉 Open:

```
http://127.0.0.1:8000
```

---

## 🌐 Deployment

This project is deployed on **Render** as a single service:

* FastAPI serves backend + frontend
* Static files served internally
* No separate frontend hosting required

---

## 📊 Sample Output

```json
{
  "recommendedRoute": "Fast-track",
  "missingFields": [],
  "confidenceScore": 0.91
}
```

---

## 🎥 Demo (Optional but recommended)

👉 Add here:

* Screen recording
* Loom video link

---

## 🧠 Learnings

* Built end-to-end AI system
* Integrated LLM with rule-based logic
* Designed agentic workflow using LangGraph
* Deployed full-stack app on cloud

---

## 🚀 Future Improvements

* Real-time fraud detection ML model
* Database integration
* Authentication system
* Multi-document support

---

## 👨‍💻 Author

**Amit Singh**
B.Tech CSE | Data Science
AI/ML Engineer

---

## ⭐ If you like this project

Give it a star ⭐ on GitHub
