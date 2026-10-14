# 🚀 AI Personalized Learning & Skill-Gap Platform

A modern full-stack web application designed to help students bridge the gap between their current skill levels and industry career requirements. The platform evaluates competencies, calculates real-time skill gaps, generates a custom learning roadmap with free curated resources, and tracks study progress.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Architecture](#-project-architecture)
- [Prerequisites](#-prerequisites)
- [Step-by-Step Setup & Run Instructions](#-step-by-step-setup--run-instructions)
  - [1. Backend Setup (FastAPI)](#1-backend-setup-fastapi)
  - [2. Frontend Setup (React + Vite)](#2-frontend-setup-react--vite)
- [Demo Credentials](#-demo-credentials)
- [Core Logic Explained](#-core-logic-explained)
- [Testing](#-testing)
- [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Overview

Students entering technical fields often face three major challenges:
1. They don't know the exact benchmark skills required for specific tech roles.
2. They don't know their current skill deficit or the right order to learn prerequisite skills.
3. High-quality learning resources are scattered and hard to match to their current level.

This platform solves this by offering:
- **Career Benchmarking**: Select from target roles (Full Stack Developer, Data Analyst, AI/ML Engineer).
- **Rule-Based Skill Assessment**: Rate skills on a 1–5 scale to immediately calculate deficits and a verified readiness score.
- **Dynamic Learning Roadmaps**: Generate step-by-step schedules with weekly time estimates, prerequisites, and free resources.
- **Milestone & Progress Tracking**: Update activity statuses (`Not Started`, `In Progress`, `Completed`) with interactive visual charts.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔐 **Authentication & Demo Mode** | Secure JWT authentication with bcrypt password hashing, plus a 1-click **"Try demo account"** button. |
| 🎯 **Career Selection** | Explore career paths with required skill matrices and industry benchmarks. |
| 📝 **Skill Assessment** | Interactive self-rating tool (Level 1 Beginner to Level 5 Expert) with instant feedback. |
| 📊 **Skill-Gap Analysis** | Clear breakdown of achieved skills, deficits, and priority levels. |
| 🗺️ **Personalized Roadmap** | Configurable study pace (hours/day and days/week) with structured sequence and curated free learning resources. |
| 📈 **Interactive Dashboard** | Compact 4-metric statistics row, skill readiness breakdown, progress donut chart, and recommended next activities. |
| 🔄 **Skill Reassessment** | Re-rate competencies after completing learning modules to confirm achievements and boost readiness scores. |

---

## 🛠 Tech Stack

### Frontend
- **Framework**: [React](https://react.dev/) (v18/19) with [Vite](https://vitejs.dev/)
- **Routing**: [React Router](https://reactrouter.com/) (v6)
- **Charts**: [Recharts](https://recharts.org/)
- **HTTP Client**: [Axios](https://axios-http.com/) with JWT interceptors
- **Styling**: Vanilla CSS with modern tokens, responsive grids, and dark navy/blue theme

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **Server**: [Uvicorn](https://www.uvicorn.org/) (ASGI)
- **Database**: SQLite with [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- **Validation**: [Pydantic](https://docs.pydantic.dev/) schemas
- **Security**: PyJWT (Bearer token) and Passlib (bcrypt hashing)
- **Testing**: [pytest](https://docs.pytest.org/) with FastAPI TestClient

---

## 📂 Project Architecture

```text
ai-learning-platform/
├── backend/
│   ├── main.py                  # FastAPI application entry point & CORS configuration
│   ├── auth.py                  # JWT creation, token decoding, and password hashing
│   ├── auth_deps.py             # Authentication dependencies for protected routes
│   ├── database.py              # SQLite connection and session management
│   ├── models.py                # Database models (Student, Career, Skill, etc.)
│   ├── roadmap_models.py        # Roadmap and learning activity database models
│   ├── schemas.py               # Pydantic request and response schemas
│   ├── crud.py                  # Database queries and persistence functions
│   ├── seed.py                  # Auto-seeds default careers and skill datasets
│   ├── requirements.txt         # Python package dependencies
│   ├── routers/
│   │   ├── progress.py          # Dashboard and progress tracking endpoints
│   │   └── roadmap.py           # Roadmap generation and activity update endpoints
│   ├── services/
│   │   ├── skill_analyzer.py    # Rule-based skill gap and readiness algorithms
│   │   ├── roadmap_generator.py # Topological sort and schedule generator
│   │   └── roadmap_service.py   # Roadmap serialization and lifecycle management
│   └── tests/                   # Pytest automated test suites
│
└── frontend/
    ├── package.json             # Node dependencies and scripts
    ├── vite.config.js           # Vite build configuration
    ├── index.html               # Main HTML entry file
    └── src/
        ├── App.jsx              # Main router and route protection
        ├── api/                 # Axios HTTP client and API integration modules
        ├── context/             # AppContext for student login and state management
        ├── components/          # Reusable UI components (Navbar, Charts, ProgressBar, etc.)
        ├── pages/               # Dashboard, Roadmap, ProgressTracker, Assessment, Login, etc.
        └── styles/
            └── global.css       # Unified design system, tokens, and responsive utilities
```

---

## 📋 Prerequisites

Make sure the following tools are installed on your system:
- **Node.js**: `v18.0.0` or newer ([Download Node.js](https://nodejs.org/))
- **Python**: `3.10` or newer ([Download Python](https://www.python.org/))
- **Package Managers**: `npm` (comes with Node.js) and `pip` (comes with Python)

---

## 🏃 Step-by-Step Setup & Run Instructions

To run the application locally, you will run the **backend** and **frontend** in two separate terminal windows.

### 1. Backend Setup (FastAPI)

Open your first terminal window:

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create a Python virtual environment (named 'venv')
# Windows (PowerShell or Command Prompt):
python -m venv venv

# macOS / Linux:
python3 -m venv venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# (If PowerShell blocks script execution, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# Windows (Command Prompt):
venv\Scripts\activate.bat

# macOS / Linux:
source venv/bin/activate

# 4. Upgrade pip and install backend dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Start the backend server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

> [!NOTE]
> On the first startup, FastAPI will automatically initialize the SQLite database file (`backend/learning.db`) and seed all careers, skills, and prerequisite links.

- **Backend API URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

### 2. Frontend Setup (React + Vite)

Open a second terminal window:

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install frontend dependencies
npm install

# 3. Launch the Vite development server
npm run dev
```

- **Frontend Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Demo Credentials

You can explore the platform immediately without filling out a registration form:
1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. On the Login page, click the **"Try demo account"** button.
3. This creates an authenticated session for demo student **Pravin** with a pre-configured career track and sample progress.

Alternatively, you can register a new account on the **Register** page using any valid email address and password.

---

## 🧠 Core Logic Explained

### 1. Skill Gap Calculation
Proficiency levels are evaluated on a transparent 1 to 5 scale:
- `1` = Beginner
- `2` = Basic
- `3` = Intermediate
- `4` = Advanced
- `5` = Expert

$$\text{Skill Gap} = \max(0, \text{Target Level} - \text{Current Level})$$

- **Gap = 0**: Skill Achieved
- **Gap = 1**: Needs Minor Improvement
- **Gap > 1**: Significant Skill Gap

### 2. Readiness Score (%)
The readiness score reflects the proportion of required skills mastered:

$$\text{Readiness (\%)} = \left(\frac{\sum \min(\text{Current Level}, \text{Target Level})}{\sum \text{Target Level}}\right) \times 100$$

### 3. Roadmap Sequencing (Topological Ordering)
The roadmap generator ensures that prerequisite skills appear before advanced concepts (e.g. *HTML & CSS* and *JavaScript* come before *React*). Estimated learning hours are based on the student's available daily hours and study days per week.

---

## 🧪 Testing

### Backend Unit & Integration Tests
Ensure your virtual environment is active in the `backend/` directory, then run:

```bash
# Run the core roadmap and progress test suite
pytest tests/test_progress.py tests/test_roadmap.py -v
```

### Frontend Production Build Test
In the `frontend/` directory, verify that there are no syntax or bundler errors:

```bash
npm run build
```

---

## ❓ Troubleshooting & FAQ

### 1. PowerShell Script Execution Error
If you receive an error like `File ...\Activate.ps1 cannot be loaded because running scripts is disabled on this system`, run this in PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then re-run `.\venv\Scripts\Activate.ps1`.

### 2. Port Already in Use
- If port `8000` is busy: Specify an alternate port with `uvicorn main:app --reload --port 8001` and update the `baseURL` in `frontend/src/api/http.js`.
- If port `5173` is busy: Vite will automatically suggest port `5174`.

### 3. Resetting the Database
To reset all student data and re-seed clean career/skill matrices, stop the backend server and delete `backend/learning.db`:
```bash
# In backend directory
rm learning.db
# Restart uvicorn to automatically re-create and re-seed
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 📄 License
This project is open-source and intended for educational and skill development purposes.