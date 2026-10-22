
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
        "Produce a concise, neutral summary of only the reported symptoms, "
        "including timing or severity only when supplied. Note important "
        "missing context without guessing. Flag a possible immediate safety "
        "concern only when supported by the reported symptoms. Do not diagnose "
        "or repeat generic advice that belongs in the final guidance."
    ),
    expected_output=(
        "A brief symptom summary, relevant missing context, and any "
        "input-supported urgent concern. Do not add unsupported facts."
    ),
    agent=symptom_analyst,
)


test_interpretation_task = Task(
    description=(
        "Review the patient's test results: {test_results}. "
        "Explain the reported results in plain language, using reference "
        "ranges and units only when provided. Distinguish supplied facts from "
        "possible interpretations. Do not infer a diagnosis, invent missing "
        "values or ranges, or restate the symptom summary. If no test results "
        "were supplied, say so briefly."
    ),
    expected_output=(
        "A concise explanation of supplied results and their limitations, "
        "or a brief note that no results were provided."
    ),
    agent=test_interpreter,
)


diagnosis_suggestion_task = Task(
    description=(
        "Using the symptom summary and test interpretation, mention only "
        "relevant possible explanations that are supported by the information. "
        "Clearly label them as possibilities, explain key uncertainty briefly, "
        "and do not introduce unsupported findings, repeat prior summaries, "
        "or provide treatment advice."
    ),
    expected_output=(
        "A short, non-diagnostic note on relevant possibilities and "
        "uncertainty, or a statement that the information is insufficient "
        "to suggest one."
    ),
    agent=diagnosis_specialist,
)


treatment_planning_task = Task(
    description=(
        "Write the final user-facing response by synthesizing the preceding "
        "task outputs. Do not repeat their explanations or add findings not "
        "supported by the user's information. Use plain, accessible language, "
        "short paragraphs, and bullets where useful. Aim for about 150–250 "
        "words for a typical response, but use more when needed to preserve "
        "important safety information; this is a guide, not a hard limit. "
        "Use these Markdown sections where relevant: "
        "'## Summary', '## What the information may indicate', "
        "'## Recommended next steps', "
        "'## When to seek urgent medical care' (include only when relevant, "
        "and never omit an input-supported urgent warning to meet the length "
        "target), and '## Questions to ask your doctor'. End with "
        "'## Medical disclaimer' explaining that this is general educational "
        "information, not a diagnosis or a substitute for a qualified "
        "healthcare professional. Preserve uncertainty, do not claim possible "
        "conditions are confirmed, and do not prescribe medication or invent "
        "doses. Keep each point in one appropriate section."
    ),
    expected_output=(
        "A concise, structured final response with relevant next steps, "
        "questions for a clinician, input-supported urgent-care guidance, "
        "and a medical disclaimer. Typical responses should be about "
        "150–250 words, with room for longer safety-critical guidance."
    ),
    agent=treatment_planner,
)
