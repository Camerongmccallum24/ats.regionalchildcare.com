#!/usr/bin/env python3
import requests
import json
import uuid
import time
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
        
        # We'll store created resources here for cleanup and further testing
        self.created_resources = {
            "jobs": [],
            "candidates": [],
            "applications": []
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
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
