# Setup Guide

## Prerequisites

- Python 3.10+
- SQLite (included with Python)
- Gmail account (for email notifications)
- Telegram bot (optional, for remote commands)

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-agent.git
cd ai-agent
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn sqlalchemy requests python-dotenv
```

### 3. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```
# Email (Gmail)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Telegram (optional)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789

# Tavily (optional, for web search)
TAVILY_API_KEY=tvly-xxxxx
```

### 4. Add your resume
Create `resume.txt` in the project root with your resume content. Skills will be automatically extracted.

### 5. Initialize the database
The database is created automatically on first run.

---

## Running the System

### Option 1: Start all services
```bash
python start_system.py
```
This starts both the API server (8000) and web dashboard (8001).

### Option 2: Run services individually
```bash
# Terminal 1: API Server
python interfaces/api/main.py

# Terminal 2: Web Dashboard
python interfaces/web/web_dashboard.py

# Terminal 3: Telegram Bot (optional)
python shared/tools/telegram_bot.py
```

### Option 3: Run discovery manually
```bash
# Via API
curl -X POST http://localhost:8000/run-workflow

# Or directly
python -c "
from agents.orchestrator.orchestrator_agent import OrchestratorAgent
o = OrchestratorAgent()
print(o.execute())
"
```

---

## Gmail App Password Setup

1. Go to Google Account settings
2. Security → 2-Step Verification (must be enabled)
3. App passwords → Generate new
4. Select "Mail" and your device
5. Copy the 16-character password to `.env`

---

## Telegram Bot Setup

### 1. Create a bot
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow prompts to name your bot
4. Copy the token to `.env`

### 2. Get your chat ID
1. Message your bot
2. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}` in response
4. Copy the ID to `.env`

---

## Scheduled Execution (Cron)

### Install crontab
```bash
crontab scripts/crontab.txt
```

### Default schedule
- 8:00 AM - Morning discovery run
- 6:00 PM - Evening discovery run
- 3:00 AM - Database backup

### View current cron jobs
```bash
crontab -l
```

---

## Systemd Services (Production)

### 1. Copy service files
```bash
sudo cp scripts/ai-agent-api.service /etc/systemd/system/
sudo cp scripts/ai-agent-dashboard.service /etc/systemd/system/
```

### 2. Enable and start
```bash
sudo systemctl enable ai-agent-api ai-agent-dashboard
sudo systemctl start ai-agent-api ai-agent-dashboard
```

### 3. Check status
```bash
sudo systemctl status ai-agent-api
sudo systemctl status ai-agent-dashboard
```

---

## Accessing the Dashboard

Open your browser to:
```
http://localhost:8001
```

Features:
- View all discovered internships
- Search and filter
- Mark as applied/interviewing/rejected/offer
- Analyze jobs for ATS optimization
- Add internships manually

---

## Troubleshooting

### Database locked error
```bash
# Find and kill processes using the database
fuser internships.db
```

### Port already in use
```bash
# Find process on port
lsof -i :8001
# Kill it
kill -9 <PID>
```

### Resume not loading
Ensure `resume.txt` exists in the project root directory.

### Email not sending
- Check Gmail app password is correct
- Ensure 2FA is enabled on Gmail
- Check `.env` file has no extra spaces

### Telegram not working
- Verify bot token is correct
- Ensure you've messaged the bot first
- Check chat ID matches your conversation
