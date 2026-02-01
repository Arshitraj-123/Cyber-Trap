# CyberTrap – Agentic Scam Intelligence Honey-Pot

🕷️ An AI-powered honey-pot system that engages scammers using a sophisticated persona (Mrs. Shanthi) to extract intelligence like UPI IDs, bank accounts, and phishing links.

## 🏆 Hackathon Submission

**Live API Endpoint**: `https://your-api-url.onrender.com`  
**API Key**: Provided in submission form

## Features

- **4-Stage Extraction Funnel**: Hook → Technical Friction → Pivot → Extraction
- **Consensus Confidence System**: 100% confidence when values confirmed across multiple turns
- **Multi-Language Support**: English, Hindi, Tamil, Telugu, Malayalam (with code-mixing)
- **Stealth Function Calling**: Intelligence extraction invisible to scammer
- **Soft-Fail Validation**: Auto-cleans dirty data with natural clarification prompts
- **Stage Buffer Logic**: Prevents eager extraction, builds rapport first
- **Real-time Dashboard**: Dark theme cyber UI with live JSON updates

## Environment Variables

> ⚠️ **Important**: Create a `.env` file from `.env.example` before running

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq Cloud API key for Llama 3.3 70B | ✅ Yes |
| `API_SECRET_KEY` | API authentication header key | ✅ Yes |

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:5173 in your browser.

## API Schema (Hackathon Compliant)

### POST /api/engage

**Headers:**
```
X-API-Key: your_api_secret_key
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Congratulations! You won 50 lakhs lottery!",
  "conversation_history": [],
  "session_id": "test-session"
}
```

**Response Schema:**
```json
{
  "classification": "SCAM",
  "confidence": 0.75,
  "reply": "Aiyyo! This is wonderful news, beta! I am so happy!...",
  "intelligence": {
    "upi": "scammer@okaxis",
    "bank_account": null,
    "ifsc": null,
    "link": "http://fake-prize.com"
  },
  "explanation": "Stage 1: Building rapport | Groq LLM response | Confidence: 75%",
  "current_stage": 1,
  "detected_language": "english",
  "thought_process": [...],
  "needs_clarification": null,
  "extraction_allowed": true
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `classification` | string | Always "SCAM" (honey-pot system) |
| `confidence` | float | 0.0-1.0 score (1.0 = consensus achieved) |
| `reply` | string | Mrs. Shanthi's response to scammer |
| `intelligence` | object | Extracted UPI, bank, IFSC, links |
| `explanation` | string | Agent's reasoning for current action |

## Confidence Scoring System

| Level | Score | Condition |
|-------|-------|-----------|
| Base | 50% | First extraction detected |
| Regex Match | 65% | Pattern validated |
| Extended Turn | 75% | Turn count > 4 |
| **Consensus** | **100%** | Same value extracted twice 🔒 |

## Project Structure

```
├── backend/
│   ├── main.py           # FastAPI server with Groq integration
│   ├── persona.py        # Mrs. Shanthi staged persona
│   ├── validators.py     # Pydantic validators with consensus
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment template
└── frontend/
    ├── src/
    │   ├── App.tsx           # Main dashboard
    │   └── components/
    │       ├── ChatPanel.tsx
    │       ├── IntelligencePanel.tsx
    │       └── ThoughtProcess.tsx
    ├── index.html
    └── package.json
```

## Deployment

### Backend (Render.com)

1. Push code to GitHub
2. Create new Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render Dashboard:
   - `GROQ_API_KEY`: Your Groq API key
   - `API_SECRET_KEY`: Your API authentication key

### Frontend (Vercel)

1. Push code to GitHub
2. Import project on Vercel
3. Set root directory to `frontend`
4. Update `API_URL` in `App.tsx` to your Render backend URL

## Mrs. Shanthi Persona

> *"Aiyyo beta, my NetProtect software is showing danger sign! Can you give me your UPI ID? My neighbor Lakshmi's son can do the transfer..."*

- 68-year-old retired Tamil teacher from Chennai
- Polite, uses "beta" to address scammer
- "Struggling" with technology
- Eager to receive prize/refund
- Asks for UPI/bank details as "alternative"

## Tech Stack

- **Backend**: FastAPI, Groq (Llama 3.3 70B), Pydantic, Tenacity
- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **AI Features**: Function calling, language detection, staged prompting, consensus scoring

## License

MIT
