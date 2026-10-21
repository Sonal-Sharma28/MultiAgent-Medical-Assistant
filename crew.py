
from crewai import Crew, Process

from agents import (
    symptom_analyst,
    test_interpreter,
    diagnosis_specialist,
    treatment_planner,
)

from tasks import (
    symptom_analysis_task,
    test_interpretation_task,
    diagnosis_suggestion_task,
    treatment_planning_task,
)


medical_crew = Crew(
    agents=[
        symptom_analyst,
        test_interpreter,
        diagnosis_specialist,
        treatment_planner,
    ],
    tasks=[
        symptom_analysis_task,
        test_interpretation_task,
        diagnosis_suggestion_task,
        treatment_planning_task,
    ],
    process=Process.sequential,
    verbose=True,
)
