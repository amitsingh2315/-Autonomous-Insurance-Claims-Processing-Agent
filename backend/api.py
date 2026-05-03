"""
FastAPI server for the Insurance Claims Processing Agent.

Serves both the REST API and the frontend UI.

Usage:
    uvicorn backend.api:app --reload --port 8000
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .graph import run_pipeline, format_output
from .assignment import EMPLOYEES

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent   # insurance-agent/
FRONT_DIR = BASE_DIR / "frontend"

# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Insurance Claims Processing Agent",
    description="Autonomous FNOL document processing — hybrid AI (rule-based + Groq LLM)",
    version="1.0.0",
)

# Allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend assets (CSS / JS / images)
if FRONT_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONT_DIR / "static")), name="static")


# ── API routes ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "insurance-claims-agent"}

@app.get("/employees")
async def get_employees() -> JSONResponse:
    """Return the employee directory."""
    return JSONResponse(content={"employees": EMPLOYEES})


@app.post("/process")
async def process_claim(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload an FNOL PDF → returns structured JSON with routing decision.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    logger.info(f"Received file: {file.filename}")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = run_pipeline(tmp_path)
        output = format_output(result)
        logger.info(f"Processing complete -> Route: {output['recommendedRoute']}")
        return JSONResponse(content=output)

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Claim processing failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ── Frontend – serve index.html for every non-API route ────────────────────

@app.get("/")
async def root() -> FileResponse:
    index = FRONT_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"message": "Insurance Claims API running. Frontend not found."})
