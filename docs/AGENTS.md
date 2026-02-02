# Agent Documentation

## Overview

The system uses specialized agents that each handle a specific task. All agents extend `BaseTool` and implement an `execute()` method.

---

## Scout Agents

### GitHubInternshipMonitor

**Location:** `agents/scout/github_monitor.py`

**Purpose:** Scrape GitHub repos for internship listings.

**Sources (5 repos):**
- SimplifyJobs/Summer2026-Internships
- pittcsc/Summer2026-Internships
- speedyapply/2026-SWE-College-Jobs
- vanshb03/Summer2026-Internships
- summer2026internships/Summer2026-Internships

**Usage:**
```python
from agents.scout.github_monitor import GitHubInternshipMonitor

monitor = GitHubInternshipMonitor()
result = monitor.execute(repos=['SimplifyJobs'], limit=100)

# Result:
{
    "success": True,
    "data": {
        "repos_checked": 1,
        "total_internships": 150,
        "repo_data": [
            {
                "repo": "SimplifyJobs",
                "internships_found": 150,
                "sample_internships": [
                    {
                        "company": "Google",
                        "position": "Software Engineer Intern",
                        "location": "Mountain View, CA",
                        "url": "https://...",
                        "age_days": "3"
                    }
                ]
            }
        ]
    }
}
```

**Parsing Patterns:**
1. SimplifyJobs HTML table with age indicator
2. Markdown table with [Company](url) syntax
3. Simple markdown table with [Apply](url)
4. VanshB03 format with img badges
5. Summer2026 format with [Apply Here]
6. Badge-link combinations

---

### GitHubChangeDetector

**Location:** `agents/scout/github_monitor.py`

**Purpose:** Detect new internships that aren't in the database yet.

**Usage:**
```python
from agents.scout.github_monitor import GitHubChangeDetector

detector = GitHubChangeDetector()
result = detector.execute()

# Result:
{
    "success": True,
    "data": {
        "new_internships": 5,
        "new_postings": [...],
        "alert_needed": True
    }
}
```

---

### ATSMonitorTool

**Location:** `agents/scout/ats_monitor.py`

**Purpose:** Monitor company ATS (Applicant Tracking System) endpoints.

**Supported ATS:**
- Greenhouse (8 companies): Stripe, Reddit, Twitch, Robinhood, Coinbase, Square, Dropbox, Notion

**Usage:**
```python
from agents.scout.ats_monitor import ATSMonitorTool

monitor = ATSMonitorTool()
result = monitor.execute(companies=['stripe', 'coinbase'])
```

---

### InstantAlertTool

**Location:** `agents/scout/instant_alert.py`

**Purpose:** Send instant notifications when new internships are found.

**Channels:**
- Console output
- Telegram message
- Log file (`output/instant_alerts.log`)

**Usage:**
```python
from agents.scout.instant_alert import InstantAlertTool

alert = InstantAlertTool()
result = alert.execute(
    title="New Internship Alert",
    internships=[...],
    urgent=True
)
```

---

## Analyzer Agents

### ResumeMatcher

**Location:** `agents/analyzer/resume_matcher.py`

**Purpose:** Score internships based on resume match and analyze jobs for ATS optimization.

**Resume Location:** `resume.txt` in project root

**Scoring Formula (0-100):**
- 60% - Skills matching
- 25% - Job keywords (backend, frontend, ML, etc.)
- 15% - Company bonus (FAANG/top companies)

**Methods:**

#### execute() - Score all internships
```python
from agents.analyzer.resume_matcher import ResumeMatcher

matcher = ResumeMatcher()
result = matcher.execute()  # Scores all unscored internships

# Result:
{
    "success": True,
    "data": {
        "scored_count": 127,
        "skills_used": 23
    }
}
```

#### analyze_job() - ATS optimization for specific job
```python
result = matcher.analyze_job(internship_id=67)

# Result:
{
    "success": True,
    "data": {
        "internship_id": 67,
        "title": "Software Engineer Intern - Python",
        "company": "Garda Capital Partners",
        "ats_score": 50.0,
        "job_keywords": ["python", "intern"],
        "matching_keywords": ["python"],
        "missing_keywords": ["intern"],
        "recommendations": [
            {
                "priority": "medium",
                "type": "missing_keywords",
                "message": "Consider adding: intern"
            }
        ]
    }
}
```

#### get_top_matches() - Get best matching internships
```python
top_jobs = matcher.get_top_matches(limit=20)
# Returns list of top-scored internships
```

**Skills Extraction:**
Skills are extracted from `resume.txt` using regex patterns for:
- Languages: Python, Java, JavaScript, TypeScript, C++, Go, Rust, etc.
- Frameworks: React, Angular, Vue, Node, Django, Flask, FastAPI, Spring
- Cloud: AWS, Azure, GCP, Docker, Kubernetes
- Databases: SQL, PostgreSQL, MongoDB, Redis
- ML: TensorFlow, PyTorch, Pandas, NumPy

---

## Orchestrator Agent

### OrchestratorAgent

**Location:** `agents/orchestrator/orchestrator_agent.py`

**Purpose:** Coordinate the full discovery workflow.

**Workflow Steps:**
1. GitHub Discovery (all repos)
2. Database Saving (with deduplication)
3. Resume Matching (score all new internships)
4. Email Summary

**Usage:**
```python
from agents.orchestrator.orchestrator_agent import OrchestratorAgent

orchestrator = OrchestratorAgent()
result = orchestrator.execute()

# Result:
{
    "success": True,
    "data": {
        "total_discovered": 2697,
        "new_saved": 127,
        "duplicates_filtered": 89,
        "scored_count": 127,
        "email_sent": True,
        "workflow_complete": True
    }
}
```

---

## Adding a New Agent

1. Create file in appropriate directory (`agents/scout/`, `agents/analyzer/`, etc.)

2. Extend BaseTool:
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.tools.base import BaseTool

class MyNewAgent(BaseTool):
    name = "my_new_agent"
    description = "What this agent does"

    def execute(self, **kwargs):
        try:
            # Your logic here
            return {
                "success": True,
                "data": { ... }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

3. Add to orchestrator if needed:
```python
# In orchestrator_agent.py
from agents.mydir.my_new_agent import MyNewAgent

class OrchestratorAgent(BaseTool):
    def __init__(self):
        # ... existing agents ...
        self.my_agent = MyNewAgent()
```

4. Add API endpoint if needed:
```python
# In interfaces/api/main.py or interfaces/web/web_dashboard.py
@app.get("/api/my-endpoint")
def my_endpoint():
    agent = MyNewAgent()
    return agent.execute()
```
