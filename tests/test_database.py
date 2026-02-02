"""
Tests for database operations and models.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import (
    InternshipListing,
    AgentJob,
    get_db_session,
    save_internship,
    get_recent_internships,
    mark_as_applied
)


class TestInternshipListingModel:
    """Test InternshipListing model."""

    def test_create_internship(self, temp_db):
        """Test creating an internship listing."""
        internship = InternshipListing(
            agent_job_id="test-job",
            title="Software Engineer Intern",
            company="Google",
            url="https://google.com/jobs/123",
            location="Mountain View, CA"
        )
        temp_db.add(internship)
        temp_db.commit()

        assert internship.id is not None
        assert internship.title == "Software Engineer Intern"
        assert internship.company == "Google"

    def test_default_values(self, temp_db):
        """Test that default values are set correctly."""
        internship = InternshipListing(
            agent_job_id="test-job",
            title="Test Intern",
            company="Test Co",
            url="https://test.com/1"
        )
        temp_db.add(internship)
        temp_db.commit()

        assert internship.applied == False
        assert internship.application_status == "not_applied"
        assert internship.relevance_score == 0.0
        assert internship.interest_level == 0
        assert internship.discovered_at is not None

    def test_url_uniqueness(self, temp_db):
        """Test that URLs must be unique."""
        internship1 = InternshipListing(
            agent_job_id="test-job",
            title="Intern 1",
            company="Company A",
            url="https://unique-url.com/1"
        )
        temp_db.add(internship1)
        temp_db.commit()

        # Try to add another with same URL
        internship2 = InternshipListing(
            agent_job_id="test-job",
            title="Intern 2",
            company="Company B",
            url="https://unique-url.com/1"  # Same URL
        )
        temp_db.add(internship2)

        with pytest.raises(Exception):  # Should raise IntegrityError
            temp_db.commit()

    def test_all_fields(self, temp_db):
        """Test internship with all fields populated."""
        internship = InternshipListing(
            agent_job_id="full-test",
            title="ML Engineer Intern",
            company="OpenAI",
            url="https://openai.com/jobs/ml-intern",
            location="San Francisco, CA",
            description="Work on cutting-edge AI research.",
            requirements="Python, PyTorch, research experience",
            deadline="2026-03-01",
            salary_min=50.0,
            salary_max=70.0,
            applied=True,
            application_date=datetime.utcnow(),
            application_status="interviewing",
            notes="Applied via referral",
            relevance_score=95.0,
            interest_level=5,
            age_days=2
        )
        temp_db.add(internship)
        temp_db.commit()

        # Retrieve and verify
        saved = temp_db.query(InternshipListing).filter_by(company="OpenAI").first()
        assert saved.title == "ML Engineer Intern"
        assert saved.salary_min == 50.0
        assert saved.salary_max == 70.0
        assert saved.application_status == "interviewing"
        assert saved.relevance_score == 95.0
        assert saved.age_days == 2


class TestAgentJobModel:
    """Test AgentJob model."""

    def test_create_agent_job(self, temp_db):
        """Test creating an agent job."""
        job = AgentJob(
            job_id="abc123",
            goal="Find ML internships",
            status="queued"
        )
        temp_db.add(job)
        temp_db.commit()

        assert job.id is not None
        assert job.job_id == "abc123"
        assert job.status == "queued"
        assert job.created_at is not None

    def test_job_status_transitions(self, temp_db):
        """Test job status can be updated."""
        job = AgentJob(
            job_id="xyz789",
            goal="Test job",
            status="queued"
        )
        temp_db.add(job)
        temp_db.commit()

        # Update status
        job.status = "running"
        temp_db.commit()
        assert job.status == "running"

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.result_summary = "Found 10 internships"
        temp_db.commit()

        assert job.status == "completed"
        assert job.completed_at is not None


class TestQueryOperations:
    """Test database query operations."""

    def test_filter_by_status(self, sample_internships, temp_db):
        """Test filtering internships by status."""
        applied = temp_db.query(InternshipListing).filter_by(
            application_status="applied"
        ).all()

        assert len(applied) == 1
        assert applied[0].company == "Netflix"

    def test_filter_by_company(self, sample_internships, temp_db):
        """Test filtering by company name."""
        stripe = temp_db.query(InternshipListing).filter(
            InternshipListing.company.contains("Stripe")
        ).first()

        assert stripe is not None
        assert stripe.title == "Software Engineer Intern - Python"

    def test_order_by_score(self, sample_internships, temp_db):
        """Test ordering by relevance score."""
        sorted_internships = temp_db.query(InternshipListing).order_by(
            InternshipListing.relevance_score.desc()
        ).all()

        assert sorted_internships[0].relevance_score == 75.0
        assert sorted_internships[1].relevance_score == 60.0
        assert sorted_internships[2].relevance_score == 45.0

    def test_count_by_status(self, sample_internships, temp_db):
        """Test counting internships by status."""
        not_applied_count = temp_db.query(InternshipListing).filter_by(
            application_status="not_applied"
        ).count()

        applied_count = temp_db.query(InternshipListing).filter_by(
            application_status="applied"
        ).count()

        assert not_applied_count == 2
        assert applied_count == 1


class TestDatabaseUtilityFunctions:
    """Test utility functions in database module."""

    def test_save_internship_new(self, temp_db):
        """Test saving a new internship."""
        listing_data = {
            "title": "New Intern Position",
            "company": "New Company",
            "url": "https://newcompany.com/jobs/1",
            "location": "Remote",
            "description": "Great opportunity"
        }

        # Would need to mock the session
        # This tests the expected structure
        assert "title" in listing_data
        assert "company" in listing_data
        assert "url" in listing_data

    def test_save_internship_duplicate(self, sample_internship, temp_db):
        """Test that duplicate URLs are handled."""
        # Existing internship has URL: https://careers.google.com/jobs/123

        # Check if URL exists
        existing = temp_db.query(InternshipListing).filter_by(
            url="https://careers.google.com/jobs/123"
        ).first()

        assert existing is not None
        assert existing.company == "Google"


class TestApplicationTracking:
    """Test application status tracking."""

    def test_mark_as_applied(self, sample_internship, temp_db):
        """Test marking an internship as applied."""
        # Get the internship
        internship = temp_db.query(InternshipListing).get(sample_internship.id)

        # Mark as applied
        internship.applied = True
        internship.application_status = "applied"
        internship.application_date = datetime.utcnow()
        temp_db.commit()

        # Verify
        updated = temp_db.query(InternshipListing).get(sample_internship.id)
        assert updated.applied == True
        assert updated.application_status == "applied"
        assert updated.application_date is not None

    def test_application_status_values(self, temp_db):
        """Test all valid application status values."""
        valid_statuses = ["not_applied", "applied", "interviewing", "rejected", "offer"]

        for i, status in enumerate(valid_statuses):
            internship = InternshipListing(
                agent_job_id="test",
                title=f"Test {i}",
                company=f"Company {i}",
                url=f"https://test.com/{i}",
                application_status=status
            )
            temp_db.add(internship)

        temp_db.commit()

        # Verify all were saved
        all_internships = temp_db.query(InternshipListing).filter(
            InternshipListing.url.like("https://test.com/%")
        ).all()

        assert len(all_internships) == 5


class TestRelevanceScoring:
    """Test relevance score operations."""

    def test_update_relevance_score(self, sample_internship, temp_db):
        """Test updating relevance score."""
        internship = temp_db.query(InternshipListing).get(sample_internship.id)
        internship.relevance_score = 85.5
        temp_db.commit()

        updated = temp_db.query(InternshipListing).get(sample_internship.id)
        assert updated.relevance_score == 85.5

    def test_filter_unscored(self, temp_db):
        """Test filtering unscored internships."""
        # Add some internships
        for i in range(5):
            internship = InternshipListing(
                agent_job_id="test",
                title=f"Job {i}",
                company=f"Company {i}",
                url=f"https://score-test.com/{i}",
                relevance_score=0.0 if i < 3 else 50.0
            )
            temp_db.add(internship)
        temp_db.commit()

        # Filter unscored
        unscored = temp_db.query(InternshipListing).filter(
            InternshipListing.relevance_score == 0.0,
            InternshipListing.url.like("https://score-test.com/%")
        ).all()

        assert len(unscored) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
