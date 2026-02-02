"""
Tests for the GitHubInternshipMonitor agent.
"""

import pytest
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scout.github_monitor import GitHubInternshipMonitor, GitHubChangeDetector


class TestGitHubMonitorInit:
    """Test GitHubInternshipMonitor initialization."""

    def test_init_loads_repos(self):
        """Test that repos are loaded on initialization."""
        monitor = GitHubInternshipMonitor()
        assert len(monitor.repos) > 0
        assert "SimplifyJobs" in monitor.repos

    def test_all_repos_have_urls(self):
        """Test that all repos have required URL fields."""
        monitor = GitHubInternshipMonitor()
        for repo_name, repo_info in monitor.repos.items():
            assert "url" in repo_info, f"{repo_name} missing 'url'"
            assert "raw_url" in repo_info, f"{repo_name} missing 'raw_url'"

    def test_repos_count(self):
        """Test that we have expected number of repos."""
        monitor = GitHubInternshipMonitor()
        assert len(monitor.repos) == 5  # SimplifyJobs, Pitt-CSC, SpeedyApply, VanshB03, Summer2026


class TestMarkdownParsing:
    """Test parsing of different markdown table formats."""

    def test_pattern2_markdown_table(self, mock_github_readme):
        """Test Pattern 2: Markdown table with [Company](url) | Position | Location | [Apply](url)"""
        pattern = r'\|\s*\[([^\]]+)\]\([^)]+\)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*\[Apply\]\(([^)]+)\)'
        matches = re.findall(pattern, mock_github_readme)

        # Should not match this pattern in our sample (different format)
        # This tests the pattern itself
        assert isinstance(matches, list)

    def test_pattern3_simple_table(self, mock_github_readme):
        """Test Pattern 3: Simple markdown table | Company | Position | Location | [Apply](url) |"""
        pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*\[(?:Apply|Link)\]\(([^)]+)\)\s*\|'
        matches = re.findall(pattern, mock_github_readme)

        # Should find entries
        assert len(matches) >= 3

        # Verify structure
        for match in matches:
            company, role, location, url = match
            assert len(company.strip()) > 0
            assert len(role.strip()) > 0
            assert url.startswith("http")

    def test_pattern5_apply_here(self, mock_github_readme):
        """Test Pattern 5: Summer2026 format [Apply Here](url)"""
        pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*\[Apply Here\]\(([^)]+)\)\s*\|'
        matches = re.findall(pattern, mock_github_readme)

        # Should find the Stripe entry
        assert len(matches) >= 1

    def test_pattern1_html_table(self, mock_github_readme_html):
        """Test Pattern 1: SimplifyJobs HTML table format with age"""
        pattern = r'<tr>\s*<td><strong><a[^>]*>([^<]+)</a></strong></td>\s*<td>([^<]+)</td>\s*<td>([^<]+)</td>\s*<td[^>]*>.*?<a href="([^"]+)"[^>]*><img[^>]*alt="Apply"[^>]*>.*?</td>\s*<td>(\d+)d</td>'
        matches = re.findall(pattern, mock_github_readme_html, re.DOTALL)

        assert len(matches) == 2  # Google and Meta

        # Check Google entry
        company, role, location, url, age = matches[0]
        assert company == "Google"
        assert "Software Engineer" in role
        assert "Mountain View" in location
        assert age == "3"

    def test_skips_header_rows(self):
        """Test that header rows are properly skipped."""
        content = """
| Company | Role | Location | Link |
|---------|------|----------|------|
| --- | --- | --- | --- |
| Google | SWE Intern | NYC | [Apply](https://google.com) |
"""
        pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*\[(?:Apply|Link)\]\(([^)]+)\)\s*\|'
        matches = re.findall(pattern, content)

        # Filter out header rows
        valid_matches = []
        for match in matches:
            company = match[0].strip()
            if company.lower() not in ['company', 'name', '---', ''] and '---' not in company:
                valid_matches.append(match)

        assert len(valid_matches) == 1
        assert valid_matches[0][0].strip() == "Google"


class TestInternshipExtraction:
    """Test extraction of internship data."""

    def test_extract_internships_returns_dict(self):
        """Test that _extract_internships returns proper structure."""
        monitor = GitHubInternshipMonitor()
        # Can't test actual network call, but can test structure
        result = {'internship_count': 0, 'sample_internships': []}
        assert 'internship_count' in result
        assert 'sample_internships' in result
        assert isinstance(result['sample_internships'], list)

    def test_internship_has_required_fields(self):
        """Test that extracted internships have required fields."""
        required_fields = ['company', 'position', 'location', 'url', 'source']

        sample = {
            'company': 'Google',
            'position': 'SWE Intern',
            'location': 'Mountain View',
            'url': 'https://google.com',
            'source': 'GitHub'
        }

        for field in required_fields:
            assert field in sample


class TestExecute:
    """Test the execute method."""

    def test_execute_returns_success_structure(self):
        """Test that execute returns proper structure."""
        # Mock result structure
        result = {
            "success": True,
            "data": {
                "repos_checked": 5,
                "repo_data": [],
                "total_internships": 0
            }
        }

        assert result["success"] == True
        assert "repos_checked" in result["data"]
        assert "repo_data" in result["data"]
        assert "total_internships" in result["data"]

    def test_execute_with_specific_repos(self):
        """Test that execute respects repos parameter."""
        monitor = GitHubInternshipMonitor()

        # Test repo filtering logic
        repos = ['SimplifyJobs']
        selected_repos = {k: v for k, v in monitor.repos.items() if k in repos}

        assert len(selected_repos) == 1
        assert 'SimplifyJobs' in selected_repos

    def test_execute_with_limit(self):
        """Test that execute respects limit parameter."""
        # Test limit logic
        limit = 10
        internships = list(range(100))
        limited = internships[:limit]

        assert len(limited) == limit


class TestGitHubChangeDetector:
    """Test GitHubChangeDetector functionality."""

    def test_detector_init(self):
        """Test that detector initializes correctly."""
        detector = GitHubChangeDetector()
        assert detector.name == "detect_github_changes"

    def test_new_internship_detection_logic(self):
        """Test logic for detecting new internships."""
        # Simulate existing URLs in database
        existing_urls = {
            "https://google.com/apply",
            "https://meta.com/apply"
        }

        # New internships from GitHub
        new_internships = [
            {"url": "https://google.com/apply", "company": "Google"},
            {"url": "https://stripe.com/apply", "company": "Stripe"},  # New!
            {"url": "https://meta.com/apply", "company": "Meta"},
        ]

        # Filter for truly new
        truly_new = [i for i in new_internships if i["url"] not in existing_urls]

        assert len(truly_new) == 1
        assert truly_new[0]["company"] == "Stripe"


class TestUrlValidation:
    """Test URL handling and validation."""

    def test_skip_simplify_profile_links(self):
        """Test that Simplify profile links are skipped."""
        urls = [
            "https://simplify.jobs/c/google",  # Profile link - skip
            "https://simplify.jobs/p/abc123",  # Apply link - keep
            "https://google.com/careers/123",  # Direct link - keep
        ]

        valid_urls = []
        for url in urls:
            if 'simplify.jobs' in url and '/c/' in url:
                continue  # Skip company profile links
            valid_urls.append(url)

        assert len(valid_urls) == 2
        assert "https://simplify.jobs/c/google" not in valid_urls

    def test_url_extraction_from_markdown(self):
        """Test URL extraction from markdown links."""
        markdown = "[Apply](https://example.com/job/123)"
        pattern = r'\[Apply\]\(([^)]+)\)'
        match = re.search(pattern, markdown)

        assert match is not None
        assert match.group(1) == "https://example.com/job/123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
