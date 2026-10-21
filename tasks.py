
from crewai import Task

from agents import (
    symptom_analyst,
    test_interpreter,
    diagnosis_specialist,
    treatment_planner,
)


symptom_analysis_task = Task(
    description=(
        "Review the patient's reported symptoms: {symptoms}. "
        "Summarize the symptoms and identify possible explanations. "
        "Do not claim a confirmed diagnosis."
    ),
    expected_output=(
        "A structured symptom summary, possible explanations, "
        "and relevant missing information."
    ),
    agent=symptom_analyst,
)


test_interpretation_task = Task(
    description=(
        "Review the patient's test results: {test_results}. "
        "Explain what the reported findings may mean and note that "
        "interpretation depends on reference ranges and clinical context."
    ),
    expected_output=(
        "A plain-language explanation of the reported test results, "
        "their limitations, and any information needed for interpretation."
    ),
    agent=test_interpreter,
)


diagnosis_suggestion_task = Task(
    description=(
        "Using the symptom summary and test interpretation, describe "
        "possible conditions without presenting them as confirmed diagnoses. "
        "Mention uncertainty and recommend review by a qualified clinician."
    ),
    expected_output=(
        "An educational summary of possible explanations, uncertainty, "
        "and the need for professional assessment."
    ),
    agent=diagnosis_specialist,
)


treatment_planning_task = Task(
    description=(
        "Using the preceding task outputs, provide general guidance on "
        "appropriate next steps and questions to discuss with a healthcare "
        "professional. Do not prescribe medicines or invent dosages. "
        "Mention emergency care if the information suggests urgent danger."
    ),
    expected_output=(
        "General care guidance, suggested questions for a clinician, "
        "and relevant urgent-care precautions."
    ),
    agent=treatment_planner,
)
