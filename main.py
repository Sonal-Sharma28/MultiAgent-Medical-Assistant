import asyncio
import json
import logging
from queue import Empty

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from crew import medical_crew
from workflow_progress import (
    ProgressSession,
    active_progress_session,
)

MAX_SYMPTOMS_LENGTH = 1000
MAX_TEST_RESULTS_LENGTH = 3000
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical Information Assistant")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PatientData(BaseModel):
    symptoms: str = Field(max_length=MAX_SYMPTOMS_LENGTH)
    test_results: str = Field(default="", max_length=MAX_TEST_RESULTS_LENGTH)

    @field_validator("symptoms", "test_results", mode="before")
    @classmethod
    def trim_input(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("symptoms", mode="before")
    @classmethod
    def require_symptoms(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("Symptoms must not be empty or whitespace.")
        return value


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "max_symptoms_length": MAX_SYMPTOMS_LENGTH,
            "max_test_results_length": MAX_TEST_RESULTS_LENGTH,
        },
    )


@app.post("/api/analyze")
async def analyze_patient(patient_data: PatientData):
    try:
        return {"result": await run_analysis(patient_data)}
    except Exception as exc:
        logger.error("Analysis failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="The analysis could not be completed. Please try again later.",
        ) from exc


async def run_analysis(
    patient_data: PatientData,
    progress_session: ProgressSession | None = None,
) -> str:
    token = active_progress_session.set(progress_session)
    try:
        result = await medical_crew.kickoff_async(
            inputs={
                "symptoms": patient_data.symptoms,
                "test_results": patient_data.test_results,
            }
        )
        return str(result)
    finally:
        active_progress_session.reset(token)


def format_sse(event: str, data: dict[str, str]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/analyze/progress")
async def analyze_patient_with_progress(patient_data: PatientData):
    session = ProgressSession()

    async def event_stream():
        yield format_sse("started", {"request_id": session.request_id})
        analysis_task = asyncio.create_task(run_streamed_analysis(patient_data, session))

        try:
            while True:
                try:
                    message = session.messages.get_nowait()
                except Empty:
                    await asyncio.sleep(0.05)
                    continue

                yield format_sse(message.event, message.data)
                if message.terminal:
                    break
        finally:
            if not analysis_task.done():
                analysis_task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def run_streamed_analysis(
    patient_data: PatientData,
    session: ProgressSession,
) -> None:
    try:
        result = await run_analysis(patient_data, session)
    except Exception as exc:
        logger.error("Progress analysis failed (%s)", type(exc).__name__)
        session.publish_failure()
    else:
        session.publish_result(result)
