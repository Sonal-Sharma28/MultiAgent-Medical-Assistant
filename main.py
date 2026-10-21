from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from crew import medical_crew

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
    symptoms: str
    test_results: str = ""


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
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
