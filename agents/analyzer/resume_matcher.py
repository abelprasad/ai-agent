import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.tools.base import BaseTool
from shared.database.database import get_db_session, InternshipListing
import re
import json

class ResumeMatcher(BaseTool):
    name = "match_resume"
    description = "Score internships based on resume/skills match"

    def __init__(self, resume_path=None):
        self.skills = []
        self.keywords = []
        # Use project directory for resume path
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.resume_path = resume_path or os.path.join(project_dir, "resume.txt")
        self._load_resume()

    def _load_resume(self):
        """Load and parse resume to extract skills"""
        # Default tech skills if no resume found
        default_skills = [
            # Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql", "r",
            # Web
            "react", "angular", "vue", "node", "express", "django", "flask", "fastapi",
            # Data/ML
            "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy",
            "data science", "data analysis", "sql", "nosql", "mongodb", "postgresql",
            # Cloud/DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins", "terraform",
            # General
            "git", "linux", "agile", "rest api", "microservices", "algorithms", "data structures"
        ]

        try:
            if os.path.exists(self.resume_path):
                with open(self.resume_path, 'r') as f:
                    content = f.read().lower()
                    # Extract skills from resume
                    self.skills = self._extract_skills(content)
                    print(f"[ResumeMatcher] Loaded {len(self.skills)} skills from resume")
            else:
                print(f"[ResumeMatcher] No resume found at {self.resume_path}, using default skills")
                self.skills = default_skills
        except Exception as e:
            print(f"[ResumeMatcher] Error loading resume: {e}, using defaults")
            self.skills = default_skills

        # Common CS internship keywords
        self.keywords = [
            "software engineer", "software developer", "swe", "backend", "frontend",
            "full stack", "fullstack", "data engineer", "data scientist", "ml engineer",
            "machine learning", "ai", "artificial intelligence", "devops", "cloud",
            "mobile", "ios", "android", "web developer", "api", "infrastructure"
        ]

    def _extract_skills(self, content):
        """Extract technical skills from resume content"""
        # Common tech skills to look for
        tech_patterns = [
            r'\b(python|java|javascript|typescript|c\+\+|c#|golang|go|rust|ruby|php|swift|kotlin|scala)\b',
            r'\b(react|angular|vue|svelte|next\.?js|node\.?js|express|django|flask|fastapi|spring|rails)\b',
            r'\b(aws|azure|gcp|google cloud|docker|kubernetes|k8s|terraform|jenkins|ci/cd)\b',
            r'\b(sql|mysql|postgresql|postgres|mongodb|redis|elasticsearch|dynamodb|firebase)\b',
            r'\b(tensorflow|pytorch|keras|scikit-learn|pandas|numpy|matplotlib|opencv)\b',
            r'\b(machine learning|deep learning|nlp|computer vision|data science|ai)\b',
            r'\b(git|github|gitlab|linux|unix|bash|shell|vim|vscode)\b',
            r'\b(rest|graphql|grpc|microservices|api|websocket)\b',
            r'\b(agile|scrum|jira|confluence|kanban)\b',
        ]

        found_skills = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_skills.update([m.lower() for m in matches])

        return list(found_skills) if found_skills else None

    def execute(self, internship_ids=None, update_db=True):
        """Score internships based on resume match"""
        try:
            session = get_db_session()

            if internship_ids:
                internships = session.query(InternshipListing).filter(
                    InternshipListing.id.in_(internship_ids)
                ).all()
            else:
                # Score all unscored internships
                internships = session.query(InternshipListing).filter(
                    InternshipListing.relevance_score == 0.0
                ).all()

            print(f"[ResumeMatcher] Scoring {len(internships)} internships...")

            scored_count = 0
            for internship in internships:
                score = self._calculate_score(internship)

                if update_db:
                    internship.relevance_score = score
                    scored_count += 1

            if update_db:
                session.commit()

            session.close()

            return {
                "success": True,
                "data": {
                    "scored_count": scored_count,
                    "skills_used": len(self.skills)
                }
            }

        except Exception as e:
            print(f"[ResumeMatcher] Error: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_score(self, internship):
        """Calculate relevance score for an internship (0-100)"""
        max_score = 100

        # Combine title, company, location, description for matching
        text = f"{internship.title} {internship.company} {internship.description or ''}".lower()

        # Skill matching (70% of score)
        skill_matches = 0
        for skill in self.skills:
            if skill.lower() in text:
                skill_matches += 1

        if self.skills:
            skill_score = min(70, (skill_matches / len(self.skills)) * 100)
        else:
            skill_score = 35  # Default if no skills

        # Keyword matching (30% of score)
        keyword_matches = 0
        for keyword in self.keywords:
            if keyword.lower() in text:
                keyword_matches += 1

        keyword_score = min(30, (keyword_matches / len(self.keywords)) * 60)

        # Calculate final score
        score = skill_score + keyword_score

        return min(max_score, round(score, 1))

    def get_top_matches(self, limit=20):
        """Get top matching internships"""
        session = get_db_session()

        internships = session.query(InternshipListing).filter(
            InternshipListing.relevance_score > 0
        ).order_by(
            InternshipListing.relevance_score.desc()
        ).limit(limit).all()

        results = []
        for i in internships:
            results.append({
                "id": i.id,
                "title": i.title,
                "company": i.company,
                "location": i.location,
                "score": i.relevance_score,
                "url": i.url
            })

        session.close()
        return results

    def analyze_job(self, internship_id):
        """
        Analyze a job posting for ATS optimization.
        Returns: job keywords, matching keywords, missing keywords, and recommendations.
        """
        try:
            session = get_db_session()
            internship = session.query(InternshipListing).get(internship_id)

            if not internship:
                session.close()
                return {"success": False, "error": "Internship not found"}

            # Combine all job text
            job_text = f"{internship.title} {internship.description or ''} {internship.requirements or ''}".lower()

            # Extract keywords from job posting
            job_keywords = self._extract_skills(job_text) or []

            # Also extract from title specifically (high priority keywords)
            title_keywords = self._extract_skills(internship.title.lower()) or []

            # Add common job requirement keywords
            job_keywords = list(set(job_keywords + self._extract_requirement_keywords(job_text)))

            # Get resume skills (already loaded in self.skills)
            resume_skills = [s.lower() for s in self.skills]

            # Find matches and gaps
            matching = [kw for kw in job_keywords if kw.lower() in resume_skills]
            missing = [kw for kw in job_keywords if kw.lower() not in resume_skills]

            # Calculate ATS score
            if job_keywords:
                ats_score = round((len(matching) / len(job_keywords)) * 100, 1)
            else:
                ats_score = 50.0  # Default if no keywords found

            # Generate recommendations
            recommendations = self._generate_recommendations(missing, ats_score, internship)

            session.close()

            return {
                "success": True,
                "data": {
                    "internship_id": internship_id,
                    "title": internship.title,
                    "company": internship.company,
                    "ats_score": ats_score,
                    "job_keywords": job_keywords,
                    "matching_keywords": matching,
                    "missing_keywords": missing,
                    "match_count": len(matching),
                    "total_keywords": len(job_keywords),
                    "recommendations": recommendations
                }
            }

        except Exception as e:
            print(f"[ResumeMatcher] Error analyzing job: {e}")
            return {"success": False, "error": str(e)}

    def _extract_requirement_keywords(self, text):
        """Extract additional requirement keywords beyond tech skills"""
        requirement_patterns = [
            # Experience levels
            r'\b(entry.level|junior|senior|staff|intern|internship|co.op|new.grad)\b',
            # Degree requirements
            r'\b(bachelor|master|phd|bs|ms|computer.science|cs|engineering)\b',
            # Soft skills
            r'\b(communication|teamwork|leadership|problem.solving|analytical|detail.oriented)\b',
            # Work style
            r'\b(remote|hybrid|onsite|full.time|part.time)\b',
            # Specific tech areas
            r'\b(frontend|backend|fullstack|full.stack|devops|mlops|data.engineering)\b',
            r'\b(distributed.systems|microservices|cloud.native|serverless)\b',
            r'\b(testing|qa|automation|performance|security|scalability)\b',
        ]

        found = set()
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found.update([m.lower().replace('.', ' ') for m in matches])

        return list(found)

    def _generate_recommendations(self, missing, ats_score, internship):
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        # Score-based recommendations
        if ats_score < 30:
            recommendations.append({
                "priority": "high",
                "type": "low_match",
                "message": "Low keyword match. This role may not align well with your current resume, or consider adding relevant skills."
            })
        elif ats_score < 50:
            recommendations.append({
                "priority": "medium",
                "type": "moderate_match",
                "message": "Moderate match. Adding a few key skills could significantly improve your chances."
            })
        elif ats_score >= 70:
            recommendations.append({
                "priority": "low",
                "type": "strong_match",
                "message": "Strong match! Your resume aligns well with this role."
            })

        # Missing keywords recommendations
        if missing:
            # Prioritize technical skills
            tech_missing = [kw for kw in missing if kw in [
                'python', 'java', 'javascript', 'typescript', 'react', 'node',
                'aws', 'docker', 'kubernetes', 'sql', 'mongodb', 'git',
                'tensorflow', 'pytorch', 'machine learning', 'deep learning'
            ]]

            if tech_missing:
                recommendations.append({
                    "priority": "high",
                    "type": "missing_tech",
                    "message": f"Add these technical skills to your resume: {', '.join(tech_missing[:5])}"
                })

            other_missing = [kw for kw in missing if kw not in tech_missing][:5]
            if other_missing:
                recommendations.append({
                    "priority": "medium",
                    "type": "missing_keywords",
                    "message": f"Consider adding: {', '.join(other_missing)}"
                })

        # Company-specific tips
        company_lower = internship.company.lower() if internship.company else ""
        faang = ['google', 'meta', 'amazon', 'apple', 'microsoft', 'netflix']
        if any(f in company_lower for f in faang):
            recommendations.append({
                "priority": "info",
                "type": "faang_tip",
                "message": "FAANG company - emphasize system design, algorithms, and scalability experience."
            })

        return recommendations


# Standalone test
if __name__ == "__main__":
    matcher = ResumeMatcher()
    print(f"Skills loaded: {matcher.skills[:10]}...")

    result = matcher.execute()
    print(f"Result: {result}")

    top = matcher.get_top_matches(10)
    print("\nTop 10 matches:")
    for t in top:
        print(f"  [{t['score']}] {t['title']} at {t['company']}")
