# PATCHFORGE AI

> **From bug report to verified patch—with human approval.**

PATCHFORGE AI is an agentic software-engineering application built on Google Antigravity that leverages **Nebius Token Factory** and the **NVIDIA Nemotron** model family (`nvidia/Nemotron-3-Ultra-550b-a55b`) to inspect repositories, formulate structured plans, synthesize clean patches, run tests in isolated disposable workspaces, execute bounded repairs, and provide human-in-the-loop review.

---

## 1. Quickstart & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Nebius Token Factory API Key

### Step 1: Clone & Configure Credentials
```bash
git clone <repo_url>
cd patchforge-ai
copy .env.example .env
```
Open `.env` and fill in your Nebius credentials:
```env
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_API_KEY=your_actual_key_here
NEBIUS_MODEL=nvidia/Nemotron-3-Ultra-550b-a55b
```
> **Security Notice:** The `.env` file is excluded from Git via `.gitignore`. Never commit or paste your secret key into public chats or source files.

### Step 2: Install Backend Dependencies
```bash
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

### Step 3: Run Backend Tests
```bash
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest backend\tests
```

### Step 4: Run the Application
In terminal 1 (Backend):
```bash
$env:PYTHONPATH="backend"
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
In terminal 2 (Frontend):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 2. Core Architecture & Safety

- **Model Inference**: OpenAI-compatible client connecting to Nebius Token Factory using NVIDIA Nemotron models.
- **Credential Protection**: Automatic masking and in-memory regex redaction (`backend/app/security/redaction.py`).
- **Path Traversal & Zip-Slip Protection**: Strict boundary checks verifying files never leave the target workspace (`backend/app/services/repo_service.py`).
- **Disposable Sandbox Execution**: Tests execute on a disposable duplicate copy of the repository in `workspaces/` with allowlisted commands (`pytest`).
- **Bounded Repair Loop**: Default limit of 2 repair attempts with real captured test failure feedback.
- **Human Review**: Full diff preview, stdout/stderr inspection, and explicit Approve / Reject buttons before export.
