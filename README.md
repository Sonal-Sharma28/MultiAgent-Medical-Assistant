# Multi-Agent-Med-System
 
# Medical Diagnosis AI Assistant

An intelligent medical diagnosis system that leverages AI agents powered by Google's Gemini to assist in medical diagnosis processes. The system combines multiple specialized AI agents working together through CrewAI, with a modern web interface built using FastAPI.

## 🌟 Features

- **Multi-Agent Diagnosis System**
  - Symptom Analysis Agent
  - Test Interpretation Agent
  - Diagnosis Specialist Agent
  - Treatment Planning Agent

- **Modern Web Interface**
  - Responsive design
  - Real-time interaction
  - User-friendly interface

- **Powered by Advanced AI**
  - Google Gemini AI integration
  - CrewAI framework for agent collaboration
  - Efficient task delegation and processing

    ![image](https://github.com/user-attachments/assets/1557a841-b118-4de8-82eb-923d7c541b3c)


## 🔧 Technical Stack

- **Backend**
  - FastAPI
  - Python 3.9+
  - CrewAI
  - Google Generative AI (Gemini)

- **Frontend**
  - HTML5
  - CSS3
  - JavaScript

## 📋 Prerequisites

- Python 3.9 or higher
- Google Gemini API key
- Basic understanding of medical terminology (for use)

## ⚙️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medical-diagnosis-ai.git
cd medical-diagnosis-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🚀 Usage

1. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Enter patient symptoms and follow the interface prompts for diagnosis.

## 📁 Project Structure

```
medical-diagnosis-ai/
├── app/
│   ├── main.py           # FastAPI application
│   ├── agents.py         # AI agents configuration
│   └── utils.py          # Utility functions
├── static/
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/
│   └── index.html       # Main web interface
├── requirements.txt
└── README.md
```

## 🔄 API Endpoints

- `GET /`: Main web interface
- `POST /analyze`: Submit symptoms for analysis
- `GET /status`: Check system status
- `POST /diagnosis`: Get final diagnosis
- `POST /treatment`: Get treatment plan

## ⚠️ Rate Limits

Using Gemini's free tier with the following limits:
- 15 requests per minute (RPM)
- 1 million tokens per minute (TPM)
- 1,500 requests per day (RPD)

## 🛡️ Disclaimer

This system is designed to assist medical professionals and should not be used as a replacement for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers.

## 🔒 Security

- API key protection
- Rate limiting implementation
- Input validation and sanitization
- Secure HTTPS communication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Generative AI team for Gemini
- CrewAI framework developers
- FastAPI development team




