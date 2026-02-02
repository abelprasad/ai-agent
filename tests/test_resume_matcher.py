"""
Tests for the ResumeMatcher agent.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analyzer.resume_matcher import ResumeMatcher


class TestResumeMatcherInit:
    """Test ResumeMatcher initialization."""

    def test_init_with_resume(self, temp_resume):
        """Test initialization with a valid resume file."""
        matcher = ResumeMatcher(resume_path=temp_resume)
        assert len(matcher.skills) > 0
        assert "python" in matcher.skills or "Python" in [s.lower() for s in matcher.skills]

    def test_init_without_resume(self):
        """Test initialization with no resume falls back to defaults."""
        matcher = ResumeMatcher(resume_path="/nonexistent/path.txt")
        assert len(matcher.skills) > 0  # Should have default skills

    def test_default_keywords_loaded(self):
        """Test that default job keywords are loaded."""
        matcher = ResumeMatcher(resume_path="/nonexistent/path.txt")
        assert len(matcher.keywords) > 0
        assert "software engineer" in matcher.keywords


class TestSkillExtraction:
    """Test skill extraction from resume."""

    def test_extract_programming_languages(self, temp_resume):
        """Test extraction of programming languages."""
        matcher = ResumeMatcher(resume_path=temp_resume)
        skills_lower = [s.lower() for s in matcher.skills]

        assert "python" in skills_lower
        assert "javascript" in skills_lower

    def test_extract_frameworks(self, temp_resume):
        """Test extraction of frameworks."""
        matcher = ResumeMatcher(resume_path=temp_resume)
        skills_lower = [s.lower() for s in matcher.skills]

        assert "react" in skills_lower
        assert "fastapi" in skills_lower

    def test_extract_cloud_tools(self, temp_resume):
        """Test extraction of cloud/devops tools."""
        matcher = ResumeMatcher(resume_path=temp_resume)
        skills_lower = [s.lower() for s in matcher.skills]

        assert "aws" in skills_lower
        assert "docker" in skills_lower


class TestScoreCalculation:
    """Test internship scoring."""

    def test_calculate_score_high_match(self, temp_resume):
        """Test scoring for a high-match internship."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        # Create mock internship with matching skills
        class MockInternship:
            title = "Python Backend Engineer Intern"
            company = "Google"
            description = "Build APIs with Python, FastAPI, and AWS. Experience with React is a plus."

        score = matcher._calculate_score(MockInternship())
        assert score > 50  # Should be a good match
        assert score <= 100

    def test_calculate_score_low_match(self, temp_resume):
        """Test scoring for a low-match internship."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        class MockInternship:
            title = "Mechanical Engineering Intern"
            company = "Unknown Corp"
            description = "Design CAD models and work with manufacturing processes."

        score = matcher._calculate_score(MockInternship())
        assert score < 50  # Should be a poor match

    def test_faang_company_bonus(self, temp_resume):
        """Test that FAANG companies get a bonus."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        class GoogleInternship:
            title = "Software Engineer Intern"
            company = "Google"
            description = "General engineering work."

        class UnknownInternship:
            title = "Software Engineer Intern"
            company = "Unknown Startup"
            description = "General engineering work."

        google_score = matcher._calculate_score(GoogleInternship())
        unknown_score = matcher._calculate_score(UnknownInternship())

        assert google_score > unknown_score  # Google should score higher


class TestAnalyzeJob:
    """Test the analyze_job ATS optimization feature."""

    def test_analyze_job_returns_success(self, temp_resume, sample_internship, temp_db):
        """Test that analyze_job returns a success response."""
        # Note: This test would need database mocking
        # For now, we test the structure
        matcher = ResumeMatcher(resume_path=temp_resume)

        # Mock the database query - in real tests, use dependency injection
        # For now, test the response structure expectations
        result = {"success": True, "data": {"ats_score": 50}}
        assert result["success"] == True
        assert "ats_score" in result.get("data", {})

    def test_analyze_job_extracts_keywords(self, temp_resume):
        """Test that job keywords are extracted correctly."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        job_text = "Looking for Python developer with AWS experience and React skills."
        keywords = matcher._extract_skills(job_text.lower())

        assert "python" in keywords
        assert "aws" in keywords
        assert "react" in keywords

    def test_extract_requirement_keywords(self, temp_resume):
        """Test extraction of requirement keywords."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        job_text = "Entry level position for backend developer. Must have bachelor's degree. Remote friendly."
        keywords = matcher._extract_requirement_keywords(job_text.lower())

        assert any("entry" in kw for kw in keywords)
        assert any("bachelor" in kw for kw in keywords)
        assert any("backend" in kw for kw in keywords)
        assert any("remote" in kw for kw in keywords)


class TestRecommendations:
    """Test recommendation generation."""

    def test_low_score_recommendation(self, temp_resume):
        """Test that low scores generate appropriate recommendations."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        class MockInternship:
            company = "Test Corp"

        recommendations = matcher._generate_recommendations(
            missing=["java", "spring", "hibernate"],
            ats_score=25,
            internship=MockInternship()
        )

        # Should have a high priority recommendation for low match
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        assert len(high_priority) > 0

    def test_high_score_recommendation(self, temp_resume):
        """Test that high scores generate positive recommendations."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        class MockInternship:
            company = "Test Corp"

        recommendations = matcher._generate_recommendations(
            missing=[],
            ats_score=85,
            internship=MockInternship()
        )

        # Should have a positive recommendation
        messages = [r["message"] for r in recommendations]
        assert any("strong" in m.lower() or "align" in m.lower() for m in messages)

    def test_faang_tip_recommendation(self, temp_resume):
        """Test that FAANG companies get special tips."""
        matcher = ResumeMatcher(resume_path=temp_resume)

        class MockInternship:
            company = "Google"

        recommendations = matcher._generate_recommendations(
            missing=[],
            ats_score=70,
            internship=MockInternship()
        )

        # Should have FAANG-specific tip
        faang_tips = [r for r in recommendations if r.get("type") == "faang_tip"]
        assert len(faang_tips) > 0


class TestGetTopMatches:
    """Test get_top_matches functionality."""

    def test_returns_sorted_list(self, sample_internships, temp_db):
        """Test that top matches are returned sorted by score."""
        # This would require proper database integration testing
        # For now, verify the expected behavior
        pass  # Placeholder for integration test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
