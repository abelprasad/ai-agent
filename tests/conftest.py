"""
Pytest configuration and shared fixtures for AI Agent tests.
"""

import pytest
import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database.database import Base, InternshipListing, AgentJob


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_internship(temp_db):
    """Create a sample internship for testing."""
    internship = InternshipListing(
        agent_job_id="test-job",
        title="Software Engineer Intern",
        company="Google",
        url="https://careers.google.com/jobs/123",
        location="Mountain View, CA",
        description="Work on distributed systems and machine learning projects.",
        requirements="Python, Java, distributed systems, cloud computing",
        relevance_score=0.0,
        application_status="not_applied"
    )
    temp_db.add(internship)
    temp_db.commit()
    return internship


@pytest.fixture
def sample_internships(temp_db):
    """Create multiple sample internships for testing."""
    internships = [
        InternshipListing(
            agent_job_id="test-job",
            title="Software Engineer Intern - Python",
            company="Stripe",
            url="https://stripe.com/jobs/1",
            location="San Francisco, CA",
            description="Build payment infrastructure using Python and AWS.",
            relevance_score=75.0,
            application_status="not_applied"
        ),
        InternshipListing(
            agent_job_id="test-job",
            title="Data Science Intern",
            company="Netflix",
            url="https://netflix.com/jobs/2",
            location="Los Gatos, CA",
            description="Apply machine learning to content recommendations.",
            relevance_score=60.0,
            application_status="applied"
        ),
        InternshipListing(
            agent_job_id="test-job",
            title="Frontend Developer Intern",
            company="Airbnb",
            url="https://airbnb.com/jobs/3",
            location="Seattle, WA",
            description="Build user interfaces with React and TypeScript.",
            relevance_score=45.0,
            application_status="not_applied"
        ),
    ]
    for i in internships:
        temp_db.add(i)
    temp_db.commit()
    return internships


@pytest.fixture
def temp_resume():
    """Create a temporary resume file for testing."""
    content = """
    John Doe
    Software Engineer

    Skills:
    - Python, JavaScript, TypeScript
    - React, Node.js, FastAPI
    - AWS, Docker, Kubernetes
    - PostgreSQL, MongoDB
    - Machine Learning, TensorFlow

    Experience:
    - Built REST APIs using Python and FastAPI
    - Developed frontend applications with React
    - Deployed applications on AWS using Docker
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_github_readme():
    """Sample GitHub README content for testing parsing."""
    return """
# Summer 2026 Tech Internships

| Company | Role | Location | Link |
|---------|------|----------|------|
| Google | Software Engineer Intern | Mountain View, CA | [Apply](https://google.com/apply) |
| Meta | ML Engineer Intern | Menlo Park, CA | [Apply](https://meta.com/apply) |
| Amazon | SDE Intern | Seattle, WA | [Apply](https://amazon.com/apply) |

## Other Opportunities

| Company | Role | Location | Application |
|---------|------|----------|-------------|
| Stripe | Backend Intern | San Francisco | [Apply Here](https://stripe.com/apply) |
"""


@pytest.fixture
def mock_github_readme_html():
    """Sample GitHub README with HTML table format (SimplifyJobs style)."""
    return """
<table>
<tr>
<td><strong><a href="https://google.com">Google</a></strong></td>
<td>Software Engineer Intern</td>
<td>Mountain View, CA</td>
<td><a href="https://google.com/apply"><img alt="Apply" src="button.png"></a></td>
<td>3d</td>
</tr>
<tr>
<td><strong><a href="https://meta.com">Meta</a></strong></td>
<td>ML Engineer Intern</td>
<td>Menlo Park, CA</td>
<td><a href="https://meta.com/apply"><img alt="Apply" src="button.png"></a></td>
<td>5d</td>
</tr>
</table>
"""
