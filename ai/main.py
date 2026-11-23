

#Run from the project root:  uvicorn main:app --app-dir ai --reload --port 8000
# Or from the ai folder: uvicorn main:app  --reload --port 8000
import os
import threading
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
from crew import build_crew  # noqa: E402  (after load_dotenv so keys are available)

app = FastAPI(title="CrewAI Sales Outreach")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

JOBS: dict[str, dict] = {}


class Lead(BaseModel):
    lead_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=200)
    decision_maker: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    milestone: str = Field(..., min_length=1, max_length=300)


def run_job(job_id: str, lead: Lead):
    job = JOBS[job_id]

    def on_task(_output):
        job["stage"] = "outreach"

    try:
        job["stage"] = "profiling"
        result = build_crew(task_callback=on_task).kickoff(inputs=lead.model_dump())
        job["profile"] = result.tasks_output[0].raw
        job["campaign"] = result.tasks_output[1].raw
        job["status"], job["stage"] = "done", "done"
    except Exception as e:  # surface a readable error to the UI
        job["status"], job["error"] = "error", f"{type(e).__name__}: {e}"


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "llm_key": any(os.getenv(k) for k in ("GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")),
        "serper_key": bool(os.getenv("SERPER_API_KEY")),
    }


@app.post("/api/run")
def start(lead: Lead):
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(400, "SERPER_API_KEY is missing. Add it to .env in the project root and restart the server.")
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "stage": "queued"}
    threading.Thread(target=run_job, args=(job_id, lead), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


FRONTEND = ROOT / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
