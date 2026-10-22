# MediAssist AI

MediAssist AI is an educational health-information web app. It combines a sequential CrewAI workflow with a browser interface to help users organize reported symptoms and test results for discussion with a qualified healthcare professional.

> This app does not diagnose or replace professional medical care.
<img width="941" height="494" alt="image" src="https://github.com/user-attachments/assets/f86020f3-4054-4d52-aca6-cddca371c373" />
<img width="908" height="432" alt="image" src="https://github.com/user-attachments/assets/80ba31da-4e89-436e-b484-c31b94eecc43" />
<img width="916" height="488" alt="image" src="https://github.com/user-attachments/assets/112ad0d3-0e4f-477f-9ba3-32ccacb0f01c" />
<img width="787" height="266" alt="image" src="https://github.com/user-attachments/assets/7b770b48-3b7f-4308-84f5-c59d7fb07806" />


## Features

- **Multi-agent analysis:** CrewAI agents review symptoms, interpret provided test results, consider possible explanations, and offer general care guidance.
- **Live workflow progress:** Displays agent and task lifecycle events while an analysis runs.
- **Voice symptom entry:** Uses browser speech recognition when available. English, Hindi, or Marathi recognition is selected from browser language preferences; speech language is not automatically detected.
- **Response translation:** Translates a completed English response into Hindi or Marathi using the configured Gemini model.
- **Medical report comparison:** Compares dates, values, and units for matching tests and calculates absolute and percentage changes in the browser.
- **Convenience and accessibility:** Recent analyses are saved in browser local storage; responses can be copied or downloaded. The interface also includes Markdown formatting and light/dark themes.

## Technology

- Python 3.11
- FastAPI and Uvicorn
- CrewAI with its LiteLLM extra
- Google Gemini via CrewAI's LLM interface
- Jinja2 templates, HTML, CSS, and vanilla JavaScript

## Getting started (Windows PowerShell)

### Prerequisites

- Python 3.11 and `pip`
- A Google API key accepted by the configured Gemini provider

### 1. Clone the repository and create a virtual environment

```powershell
git clone https://github.com/Sonal-Sharma28/MultiAgent-Medical-Assistant.git
cd MultiAgent-Medical-Assistant
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents virtual-environment activation, allow scripts for this session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Configure the API key

The application reads `GOOGLE_API_KEY` from the environment. Create a `.env` file in the project root and add your own key:

```dotenv
GOOGLE_API_KEY=replace_with_your_google_api_key
```

Do not commit or share your `.env` file.

### 3. Run the application

```powershell
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000/> in your browser. The interactive API documentation is available at <http://127.0.0.1:8000/docs>.

### Run tests

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
.
├── agents.py             # CrewAI agent roles and Gemini model configuration
├── crew.py               # Sequential CrewAI workflow
├── main.py               # FastAPI application and API endpoints
├── tasks.py              # CrewAI task definitions
├── workflow_progress.py  # Request-scoped workflow event capture
├── templates/
│   └── index.html        # Application UI, styles, and browser-side behavior
├── static/               # Legacy static assets
├── tests/                # Automated tests
└── requirements.txt      # Python dependencies
```

## Limitations and medical disclaimer

MediAssist AI provides general educational information, not a medical diagnosis or a substitute for advice, diagnosis, or treatment from a qualified healthcare professional. Contact local emergency services if you may be experiencing an emergency.

AI-generated analysis and machine translations can be incomplete or inaccurate; review them with a qualified professional. Speech recognition depends on browser support, permissions, and available recognition services. The app selects one recognition locale from browser preferences and does not identify the spoken language automatically.
