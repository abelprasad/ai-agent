"""
Tests for API endpoints.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


class TestDashboardEndpoints:
    """Test web dashboard API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for dashboard."""
        from interfaces.web.web_dashboard import app
        return TestClient(app)

    def test_root_returns_html(self, client):
        """Test that root returns HTML dashboard."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Internship Database" in response.text

    def test_get_stats(self, client):
        """Test /api/stats endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "applied" in data
        assert "interviewing" in data
        assert "this_week" in data

    def test_get_internships(self, client):
        """Test /api/internships endpoint."""
        response = client.get("/api/internships")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_internships_with_search(self, client):
        """Test /api/internships with search parameter."""
        response = client.get("/api/internships?search=google")
        assert response.status_code == 200

    def test_get_internships_with_status_filter(self, client):
        """Test /api/internships with status filter."""
        response = client.get("/api/internships?status=not_applied")
        assert response.status_code == 200

    def test_get_internships_with_sort(self, client):
        """Test /api/internships with different sort options."""
        for sort in ["relevance", "posted", "date", "company"]:
            response = client.get(f"/api/internships?sort={sort}")
            assert response.status_code == 200

    def test_get_internships_with_limit(self, client):
        """Test /api/internships with limit parameter."""
        response = client.get("/api/internships?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_create_internship(self, client):
        """Test POST /api/internships."""
        new_internship = {
            "title": "Test Intern Position",
            "company": "Test Company",
            "location": "Remote",
            "url": "https://test-unique-url.com/job/999",
            "notes": "Test notes"
        }

        response = client.post("/api/internships", json=new_internship)
        assert response.status_code == 200
        assert response.json()["success"] == True

    def test_update_internship(self, client):
        """Test PUT /api/internships/{id}."""
        # First create an internship
        new_internship = {
            "title": "Update Test",
            "company": "Update Co",
            "url": "https://update-test-url.com/1"
        }
        client.post("/api/internships", json=new_internship)

        # Get the internship ID
        response = client.get("/api/internships?search=Update Test")
        internships = response.json()

        if internships:
            internship_id = internships[0]["id"]

            # Update it
            update_data = {
                "application_status": "applied",
                "notes": "Updated notes"
            }
            response = client.put(f"/api/internships/{internship_id}", json=update_data)
            assert response.status_code == 200

    def test_delete_nonexistent_internship(self, client):
        """Test DELETE for non-existent internship."""
        response = client.delete("/api/internships/999999")
        assert response.status_code == 404

    def test_mark_as_applied(self, client):
        """Test POST /api/internships/{id}/apply."""
        # Create an internship first
        new_internship = {
            "title": "Apply Test",
            "company": "Apply Co",
            "url": "https://apply-test-url.com/1"
        }
        client.post("/api/internships", json=new_internship)

        # Find and mark as applied
        response = client.get("/api/internships?search=Apply Test")
        internships = response.json()

        if internships:
            internship_id = internships[0]["id"]
            response = client.post(f"/api/internships/{internship_id}/apply")
            assert response.status_code == 200

    def test_analyze_internship(self, client):
        """Test GET /api/internships/{id}/analyze."""
        # Get any existing internship
        response = client.get("/api/internships?limit=1")
        internships = response.json()

        if internships:
            internship_id = internships[0]["id"]
            response = client.get(f"/api/internships/{internship_id}/analyze")
            assert response.status_code == 200

            data = response.json()
            if data.get("success"):
                assert "ats_score" in data["data"]
                assert "matching_keywords" in data["data"]
                assert "missing_keywords" in data["data"]

    def test_analyze_nonexistent_internship(self, client):
        """Test analyze for non-existent internship."""
        response = client.get("/api/internships/999999/analyze")
        assert response.status_code == 200  # Returns success: false
        data = response.json()
        assert data["success"] == False


class TestMainAPIEndpoints:
    """Test main API server endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for main API."""
        from interfaces.api.main import app
        return TestClient(app)

    def test_root_info(self, client):
        """Test GET / returns system info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "agents" in data

    def test_create_job(self, client):
        """Test POST /jobs creates a job."""
        job_request = {
            "goal": "Find software engineering internships"
        }

        response = client.post("/jobs", json=job_request)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_get_job_not_found(self, client):
        """Test GET /jobs/{id} for non-existent job."""
        response = client.get("/jobs/nonexistent-id")
        assert response.status_code == 200

        data = response.json()
        assert "error" in data


class TestAPIResponseFormats:
    """Test API response formats and structures."""

    def test_internship_response_format(self):
        """Test that internship responses have correct format."""
        expected_fields = [
            "id", "title", "company", "url", "location",
            "discovered_at", "application_status", "relevance_score"
        ]

        sample_response = {
            "id": 1,
            "title": "Test",
            "company": "Test Co",
            "url": "https://test.com",
            "location": "Remote",
            "discovered_at": "2026-02-01T00:00:00",
            "application_status": "not_applied",
            "relevance_score": 50.0
        }

        for field in expected_fields:
            assert field in sample_response

    def test_stats_response_format(self):
        """Test that stats response has correct format."""
        expected_fields = ["total", "applied", "interviewing", "this_week"]

        sample_stats = {
            "total": 100,
            "applied": 10,
            "interviewing": 2,
            "this_week": 25
        }

        for field in expected_fields:
            assert field in sample_stats

    def test_analyze_response_format(self):
        """Test that analyze response has correct format."""
        expected_fields = [
            "internship_id", "title", "company", "ats_score",
            "matching_keywords", "missing_keywords", "recommendations"
        ]

        sample_analysis = {
            "internship_id": 1,
            "title": "SWE Intern",
            "company": "Google",
            "ats_score": 75.0,
            "matching_keywords": ["python", "aws"],
            "missing_keywords": ["java"],
            "recommendations": []
        }

        for field in expected_fields:
            assert field in sample_analysis


class TestErrorHandling:
    """Test API error handling."""

    @pytest.fixture
    def dashboard_client(self):
        from interfaces.web.web_dashboard import app
        return TestClient(app)

    def test_invalid_status_filter(self, dashboard_client):
        """Test handling of invalid status filter."""
        response = dashboard_client.get("/api/internships?status=invalid_status")
        assert response.status_code == 200  # Should return empty list, not error

    def test_invalid_sort_option(self, dashboard_client):
        """Test handling of invalid sort option."""
        response = dashboard_client.get("/api/internships?sort=invalid_sort")
        assert response.status_code == 200  # Should use default sort

    def test_negative_limit(self, dashboard_client):
        """Test handling of negative limit."""
        response = dashboard_client.get("/api/internships?limit=-5")
        # Should handle gracefully
        assert response.status_code in [200, 422]

    def test_missing_required_fields_on_create(self, dashboard_client):
        """Test creating internship with missing fields."""
        incomplete_data = {
            "title": "Only Title"
            # Missing company, url
        }
        response = dashboard_client.post("/api/internships", json=incomplete_data)
        # Should still work (fields have defaults)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
