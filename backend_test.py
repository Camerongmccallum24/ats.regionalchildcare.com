#!/usr/bin/env python3
import requests
import json
import uuid
import time
import os
import base64
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

# Backend URL from frontend/.env
BACKEND_URL = "https://26e408c5-b9e9-47c2-87a0-063f508a5a8d.preview.emergentagent.com/api"

class GROEarlyLearningATSBackendTest(unittest.TestCase):
    """Test suite for GRO Early Learning ATS Backend"""
    
    def setUp(self):
        """Setup test data"""
        # Generate unique IDs for test data to avoid conflicts
        self.test_prefix = f"test_{uuid.uuid4().hex[:8]}"
        
        # Test job data
        self.job_data = {
            "title": f"{self.test_prefix}_Childcare Teacher",
            "location": "Mount Isa",
            "sponsorship_eligible": True,
            "relocation_support": True,
            "housing_support": True,
            "description": "We are looking for qualified childcare teachers for our Mount Isa center.",
            "requirements": ["Diploma in Early Childhood Education", "2+ years experience", "Working with Children Check"],
            "salary_range": "$65,000 - $75,000",
            "employment_type": "Full-time"
        }
        
        # Test candidate data
        self.candidate_data = {
            "email": f"{self.test_prefix}@example.com",
            "phone": "0412345678",
            "full_name": f"{self.test_prefix} Test Candidate",
            "location": "Brisbane",
            "visa_status": "temporary",
            "visa_type": "Working Holiday",
            "sponsorship_needed": True,
            "childcare_cert": "Diploma in Early Childhood Education",
            "experience_years": 3,
            "rural_experience": True,
            "relocation_willing": "yes",
            "housing_needed": True,
            "english_level": "fluent",
            "availability_start": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "salary_expectation": 70000,
            "notes": "Test candidate"
        }
        
        # Test interview data
        self.interview_data = {
            "interviewer_name": f"{self.test_prefix} Interviewer",
            "interviewer_email": f"{self.test_prefix}_interviewer@example.com",
            "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "duration_minutes": 60,
            "interview_type": "video",
            "location": None
        }
        
        # Sample PDF resume content (base64 encoded minimal PDF)
        self.sample_pdf_content = base64.b64decode(
            "JVBERi0xLjcKJeLjz9MKNSAwIG9iago8PAovRmlsdGVyIC9GbGF0ZURlY29kZQovTGVuZ3RoIDM4Cj4+CnN0cmVhbQp4nCvkMlAwMDC0"
            "NDI1MzY0NbYwMTTUszQyNDNSCOQqVDBUMABCCJGcq5ALAFQ5B0MKZW5kc3RyZWFtCmVuZG9iago0IDAgb2JqCjw8Ci9UeXBlIC9QYWdl"
            "Ci9NZWRpYUJveCBbMCAwIDYxMiA3OTJdCi9SZXNvdXJjZXMgPDw+PgovQ29udGVudHMgNSAwIFIKL1BhcmVudCAyIDAgUgo+PgplbmRv"
            "YmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0tpZHMgWzQgMCBSXQovQ291bnQgMQo+PgplbmRvYmoKMSAwIG9iago8PAovVHlwZSAv"
            "Q2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL3RyYXBwZWQgKGZhbHNlKQovQ3JlYXRvciAoU2FtcGxlIFJl"
            "c3VtZSkKL1RpdGxlIChTYW1wbGUgUmVzdW1lKQovQ3JlYXRpb25EYXRlIChEOjIwMjMwNzAxMDAwMDAwWikKL01vZERhdGUgKEQ6MjAy"
            "MzA3MDEwMDAwMDBaKQovUHJvZHVjZXIgKFNhbXBsZSBQREYgUHJvZHVjZXIpCj4+CmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1"
            "NTM1IGYgCjAwMDAwMDAyODEgMDAwMDAgbiAKMDAwMDAwMDIzMiAwMDAwMCBuIAowMDAwMDAwMzMwIDAwMDAwIG4gCjAwMDAwMDAxMDkg"
            "MDAwMDAgbiAKMDAwMDAwMDAxNSAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDYKL1Jvb3QgMSAwIFIKL0luZm8gMyAwIFIKPj4Kc3Rh"
            "cnR4cmVmCjQ5MwolJUVPRgo="
        )
        
        # We'll store created resources here for cleanup and further testing
        self.created_resources = {
            "jobs": [],
            "candidates": [],
            "applications": [],
            "interviews": []
        }
    
    def test_01_create_job(self):
        """Test creating a job"""
        print("\n🧪 Testing job creation...")
        
        response = requests.post(f"{BACKEND_URL}/jobs", json=self.job_data)
        self.assertEqual(response.status_code, 200, f"Failed to create job: {response.text}")
        
        job = response.json()
        self.created_resources["jobs"].append(job["id"])
        
        # Verify job data
        self.assertEqual(job["title"], self.job_data["title"])
        self.assertEqual(job["location"], self.job_data["location"])
        self.assertEqual(job["sponsorship_eligible"], self.job_data["sponsorship_eligible"])
        self.assertEqual(job["relocation_support"], self.job_data["relocation_support"])
        self.assertEqual(job["housing_support"], self.job_data["housing_support"])
        
        print(f"✅ Job created successfully with ID: {job['id']}")
        return job
    
    def test_02_get_jobs(self):
        """Test retrieving jobs"""
        print("\n🧪 Testing job retrieval...")
        
        # Create a job first if none exists
        if not self.created_resources["jobs"]:
            job = self.test_01_create_job()
        
        # Get all jobs
        response = requests.get(f"{BACKEND_URL}/jobs")
        self.assertEqual(response.status_code, 200, f"Failed to get jobs: {response.text}")
        
        jobs = response.json()
        self.assertIsInstance(jobs, list)
        
        # Check if our test job is in the list
        job_ids = [job["id"] for job in jobs]
        self.assertTrue(any(job_id in job_ids for job_id in self.created_resources["jobs"]), 
                       "Created job not found in jobs list")
        
        print(f"✅ Retrieved {len(jobs)} jobs successfully")
        
        # Test filtering by status
        response = requests.get(f"{BACKEND_URL}/jobs?status=active")
        self.assertEqual(response.status_code, 200)
        active_jobs = response.json()
        self.assertIsInstance(active_jobs, list)
        print(f"✅ Retrieved {len(active_jobs)} active jobs successfully")
        
        return jobs
    
    def test_03_get_job_by_id(self):
        """Test retrieving a specific job by ID"""
        print("\n🧪 Testing job retrieval by ID...")
        
        # Create a job first if none exists
        if not self.created_resources["jobs"]:
            job = self.test_01_create_job()
        
        job_id = self.created_resources["jobs"][0]
        
        # Get the job by ID
        response = requests.get(f"{BACKEND_URL}/jobs/{job_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get job by ID: {response.text}")
        
        job = response.json()
        self.assertEqual(job["id"], job_id)
        
        print(f"✅ Retrieved job by ID successfully: {job['title']}")
        return job
    
    def test_04_update_job(self):
        """Test updating a job"""
        print("\n🧪 Testing job update...")
        
        # Create a job first if none exists
        if not self.created_resources["jobs"]:
            job = self.test_01_create_job()
        
        job_id = self.created_resources["jobs"][0]
        
        # Updated job data
        updated_job_data = {
            "title": f"{self.test_prefix}_Updated Childcare Teacher",
            "location": "Moranbah",
            "sponsorship_eligible": False,
            "relocation_support": True,
            "housing_support": True,
            "description": "Updated job description",
            "requirements": ["Diploma in Early Childhood Education", "3+ years experience"],
            "salary_range": "$70,000 - $80,000",
            "employment_type": "Full-time"
        }
        
        # Update the job
        response = requests.put(f"{BACKEND_URL}/jobs/{job_id}", json=updated_job_data)
        self.assertEqual(response.status_code, 200, f"Failed to update job: {response.text}")
        
        updated_job = response.json()
        self.assertEqual(updated_job["id"], job_id)
        self.assertEqual(updated_job["title"], updated_job_data["title"])
        self.assertEqual(updated_job["location"], updated_job_data["location"])
        self.assertEqual(updated_job["sponsorship_eligible"], updated_job_data["sponsorship_eligible"])
        
        print(f"✅ Job updated successfully: {updated_job['title']}")
        return updated_job
    
    def test_05_create_candidate(self):
        """Test creating a candidate"""
        print("\n🧪 Testing candidate creation...")
        
        response = requests.post(f"{BACKEND_URL}/candidates", json=self.candidate_data)
        self.assertEqual(response.status_code, 200, f"Failed to create candidate: {response.text}")
        
        candidate = response.json()
        self.created_resources["candidates"].append(candidate["id"])
        
        # Verify candidate data
        self.assertEqual(candidate["email"], self.candidate_data["email"])
        self.assertEqual(candidate["full_name"], self.candidate_data["full_name"])
        self.assertEqual(candidate["visa_status"], self.candidate_data["visa_status"])
        self.assertEqual(candidate["sponsorship_needed"], self.candidate_data["sponsorship_needed"])
        
        # Verify scoring algorithm
        self.assertIsInstance(candidate["score"], float)
        self.assertGreaterEqual(candidate["score"], 0.0)
        self.assertLessEqual(candidate["score"], 10.0)
        
        # Expected score based on the algorithm in server.py:
        # Experience (3 years) = 2.0
        # Visa (temporary) = 1.5
        # Rural experience (True) = 2.0
        # English (fluent) = 1.5
        # Total = 7.0
        self.assertAlmostEqual(candidate["score"], 7.0, delta=0.1)
        
        print(f"✅ Candidate created successfully with ID: {candidate['id']} and score: {candidate['score']}")
        return candidate
    
    def test_06_get_candidates(self):
        """Test retrieving candidates"""
        print("\n🧪 Testing candidate retrieval...")
        
        # Create a candidate first if none exists
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        # Get all candidates
        response = requests.get(f"{BACKEND_URL}/candidates")
        self.assertEqual(response.status_code, 200, f"Failed to get candidates: {response.text}")
        
        candidates = response.json()
        self.assertIsInstance(candidates, list)
        
        # Check if our test candidate is in the list
        candidate_ids = [candidate["id"] for candidate in candidates]
        self.assertTrue(any(candidate_id in candidate_ids for candidate_id in self.created_resources["candidates"]), 
                       "Created candidate not found in candidates list")
        
        print(f"✅ Retrieved {len(candidates)} candidates successfully")
        
        # Test filtering
        response = requests.get(f"{BACKEND_URL}/candidates?sponsorship_needed=true")
        self.assertEqual(response.status_code, 200)
        sponsorship_candidates = response.json()
        self.assertIsInstance(sponsorship_candidates, list)
        print(f"✅ Retrieved {len(sponsorship_candidates)} candidates needing sponsorship successfully")
        
        return candidates
    
    def test_07_get_candidate_by_id(self):
        """Test retrieving a specific candidate by ID"""
        print("\n🧪 Testing candidate retrieval by ID...")
        
        # Create a candidate first if none exists
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        candidate_id = self.created_resources["candidates"][0]
        
        # Get the candidate by ID
        response = requests.get(f"{BACKEND_URL}/candidates/{candidate_id}")
        self.assertEqual(response.status_code, 200, f"Failed to get candidate by ID: {response.text}")
        
        candidate = response.json()
        self.assertEqual(candidate["id"], candidate_id)
        
        print(f"✅ Retrieved candidate by ID successfully: {candidate['full_name']}")
        return candidate
    
    def test_08_update_candidate(self):
        """Test updating a candidate"""
        print("\n🧪 Testing candidate update...")
        
        # Create a candidate first if none exists
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        candidate_id = self.created_resources["candidates"][0]
        
        # Updated candidate data
        updated_candidate_data = {
            "email": f"{self.test_prefix}_updated@example.com",
            "phone": "0498765432",
            "full_name": f"{self.test_prefix} Updated Candidate",
            "location": "Sydney",
            "visa_status": "permanent",
            "visa_type": "PR",
            "sponsorship_needed": False,
            "childcare_cert": "Bachelor in Early Childhood Education",
            "experience_years": 5,
            "rural_experience": True,
            "relocation_willing": "yes",
            "housing_needed": False,
            "english_level": "native",
            "availability_start": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "salary_expectation": 80000,
            "notes": "Updated test candidate"
        }
        
        # Update the candidate
        response = requests.put(f"{BACKEND_URL}/candidates/{candidate_id}", json=updated_candidate_data)
        self.assertEqual(response.status_code, 200, f"Failed to update candidate: {response.text}")
        
        updated_candidate = response.json()
        self.assertEqual(updated_candidate["id"], candidate_id)
        self.assertEqual(updated_candidate["email"], updated_candidate_data["email"])
        self.assertEqual(updated_candidate["full_name"], updated_candidate_data["full_name"])
        self.assertEqual(updated_candidate["visa_status"], updated_candidate_data["visa_status"])
        self.assertEqual(updated_candidate["sponsorship_needed"], updated_candidate_data["sponsorship_needed"])
        
        # Verify updated score
        # Expected score based on the algorithm in server.py:
        # Experience (5 years) = 3.0
        # Visa (permanent, no sponsorship) = 3.0
        # Rural experience (True) = 2.0
        # English (native) = 2.0
        # Total = 10.0
        self.assertAlmostEqual(updated_candidate["score"], 10.0, delta=0.1)
        
        print(f"✅ Candidate updated successfully: {updated_candidate['full_name']} with new score: {updated_candidate['score']}")
        return updated_candidate
    
    def test_09_create_application(self):
        """Test creating an application"""
        print("\n🧪 Testing application creation...")
        
        # Create a job and candidate first if none exists
        if not self.created_resources["jobs"]:
            job = self.test_01_create_job()
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        job_id = self.created_resources["jobs"][0]
        candidate_id = self.created_resources["candidates"][0]
        
        # Application data
        application_data = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "cover_letter": "I am very interested in this position and believe my skills and experience make me a strong candidate."
        }
        
        # Create the application
        response = requests.post(f"{BACKEND_URL}/applications", json=application_data)
        self.assertEqual(response.status_code, 200, f"Failed to create application: {response.text}")
        
        application = response.json()
        self.created_resources["applications"].append(application["id"])
        
        # Verify application data
        self.assertEqual(application["job_id"], job_id)
        self.assertEqual(application["candidate_id"], candidate_id)
        self.assertEqual(application["status"], "new")
        self.assertEqual(application["cover_letter"], application_data["cover_letter"])
        
        print(f"✅ Application created successfully with ID: {application['id']}")
        return application
    
    def test_10_get_applications(self):
        """Test retrieving applications"""
        print("\n🧪 Testing application retrieval...")
        
        # Create an application first if none exists
        if not self.created_resources["applications"]:
            application = self.test_09_create_application()
        
        # Get all applications
        response = requests.get(f"{BACKEND_URL}/applications")
        self.assertEqual(response.status_code, 200, f"Failed to get applications: {response.text}")
        
        applications = response.json()
        self.assertIsInstance(applications, list)
        
        # Check if our test application is in the list
        application_ids = [app["id"] for app in applications]
        self.assertTrue(any(app_id in application_ids for app_id in self.created_resources["applications"]), 
                       "Created application not found in applications list")
        
        print(f"✅ Retrieved {len(applications)} applications successfully")
        
        # Test filtering
        job_id = self.created_resources["jobs"][0]
        response = requests.get(f"{BACKEND_URL}/applications?job_id={job_id}")
        self.assertEqual(response.status_code, 200)
        job_applications = response.json()
        self.assertIsInstance(job_applications, list)
        print(f"✅ Retrieved {len(job_applications)} applications for job {job_id} successfully")
        
        return applications
    
    def test_11_update_application(self):
        """Test updating an application status"""
        print("\n🧪 Testing application status update...")
        
        # Create an application first if none exists
        if not self.created_resources["applications"]:
            application = self.test_09_create_application()
        
        application_id = self.created_resources["applications"][0]
        
        # Update to screening status
        update_data = {
            "status": "screening",
            "notes": "Candidate looks promising, moving to screening phase."
        }
        
        # Update the application
        response = requests.put(f"{BACKEND_URL}/applications/{application_id}", json=update_data)
        self.assertEqual(response.status_code, 200, f"Failed to update application: {response.text}")
        
        updated_application = response.json()
        self.assertEqual(updated_application["id"], application_id)
        self.assertEqual(updated_application["status"], update_data["status"])
        
        print(f"✅ Application updated successfully to status: {updated_application['status']}")
        
        # Update to interview status
        update_data = {
            "status": "interview",
            "notes": "Screening complete, scheduling interview."
        }
        
        response = requests.put(f"{BACKEND_URL}/applications/{application_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        
        updated_application = response.json()
        self.assertEqual(updated_application["status"], update_data["status"])
        
        print(f"✅ Application updated successfully to status: {updated_application['status']}")
        
        return updated_application
    
    def test_12_bulk_update_applications(self):
        """Test bulk updating applications"""
        print("\n🧪 Testing bulk application update...")
        
        # Create multiple applications if needed
        if len(self.created_resources["applications"]) < 2:
            # Create a second job if needed
            if len(self.created_resources["jobs"]) < 2:
                second_job_data = dict(self.job_data)
                second_job_data["title"] = f"{self.test_prefix}_Second Job"
                second_job_data["location"] = "Charters Towers"
                
                response = requests.post(f"{BACKEND_URL}/jobs", json=second_job_data)
                self.assertEqual(response.status_code, 200)
                second_job = response.json()
                self.created_resources["jobs"].append(second_job["id"])
            
            # Create a second application
            application_data = {
                "job_id": self.created_resources["jobs"][1] if len(self.created_resources["jobs"]) > 1 else self.created_resources["jobs"][0],
                "candidate_id": self.created_resources["candidates"][0],
                "cover_letter": "This is a second application for testing bulk updates."
            }
            
            response = requests.post(f"{BACKEND_URL}/applications", json=application_data)
            self.assertEqual(response.status_code, 200)
            second_application = response.json()
            self.created_resources["applications"].append(second_application["id"])
        
        # Bulk update data
        bulk_update_data = {
            "application_ids": self.created_resources["applications"],
            "status": "offer",
            "notes": "Bulk update to offer status for testing."
        }
        
        # Perform bulk update
        response = requests.post(f"{BACKEND_URL}/applications/bulk-update", json=bulk_update_data)
        self.assertEqual(response.status_code, 200, f"Failed to bulk update applications: {response.text}")
        
        result = response.json()
        self.assertIn("updated_count", result)
        self.assertEqual(result["updated_count"], len(self.created_resources["applications"]))
        
        # Verify updates
        for app_id in self.created_resources["applications"]:
            response = requests.get(f"{BACKEND_URL}/applications?status=offer")
            self.assertEqual(response.status_code, 200)
            
            applications = response.json()
            app_ids = [app["id"] for app in applications]
            self.assertIn(app_id, app_ids, f"Application {app_id} not found in offer status")
        
        print(f"✅ Bulk updated {result['updated_count']} applications to 'offer' status successfully")
        return result
    
    def test_13_dashboard_stats(self):
        """Test dashboard statistics API"""
        print("\n🧪 Testing dashboard statistics API...")
        
        response = requests.get(f"{BACKEND_URL}/dashboard/stats")
        self.assertEqual(response.status_code, 200, f"Failed to get dashboard stats: {response.text}")
        
        stats = response.json()
        
        # Verify stats structure
        self.assertIn("total_jobs", stats)
        self.assertIn("total_candidates", stats)
        self.assertIn("total_applications", stats)
        self.assertIn("applications_by_status", stats)
        self.assertIn("visa_sponsorship", stats)
        self.assertIn("jobs_by_location", stats)
        
        # Verify stats are numbers
        self.assertIsInstance(stats["total_jobs"], int)
        self.assertIsInstance(stats["total_candidates"], int)
        self.assertIsInstance(stats["total_applications"], int)
        
        print(f"✅ Dashboard stats retrieved successfully:")
        print(f"   - Total Jobs: {stats['total_jobs']}")
        print(f"   - Total Candidates: {stats['total_candidates']}")
        print(f"   - Total Applications: {stats['total_applications']}")
        print(f"   - Applications by Status: {stats['applications_by_status']}")
        print(f"   - Visa Sponsorship: {stats['visa_sponsorship']}")
        print(f"   - Jobs by Location: {stats['jobs_by_location']}")
        
        return stats

    def test_14_upload_resume(self):
        """Test resume upload and parsing"""
        print("\n🧪 Testing resume upload and parsing...")
        
        # Create a candidate first if none exists
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        candidate_id = self.created_resources["candidates"][0]
        
        # Create a temporary PDF file with sample content
        temp_pdf_path = f"/tmp/{self.test_prefix}_resume.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(self.sample_pdf_content)
        
        # Upload the resume
        with open(temp_pdf_path, "rb") as f:
            files = {"file": (f"{self.test_prefix}_resume.pdf", f, "application/pdf")}
            response = requests.post(
                f"{BACKEND_URL}/candidates/{candidate_id}/upload-resume",
                files=files
            )
        
        # Clean up the temporary file
        os.remove(temp_pdf_path)
        
        # Verify the response
        self.assertEqual(response.status_code, 200, f"Failed to upload resume: {response.text}")
        
        result = response.json()
        self.assertIn("message", result)
        self.assertIn("parsed_skills", result)
        self.assertIn("new_score", result)
        
        print(f"✅ Resume uploaded successfully")
        print(f"   - Parsed skills: {result.get('parsed_skills', [])}")
        print(f"   - Education: {result.get('education')}")
        print(f"   - New score: {result.get('new_score')}")
        
        # Verify candidate was updated with resume data
        response = requests.get(f"{BACKEND_URL}/candidates/{candidate_id}")
        self.assertEqual(response.status_code, 200)
        
        updated_candidate = response.json()
        self.assertIsNotNone(updated_candidate.get("resume_url"))
        
        return result
    
    def test_15_visa_evaluation(self):
        """Test visa sponsorship evaluation"""
        print("\n🧪 Testing visa sponsorship evaluation...")
        
        # Create a candidate first if none exists
        if not self.created_resources["candidates"]:
            candidate = self.test_05_create_candidate()
        
        candidate_id = self.created_resources["candidates"][0]
        
        # Get visa evaluation
        response = requests.get(f"{BACKEND_URL}/candidates/{candidate_id}/visa-evaluation")
        self.assertEqual(response.status_code, 200, f"Failed to get visa evaluation: {response.text}")
        
        evaluation = response.json()
        
        # Verify evaluation structure
        self.assertIn("eligible", evaluation)
        self.assertIn("reason", evaluation)
        self.assertIn("visa_pathway", evaluation)
        self.assertIn("requirements", evaluation)
        self.assertIn("score", evaluation)
        
        # Verify score is a number
        self.assertIsInstance(evaluation["score"], (int, float))
        
        print(f"✅ Visa evaluation retrieved successfully:")
        print(f"   - Eligible: {evaluation['eligible']}")
        print(f"   - Reason: {evaluation['reason']}")
        print(f"   - Visa pathway: {evaluation['visa_pathway']}")
        print(f"   - Requirements: {evaluation['requirements']}")
        print(f"   - Score: {evaluation['score']}")
        
        return evaluation
    
    def test_16_create_interview(self):
        """Test creating an interview"""
        print("\n🧪 Testing interview creation...")
        
        # Create an application first if none exists
        if not self.created_resources["applications"]:
            application = self.test_09_create_application()
        
        application_id = self.created_resources["applications"][0]
        
        # Create interview data
        interview_data = dict(self.interview_data)
        interview_data["application_id"] = application_id
        
        # Create the interview
        response = requests.post(f"{BACKEND_URL}/interviews", json=interview_data)
        self.assertEqual(response.status_code, 200, f"Failed to create interview: {response.text}")
        
        interview = response.json()
        self.created_resources["interviews"].append(interview["id"])
        
        # Verify interview data
        self.assertEqual(interview["application_id"], application_id)
        self.assertEqual(interview["interviewer_name"], interview_data["interviewer_name"])
        self.assertEqual(interview["interviewer_email"], interview_data["interviewer_email"])
        self.assertEqual(interview["status"], "scheduled")
        
        # Verify meeting link was generated for video interview
        if interview_data["interview_type"] == "video":
            self.assertIsNotNone(interview["meeting_link"])
            self.assertTrue(interview["meeting_link"].startswith("https://"))
        
        print(f"✅ Interview created successfully with ID: {interview['id']}")
        print(f"   - Status: {interview['status']}")
        print(f"   - Type: {interview['interview_type']}")
        print(f"   - Meeting link: {interview.get('meeting_link')}")
        
        return interview
    
    def test_17_get_interviews(self):
        """Test retrieving interviews"""
        print("\n🧪 Testing interview retrieval...")
        
        # Create an interview first if none exists
        if not self.created_resources["interviews"]:
            interview = self.test_16_create_interview()
        
        # Get all interviews
        response = requests.get(f"{BACKEND_URL}/interviews")
        self.assertEqual(response.status_code, 200, f"Failed to get interviews: {response.text}")
        
        interviews = response.json()
        self.assertIsInstance(interviews, list)
        
        # Check if our test interview is in the list
        interview_ids = [interview["id"] for interview in interviews]
        self.assertTrue(any(interview_id in interview_ids for interview_id in self.created_resources["interviews"]), 
                       "Created interview not found in interviews list")
        
        print(f"✅ Retrieved {len(interviews)} interviews successfully")
        
        # Test filtering by status
        response = requests.get(f"{BACKEND_URL}/interviews?status=scheduled")
        self.assertEqual(response.status_code, 200)
        scheduled_interviews = response.json()
        self.assertIsInstance(scheduled_interviews, list)
        print(f"✅ Retrieved {len(scheduled_interviews)} scheduled interviews successfully")
        
        # Test filtering by candidate
        if self.created_resources["candidates"]:
            candidate_id = self.created_resources["candidates"][0]
            response = requests.get(f"{BACKEND_URL}/interviews?candidate_id={candidate_id}")
            self.assertEqual(response.status_code, 200)
            candidate_interviews = response.json()
            self.assertIsInstance(candidate_interviews, list)
            print(f"✅ Retrieved {len(candidate_interviews)} interviews for candidate {candidate_id} successfully")
        
        return interviews
    
    def test_18_update_interview(self):
        """Test updating an interview"""
        print("\n🧪 Testing interview update...")
        
        # Create an interview first if none exists
        if not self.created_resources["interviews"]:
            interview = self.test_16_create_interview()
        
        interview_id = self.created_resources["interviews"][0]
        
        # Update to completed status with feedback
        update_data = {
            "status": "completed",
            "feedback": "Candidate performed well in the interview. Strong communication skills and relevant experience.",
            "technical_score": 8.5,
            "cultural_fit_score": 9.0,
            "visa_suitability_score": 7.5,
            "overall_recommendation": "hire"
        }
        
        # Update the interview
        response = requests.put(f"{BACKEND_URL}/interviews/{interview_id}", json=update_data)
        self.assertEqual(response.status_code, 200, f"Failed to update interview: {response.text}")
        
        updated_interview = response.json()
        self.assertEqual(updated_interview["id"], interview_id)
        self.assertEqual(updated_interview["status"], update_data["status"])
        self.assertEqual(updated_interview["feedback"], update_data["feedback"])
        self.assertEqual(updated_interview["technical_score"], update_data["technical_score"])
        self.assertEqual(updated_interview["cultural_fit_score"], update_data["cultural_fit_score"])
        self.assertEqual(updated_interview["visa_suitability_score"], update_data["visa_suitability_score"])
        self.assertEqual(updated_interview["overall_recommendation"], update_data["overall_recommendation"])
        
        print(f"✅ Interview updated successfully to status: {updated_interview['status']}")
        print(f"   - Technical score: {updated_interview['technical_score']}")
        print(f"   - Cultural fit score: {updated_interview['cultural_fit_score']}")
        print(f"   - Visa suitability score: {updated_interview['visa_suitability_score']}")
        print(f"   - Overall recommendation: {updated_interview['overall_recommendation']}")
        
        # Update to rescheduled status
        update_data = {
            "status": "rescheduled",
            "scheduled_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "notes": "Rescheduled at candidate's request."
        }
        
        response = requests.put(f"{BACKEND_URL}/interviews/{interview_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        
        updated_interview = response.json()
        self.assertEqual(updated_interview["status"], update_data["status"])
        self.assertEqual(updated_interview["notes"], update_data["notes"])
        
        print(f"✅ Interview rescheduled successfully")
        
        return updated_interview
    
    def test_19_enhanced_candidate_scoring(self):
        """Test enhanced candidate scoring algorithm"""
        print("\n🧪 Testing enhanced candidate scoring algorithm...")
        
        # Create candidates with different profiles to test scoring
        # Candidate 1: High experience, permanent resident, rural experience, native English
        candidate1_data = {
            "email": f"{self.test_prefix}_high_score@example.com",
            "phone": "0412345678",
            "full_name": f"{self.test_prefix} High Score Candidate",
            "location": "Brisbane",
            "visa_status": "permanent",
            "visa_type": "PR",
            "sponsorship_needed": False,
            "childcare_cert": "Bachelor in Early Childhood Education",
            "experience_years": 5,
            "rural_experience": True,
            "relocation_willing": "yes",
            "housing_needed": False,
            "english_level": "native",
            "availability_start": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "salary_expectation": 80000,
            "notes": "High score test candidate"
        }
        
        # Candidate 2: Low experience, needs sponsorship, no rural experience, basic English
        candidate2_data = {
            "email": f"{self.test_prefix}_low_score@example.com",
            "phone": "0412345679",
            "full_name": f"{self.test_prefix} Low Score Candidate",
            "location": "Sydney",
            "visa_status": "needs_sponsorship",
            "visa_type": "None",
            "sponsorship_needed": True,
            "childcare_cert": None,
            "experience_years": 0,
            "rural_experience": False,
            "relocation_willing": "no",
            "housing_needed": True,
            "english_level": "basic",
            "availability_start": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "salary_expectation": 60000,
            "notes": "Low score test candidate"
        }
        
        # Create the candidates
        response1 = requests.post(f"{BACKEND_URL}/candidates", json=candidate1_data)
        self.assertEqual(response1.status_code, 200)
        candidate1 = response1.json()
        self.created_resources["candidates"].append(candidate1["id"])
        
        response2 = requests.post(f"{BACKEND_URL}/candidates", json=candidate2_data)
        self.assertEqual(response2.status_code, 200)
        candidate2 = response2.json()
        self.created_resources["candidates"].append(candidate2["id"])
        
        # Verify scoring
        print(f"✅ High score candidate created with score: {candidate1['score']}")
        print(f"✅ Low score candidate created with score: {candidate2['score']}")
        
        # Verify high score candidate has higher score than low score candidate
        self.assertGreater(candidate1["score"], candidate2["score"])
        
        # Verify high score candidate has high score (expected around 9-10)
        self.assertGreaterEqual(candidate1["score"], 9.0)
        
        # Verify low score candidate has low score (expected around 1-2)
        self.assertLessEqual(candidate2["score"], 2.0)
        
        # Test score update when adding skills
        # Upload resume for high score candidate to add skills
        if hasattr(self, 'sample_pdf_content'):
            temp_pdf_path = f"/tmp/{self.test_prefix}_resume.pdf"
            with open(temp_pdf_path, "wb") as f:
                f.write(self.sample_pdf_content)
            
            with open(temp_pdf_path, "rb") as f:
                files = {"file": (f"{self.test_prefix}_resume.pdf", f, "application/pdf")}
                response = requests.post(
                    f"{BACKEND_URL}/candidates/{candidate1['id']}/upload-resume",
                    files=files
                )
            
            os.remove(temp_pdf_path)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Resume uploaded for high score candidate, new score: {result.get('new_score')}")
                
                # Verify score increased or stayed at max
                self.assertGreaterEqual(result.get('new_score'), candidate1['score'])
        
        return {
            "high_score_candidate": candidate1,
            "low_score_candidate": candidate2
        }


if __name__ == "__main__":
    # Run the tests
    print("🚀 Starting GRO Early Learning ATS Backend Tests")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    # Create a test suite with ordered tests
    test_suite = unittest.TestSuite()
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_01_create_job'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_02_get_jobs'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_03_get_job_by_id'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_04_update_job'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_05_create_candidate'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_06_get_candidates'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_07_get_candidate_by_id'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_08_update_candidate'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_09_create_application'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_10_get_applications'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_11_update_application'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_12_bulk_update_applications'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_13_dashboard_stats'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_14_upload_resume'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_15_visa_evaluation'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_16_create_interview'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_17_get_interviews'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_18_update_interview'))
    test_suite.addTest(GROEarlyLearningATSBackendTest('test_19_enhanced_candidate_scoring'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
