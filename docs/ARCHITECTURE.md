# System Architecture

## Overview

The AI Internship Agent is a multi-agent system that autonomously discovers, tracks, and helps you apply to internships. It uses a modular architecture with specialized agents for different tasks.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Web Dashboard  │  │   Telegram Bot  │  │    REST API     │  │
│  │   (port 8001)   │  │   (commands)    │  │   (port 8000)   │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼─────────────────────┼─────────────────────┼──────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator Agent                          │
│         Coordinates workflow: Discovery → Save → Score           │
└─────────────────────────────────────────────────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│   Scout Agents  │  │ Analyzer Agents │  │   Shared Tools      │
│  - GitHub       │  │  - Resume       │  │  - Database         │
│  - ATS          │  │    Matcher      │  │  - Email            │
│  - Alerts       │  │  - ATS Optimizer│  │  - Telegram         │
└────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘
         │                    │                      │
         ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite Database                              │
│              internship_listings, agent_jobs                     │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
ai-agent/
├── agents/                    # Specialized agents
│   ├── orchestrator/          # Workflow coordination
│   │   └── orchestrator_agent.py
│   ├── scout/                 # Discovery agents
│   │   ├── github_monitor.py  # GitHub repo scraping
│   │   ├── ats_monitor.py     # ATS endpoint monitoring
│   │   └── instant_alert.py   # Notification dispatch
│   ├── analyzer/              # Analysis agents
│   │   └── resume_matcher.py  # Resume matching + ATS optimization
│   ├── applicant/             # (Future) Auto-application
│   └── quality/               # (Future) Quality checks
│
├── interfaces/                # User-facing interfaces
│   ├── api/
│   │   └── main.py            # FastAPI server (port 8000)
│   └── web/
│       └── web_dashboard.py   # Web UI (port 8001)
│
├── shared/                    # Shared utilities
│   ├── database/
│   │   └── database.py        # SQLAlchemy models
│   └── tools/
│       ├── base.py            # BaseTool class
│       ├── database.py        # Database operations
│       ├── email_tool.py      # Email sending
│       ├── telegram.py        # Telegram messages
│       └── telegram_bot.py    # Telegram bot listener
│
├── scripts/                   # Deployment scripts
│   ├── run-workflow.sh        # Cron trigger script
│   └── crontab.txt            # Cron schedule
│
├── docs/                      # Documentation
├── tests/                     # Test suite
├── resume.txt                 # Your resume for matching
├── internships.db             # SQLite database
└── .env                       # Environment variables
```

## Data Flow

### 1. Discovery Flow
```
Cron/Manual Trigger
       │
       ▼
┌──────────────────┐
│   Orchestrator   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│  GitHub Monitor  │────▶│   5 GitHub Repos │
│  (6 patterns)    │     │   (README.md)    │
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│  Database Tool   │────▶ Deduplicate & Save
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Resume Matcher  │────▶ Score 0-100%
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Email Tool     │────▶ Summary notification
└──────────────────┘
```

### 2. Analysis Flow (ATS Optimizer)
```
User clicks "Analyze"
         │
         ▼
┌──────────────────┐
│  Web Dashboard   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ /api/.../analyze │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│  Resume Matcher  │────▶│   analyze_job()  │
│                  │     │                  │
│  - Load resume   │     │  - Extract job   │
│  - Extract skills│     │    keywords      │
│                  │     │  - Compare       │
│                  │     │  - Recommend     │
└──────────────────┘     └──────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  Response:                       │
│  - ATS Score (0-100%)            │
│  - Matching keywords             │
│  - Missing keywords              │
│  - Recommendations               │
└──────────────────────────────────┘
```

## Agent Design Pattern

All agents follow the `BaseTool` pattern:

```python
from shared.tools.base import BaseTool

class MyAgent(BaseTool):
    name = "my_agent"
    description = "What this agent does"

    def execute(self, **kwargs):
        try:
            # Do work
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

## Database Schema

### internship_listings
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String | Job title |
| company | String | Company name |
| url | String | Application URL (unique) |
| location | String | Job location |
| description | Text | Job description |
| requirements | Text | Job requirements |
| discovered_at | DateTime | When found |
| relevance_score | Float | Resume match (0-100) |
| application_status | String | not_applied/applied/interviewing/rejected/offer |
| age_days | Integer | Days since posted |

### agent_jobs
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| job_id | String | UUID |
| goal | Text | Job goal/prompt |
| status | String | queued/running/completed/failed |
| created_at | DateTime | When created |
| completed_at | DateTime | When finished |

## Scheduled Execution

Cron runs discovery at 8 AM and 6 PM daily:

```
0 8 * * * /home/user/ai-agent/scripts/run-workflow.sh
0 18 * * * /home/user/ai-agent/scripts/run-workflow.sh
```

## Environment Variables

Required in `.env`:
```
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
TAVILY_API_KEY=tvly-xxxxx  # Optional, for web search
```
