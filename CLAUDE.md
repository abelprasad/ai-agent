# CLAUDE.md - AI Assistant Guide for ai-agent

## Project Overview

This is a **self-hosted autonomous AI agent system** for internship discovery and management. The system uses LLM orchestration (Ollama with Llama 3.1 8B) to execute multi-step workflows including web scraping, database management, and notifications.

**Primary purpose:** Automatically discover software engineering internships from GitHub repositories, save them to a database, score them against a resume, and provide a web dashboard for tracking applications.

## Architecture

```
User Request → FastAPI API (port 8000) → Agent Loop → LLM Decision Engine (Ollama)
                                                              ↓
                                              Tool Orchestration Layer
                                              ├── Web Search (Tavily)
                                              ├── Browser (Playwright)
                                              ├── Database (SQLite)
                                              ├── Email (Gmail SMTP)
                                              ├── Telegram Notifications
                                              └── GitHub Monitors

Web Dashboard (port 8001) ←→ SQLite Database (internships.db)
```

## Directory Structure

```
ai-agent/
├── agent.py                    # Core agent loop - LLM orchestration
├── start_system.py             # Launcher for both servers
├── resume.txt                  # User resume for matching
├── interfaces/
│   ├── api/main.py            # FastAPI server (port 8000) - job submission
│   └── web/web_dashboard.py   # Web dashboard (port 8001) - CRUD interface
├── agents/
│   ├── orchestrator/
│   │   └── orchestrator_agent.py  # Workflow orchestration
│   ├── scout/
│   │   ├── github_monitor.py      # GitHub repo monitoring
│   │   ├── ats_monitor.py         # ATS system monitoring
│   │   └── instant_alert.py       # Real-time notifications
│   ├── analyzer/
│   │   └── resume_matcher.py      # Resume-based scoring
│   ├── quality/                   # (Planned) Quality review
│   └── applicant/                 # (Planned) Auto-application
├── shared/
│   ├── database/
│   │   └── database.py           # SQLAlchemy models and utilities
│   └── tools/
│       ├── base.py               # BaseTool interface
│       ├── websearch.py          # Tavily API integration
│       ├── browser.py            # Playwright automation
│       ├── database.py           # Database save/query tools
│       ├── email_tool.py         # Gmail SMTP
│       ├── telegram.py           # Telegram bot
│       └── filesystem.py         # File operations
├── scripts/
│   ├── run-workflow.sh          # Cron trigger script
│   ├── crontab.txt              # Scheduled job config
│   └── *.service                # Systemd service files
└── backups/                     # Database backups
```

## Key Components

### 1. Agent Core (`agent.py`)
The main agent loop that:
- Takes a natural language goal
- Iteratively calls the LLM for next action
- Executes tools based on LLM decisions
- Returns JSON responses: `{"tool": "name", "args": {...}}` or `{"done": true, "summary": "..."}`
- Max 15 iterations per goal

### 2. Tools (BaseTool Interface)
All tools implement the `BaseTool` interface from `shared/tools/base.py`:
```python
class BaseTool:
    name = ""           # Tool identifier
    description = ""    # Shown to LLM

    def execute(self, **kwargs):
        # Must return: {"success": True/False, "data": ...} or {"error": "..."}
```

**Available Tools:**
| Tool | Name | Purpose |
|------|------|---------|
| WebSearchTool | `web_search` | Tavily API search |
| BrowserTool | `browse_website` | Playwright page extraction |
| DatabaseTool | `save_to_database` | Save internships |
| DatabaseQueryTool | `query_database` | Query internships |
| EmailTool | `send_email` | Gmail notifications |
| TelegramTool | `send_telegram` | Instant alerts |
| GitHubInternshipMonitor | `monitor_github_internships` | GitHub repo scraping |
| ResumeMatcher | `match_resume` | Score internships |
| OrchestratorAgent | `orchestrate_workflow` | Full workflow execution |

### 3. Database Schema (`shared/database/database.py`)
**InternshipListing** table:
- `id`, `agent_job_id`, `title`, `company`, `url` (unique), `location`
- `description`, `requirements`, `deadline`
- `salary_min`, `salary_max`
- `discovered_at`, `applied`, `application_date`, `application_status`
- `relevance_score`, `interest_level`, `age_days`

**AgentJob** table:
- `job_id`, `goal`, `status`, `result_summary`, `created_at`, `completed_at`

### 4. API Endpoints (`interfaces/api/main.py`)
- `POST /jobs` - Submit new agent job
- `GET /jobs/{job_id}` - Check job status
- `POST /run-workflow` - Direct workflow execution (bypasses LLM)
- `GET /` - System info

### 5. Dashboard API (`interfaces/web/web_dashboard.py`)
- `GET /api/stats` - Database statistics
- `GET /api/internships` - List with filtering/sorting
- `POST /api/internships` - Create
- `PUT /api/internships/{id}` - Update
- `DELETE /api/internships/{id}` - Delete
- `POST /api/internships/{id}/apply` - Mark as applied

## Development Workflows

### Running the System
```bash
# Start both servers
python start_system.py

# Or individually
python interfaces/api/main.py      # API on port 8000
python interfaces/web/web_dashboard.py  # Dashboard on port 8001
```

### Running a Workflow
```bash
# Via API
curl -X POST http://localhost:8000/run-workflow

# Or submit a custom goal
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"goal": "Find 10 software engineering internships"}'
```

### Testing Tools Individually
```bash
# Test resume matcher
python agents/analyzer/resume_matcher.py

# View database contents
python shared/database/view_database.py
```

## Configuration

### Environment Variables (`.env`)
```bash
TAVILY_API_KEY=tvly-...          # Web search API
EMAIL_SENDER=your@gmail.com       # Gmail address
EMAIL_PASSWORD=xxxx-xxxx-xxxx     # Gmail app password
EMAIL_RECIPIENT=your@gmail.com    # Notification recipient
TELEGRAM_BOT_TOKEN=123456:ABC...  # Telegram bot token
TELEGRAM_CHAT_ID=123456789        # Your Telegram chat ID
```

### GitHub Repos Monitored
- `SimplifyJobs/Summer2026-Internships`
- `pittcsc/Summer2026-Internships`
- `speedyapply/2026-SWE-College-Jobs`

## Conventions

### Code Style
- Python 3.10+ with type hints where appropriate
- SQLAlchemy for database operations
- FastAPI for HTTP endpoints
- Tool results always return `{"success": bool, "data": ...}` or `{"success": False, "error": "..."}`

### Adding New Tools
1. Create tool class in `shared/tools/` extending `BaseTool`
2. Define `name`, `description` (for LLM), and `execute(**kwargs)` method
3. Register in `interfaces/api/main.py` tools list

### Database Operations
- Always use `get_db_session()` for sessions
- Close sessions after use
- URL-based deduplication for internships
- Use SQLAlchemy ORM, not raw SQL

### Error Handling
- Tools should catch exceptions and return `{"success": False, "error": "message"}`
- Agent loop handles invalid JSON and unknown tools gracefully
- Max 15 iterations prevents infinite loops

## Common Tasks

### Add a new internship source
1. Create monitor tool in `agents/scout/`
2. Add URL parsing logic for the source's format
3. Register in API tools list
4. Add to orchestrator workflow if needed

### Modify scoring algorithm
Edit `agents/analyzer/resume_matcher.py`:
- `_extract_skills()` - Parse resume
- `_calculate_score()` - Scoring logic (0-100)
- Adjust weights: skills (60%), keywords (25%), company bonus (15%)

### Update dashboard UI
The dashboard uses inline HTML/CSS/JS in `interfaces/web/web_dashboard.py`:
- Dark theme with Tailwind-style classes
- Vanilla JavaScript for API calls
- Auto-refresh every 60 seconds

## Testing

No formal test suite. Manual testing approach:
```bash
# Test browser tool
python test_browser.py

# Test email tool
python test_email.py

# Test full workflow
curl -X POST http://localhost:8000/run-workflow
```

## Deployment

### Systemd Services (in `scripts/`)
- `ai-agent-api.service` - API server
- `ai-agent-dashboard.service` - Web dashboard
- `telegram-bot.service` - Telegram bot

### Cron Jobs (`scripts/crontab.txt`)
- Discovery workflow: 8 AM and 6 PM daily
- Database backup: 3 AM daily

## Important Notes

1. **Database location**: `internships.db` in project root (excluded from git)
2. **LLM requirement**: Ollama with `llama3.1:8b` model must be running
3. **Browser automation**: Runs headless; requires Playwright browsers installed
4. **Rate limiting**: GitHub API has rate limits; be mindful with frequent calls
5. **Email**: Requires Gmail app password (not regular password)
6. **Backup database before major changes**: `cp internships.db internships_backup.db`
