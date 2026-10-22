from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from crew import medical_crew

MAX_SYMPTOMS_LENGTH = 1000
MAX_TEST_RESULTS_LENGTH = 3000

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
        result = await medical_crew.kickoff_async(
    inputs={
        "symptoms": patient_data.symptoms,
        "test_results": patient_data.test_results,
    }
)

        return {"result": str(result)}

    except Exception as exc:
        print(f"Analysis error: {exc}")
        raise HTTPException(
            status_code=500,
            detail="The analysis could not be completed. Please try again later.",
        ) from exc
