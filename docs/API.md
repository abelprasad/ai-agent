# API Documentation

## Overview

The system exposes two HTTP servers:
- **API Server** (port 8000) - Job management and workflow execution
- **Web Dashboard** (port 8001) - User interface and CRUD operations

---

## API Server (Port 8000)

Base URL: `http://localhost:8000`

### GET /
System information and capabilities.

**Response:**
```json
{
    "message": "Nuclear Internship Detection - Multi-Agent System",
    "version": "3.0",
    "architecture": "Multi-Agent Orchestrated Workflow",
    "agents": {
        "orchestrator": "Workflow coordination and database management",
        "scout": "GitHub/ATS internship discovery",
        "analyzer": "Resume matching",
        "quality": "Professional review (coming soon)",
        "applicant": "Auto-application (coming soon)"
    },
    "capabilities": [...]
}
```

---

### POST /jobs
Submit a new job to the multi-agent system.

**Request:**
```json
{
    "goal": "Find machine learning internships"
}
```

**Response:**
```json
{
    "job_id": "a1b2c3d4",
    "status": "queued",
    "message": "Multi-agent system started"
}
```

---

### GET /jobs/{job_id}
Check job status and results.

**Response:**
```json
{
    "id": "a1b2c3d4",
    "goal": "Find machine learning internships",
    "status": "completed",
    "created_at": "2026-02-01T10:00:00",
    "completed_at": "2026-02-01T10:05:00",
    "result": {...}
}
```

---

### POST /run-workflow
Execute the orchestrated workflow directly (bypasses LLM).

**Response:**
```json
{
    "success": true,
    "message": "Workflow completed successfully",
    "result": {
        "data": {
            "total_discovered": 2697,
            "new_saved": 127,
            "duplicates_filtered": 89,
            "scored_count": 127,
            "email_sent": true,
            "workflow_complete": true
        }
    }
}
```

---

## Web Dashboard (Port 8001)

Base URL: `http://localhost:8001`

### GET /
Main dashboard HTML page.

---

### GET /api/stats
Database statistics.

**Response:**
```json
{
    "total": 2697,
    "applied": 45,
    "interviewing": 3,
    "this_week": 127
}
```

---

### GET /api/internships
Get internships with filtering and sorting.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search in title, company, description |
| status | string | Filter by status (not_applied, applied, interviewing, rejected, offer) |
| sort | string | Sort by: relevance, posted, date, company |
| limit | int | Max results (default: 50) |

**Example:**
```
GET /api/internships?search=google&status=not_applied&sort=relevance&limit=20
```

**Response:**
```json
[
    {
        "id": 1,
        "title": "Software Engineer Intern",
        "company": "Google",
        "url": "https://...",
        "location": "Mountain View, CA",
        "description": "...",
        "discovered_at": "2026-02-01T10:00:00",
        "application_status": "not_applied",
        "relevance_score": 85.5,
        "age_days": 3
    }
]
```

---

### POST /api/internships
Create a new internship manually.

**Request:**
```json
{
    "title": "Data Science Intern",
    "company": "Startup Inc",
    "location": "Remote",
    "url": "https://example.com/apply",
    "notes": "Found via referral"
}
```

**Response:**
```json
{
    "success": true
}
```

---

### PUT /api/internships/{id}
Update an internship.

**Request:**
```json
{
    "title": "Updated Title",
    "application_status": "applied",
    "notes": "Applied on 2/1"
}
```

**Response:**
```json
{
    "success": true
}
```

---

### DELETE /api/internships/{id}
Delete an internship.

**Response:**
```json
{
    "success": true
}
```

---

### POST /api/internships/{id}/apply
Mark internship as applied.

**Response:**
```json
{
    "success": true
}
```

---

### GET /api/internships/{id}/analyze
Analyze job for ATS optimization.

**Response:**
```json
{
    "success": true,
    "data": {
        "internship_id": 67,
        "title": "Software Engineer Intern - Python",
        "company": "Garda Capital Partners",
        "ats_score": 50.0,
        "job_keywords": ["python", "intern", "backend"],
        "matching_keywords": ["python", "backend"],
        "missing_keywords": ["intern"],
        "match_count": 2,
        "total_keywords": 3,
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

---

## Telegram Bot Commands

The Telegram bot listens for commands when running:

| Command | Description |
|---------|-------------|
| /health | Check if services are running |
| /status | Show system status and stats |
| /check | Run internship discovery now |
| /backup | Backup the database |
| /help | Show available commands |

---

## Error Responses

All endpoints return errors in this format:

```json
{
    "success": false,
    "error": "Error message here"
}
```

HTTP Status Codes:
- 200 - Success
- 404 - Not found
- 500 - Server error
