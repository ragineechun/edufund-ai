# EduFund AI

A web platform that helps students find ways to fund their education. A student fills in their academic and financial profile and gets a funding assessment, matched scholarships and work-study openings, and can start a crowdfunding campaign. Admins manage the scholarships and opportunities.

Built with a Flask REST API, SQLite and a plain HTML/CSS/JavaScript frontend.

## Features

- **Accounts and roles** – student and admin logins with JWT tokens; passwords hashed with bcrypt.
- **Funding assessment** – estimates a student's funding gap, repayment capacity, eligibility score and risk level from income, marks, fees and course length.
- **Scholarship matching** – scores each scholarship against the student's profile (marks, income limit, course, merit or need based) and checks eligibility.
- **Work-study opportunities** – listings matched on skills, location and hours, with applications.
- **Crowdfunding** – students create campaigns with a story, goal and image; anyone logged in can donate.
- **Donation ledger** – every donation is added as a block to a simple hash-chained ledger with proof-of-work, viewable at `/api/blockchain/records`.
- **Admin panel** – dashboard statistics, scholarship and work-study management, student list.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, Flask, Flask-JWT-Extended, Flask-CORS |
| Data and ML | SQLite, pandas, NumPy, scikit-learn |
| Frontend | HTML, CSS, JavaScript (fetch API) |

## Run it locally

You need Python 3.10 or newer.

```bash
git clone https://github.com/ragineechun/edufund-ai.git
cd edufund-ai/backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
copy .env.example .env       # Windows   (macOS / Linux: cp .env.example .env)
python init_admin.py         # creates the admin account
python seed_scholarships.py  # loads sample scholarships
python app.py
```

Open http://localhost:5000.

| Page | URL | Login |
|---|---|---|
| Landing page | `/` | register a new student account |
| Student dashboard | `/student` | your student account |
| Admin panel | `/admin` | `admin@edufund.ai` / `admin123` (demo only, change it) |

## Project structure

```
backend/
  app.py                 Flask app, page routes, ledger endpoint
  config.py              settings read from .env
  init_admin.py          creates the admin account
  seed_scholarships.py   loads sample scholarships
  models/
    database.py          SQLite tables and queries
    ai_model.py          funding assessment
    matching_engine.py   scholarship and work-study matching
    blockchain.py        hash-chained donation ledger
  routes/                auth, student, admin, crowdfunding, work-study APIs
  data/                  small sample dataset
frontend/                landing page, student dashboard, admin panel
crawler/                 script that collects scholarship listings from the web
```

## How the assessment works

The funding assessment uses a rule-based formula: the funding gap is the tuition fee minus what the family can reasonably contribute, and repayment capacity and risk come from income and marks. The code also trains Random Forest models on the sample dataset at startup, but that dataset has only 14 rows, far too few for reliable predictions, so the app relies on the rule-based result.

## Experimental modules

These are in the repository but not connected to the running app yet. They need the extra packages in `backend/requirements-optional.txt`.

- `routes/ai_features.py` with `models/enhanced_matching_engine.py`, `models/semantic_search.py` and `models/resume_analyzer.py` – success prediction, text search over scholarships and resume analysis.
- `add_s.py` – a command-line resume scanner that uses the Gemini API (set `GEMINI_API_KEY` first).
- `crawler/find_scholarships.py` – scholarship crawler.

## Limitations

- The ledger is kept in memory, so it resets when the server restarts. It demonstrates the idea and is not a real blockchain network.
- Donations are simulated; there is no payment gateway.
- Password reset and email verification endpoints are placeholders.
