from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum
import sendgrid
from sendgrid.helpers.mail import Mail
import json
import PyPDF2
import io
import base64
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# SendGrid setup
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class LocationEnum(str, Enum):
    mount_isa = "Mount Isa"
    moranbah = "Moranbah"
    charters_towers = "Charters Towers"

class VisaStatusEnum(str, Enum):
    citizen = "citizen"
    permanent = "permanent"  
    temporary = "temporary"
    needs_sponsorship = "needs_sponsorship"

class ApplicationStatusEnum(str, Enum):
    new = "new"
    screening = "screening"
    interview = "interview" 
    offer = "offer"
    hired = "hired"
    rejected = "rejected"

class RelocationWillingnessEnum(str, Enum):
    yes = "yes"
    no = "no"
    maybe = "maybe"

class EnglishLevelEnum(str, Enum):
    native = "native"
    fluent = "fluent"
    good = "good"
    basic = "basic"

# Models
class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    location: LocationEnum
    sponsorship_eligible: bool = False
    relocation_support: bool = False
    housing_support: bool = False
    description: str
    requirements: List[str] = []
    salary_range: Optional[str] = None
    employment_type: str = "Full-time"
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class JobCreate(BaseModel):
    title: str
    location: LocationEnum
    sponsorship_eligible: bool = False
    relocation_support: bool = False
    housing_support: bool = False
    description: str
    requirements: List[str] = []
    salary_range: Optional[str] = None
    employment_type: str = "Full-time"

class Candidate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    phone: str
    full_name: str
    location: str
    visa_status: VisaStatusEnum
    visa_type: Optional[str] = None
    sponsorship_needed: bool
    childcare_cert: Optional[str] = None
    experience_years: int = 0
    rural_experience: bool = False
    relocation_willing: RelocationWillingnessEnum
    housing_needed: bool = False
    english_level: EnglishLevelEnum
    availability_start: Optional[datetime] = None
    salary_expectation: Optional[int] = None
    source: str = "direct"
    status: ApplicationStatusEnum = ApplicationStatusEnum.new
    score: float = 0.0
    notes: str = ""
    resume_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CandidateCreate(BaseModel):
    email: str
    phone: str
    full_name: str
    location: str
    visa_status: VisaStatusEnum
    visa_type: Optional[str] = None
    sponsorship_needed: bool
    childcare_cert: Optional[str] = None
    experience_years: int = 0
    rural_experience: bool = False
    relocation_willing: RelocationWillingnessEnum
    housing_needed: bool = False
    english_level: EnglishLevelEnum
    availability_start: Optional[datetime] = None
    salary_expectation: Optional[int] = None
    notes: str = ""

class Application(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    candidate_id: str
    status: ApplicationStatusEnum = ApplicationStatusEnum.new
    cover_letter: Optional[str] = None
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ApplicationCreate(BaseModel):
    job_id: str
    candidate_id: str
    cover_letter: Optional[str] = None

class EmailTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    content: str
    type: str  # application_received, interview_invitation, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ApplicationUpdate(BaseModel):
    status: ApplicationStatusEnum
    notes: Optional[str] = None

# Email service functions
async def send_email(to_email: str, subject: str, content: str):
    try:
        message = Mail(
            from_email='noreply@grolearning.com',
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        response = sg.send(message)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def calculate_candidate_score(candidate: Candidate, job: Job = None) -> float:
    """Simple rules-based scoring for candidates"""
    score = 0.0
    
    # Experience score (0-3 points)
    if candidate.experience_years >= 5:
        score += 3.0
    elif candidate.experience_years >= 2:
        score += 2.0
    elif candidate.experience_years >= 1:
        score += 1.0
    
    # Visa eligibility (0-3 points)
    if not candidate.sponsorship_needed:
        score += 3.0
    elif candidate.visa_status == VisaStatusEnum.temporary:
        score += 1.5
    
    # Rural experience bonus (0-2 points)
    if candidate.rural_experience:
        score += 2.0
    
    # English proficiency (0-2 points)
    if candidate.english_level == EnglishLevelEnum.native:
        score += 2.0
    elif candidate.english_level == EnglishLevelEnum.fluent:
        score += 1.5
    elif candidate.english_level == EnglishLevelEnum.good:
        score += 1.0
    
    return min(score, 10.0)  # Cap at 10

# API Routes

# Jobs
@api_router.post("/jobs", response_model=Job)
async def create_job(job_data: JobCreate):
    job_dict = job_data.dict()
    job = Job(**job_dict)
    result = await db.jobs.insert_one(job.dict())
    return job

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(status: Optional[str] = Query(None)):
    query = {}
    if status:
        query["status"] = status
    jobs = await db.jobs.find(query).sort("created_at", -1).to_list(1000)
    return [Job(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return Job(**job)

@api_router.put("/jobs/{job_id}", response_model=Job)
async def update_job(job_id: str, job_data: JobCreate):
    job_dict = job_data.dict()
    job_dict["updated_at"] = datetime.utcnow()
    
    result = await db.jobs.update_one(
        {"id": job_id},
        {"$set": job_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    
    updated_job = await db.jobs.find_one({"id": job_id})
    return Job(**updated_job)

# Candidates
@api_router.post("/candidates", response_model=Candidate)
async def create_candidate(candidate_data: CandidateCreate):
    candidate_dict = candidate_data.dict()
    candidate = Candidate(**candidate_dict)
    candidate.score = calculate_candidate_score(candidate)
    
    result = await db.candidates.insert_one(candidate.dict())
    
    # Send welcome email
    await send_email(
        candidate.email,
        "Welcome to GRO Early Learning - Application Received",
        f"<p>Dear {candidate.full_name},</p><p>Thank you for your interest in GRO Early Learning positions. We have received your application and will review it shortly.</p><p>Best regards,<br>GRO Early Learning Recruitment Team</p>"
    )
    
    return candidate

@api_router.get("/candidates", response_model=List[Candidate])
async def get_candidates(
    location: Optional[str] = Query(None),
    visa_status: Optional[VisaStatusEnum] = Query(None),
    sponsorship_needed: Optional[bool] = Query(None),
    status: Optional[ApplicationStatusEnum] = Query(None)
):
    query = {}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if visa_status:
        query["visa_status"] = visa_status
    if sponsorship_needed is not None:
        query["sponsorship_needed"] = sponsorship_needed
    if status:
        query["status"] = status
    
    candidates = await db.candidates.find(query).sort("score", -1).to_list(1000)
    return [Candidate(**candidate) for candidate in candidates]

@api_router.get("/candidates/{candidate_id}", response_model=Candidate)
async def get_candidate(candidate_id: str):
    candidate = await db.candidates.find_one({"id": candidate_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return Candidate(**candidate)

@api_router.put("/candidates/{candidate_id}", response_model=Candidate)
async def update_candidate(candidate_id: str, candidate_data: CandidateCreate):
    candidate_dict = candidate_data.dict()
    candidate_dict["updated_at"] = datetime.utcnow()
    
    # Recalculate score
    temp_candidate = Candidate(**{**candidate_dict, "id": candidate_id})
    candidate_dict["score"] = calculate_candidate_score(temp_candidate)
    
    result = await db.candidates.update_one(
        {"id": candidate_id},
        {"$set": candidate_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    updated_candidate = await db.candidates.find_one({"id": candidate_id})
    return Candidate(**updated_candidate)

# Applications
@api_router.post("/applications", response_model=Application)
async def create_application(app_data: ApplicationCreate):
    # Check if job and candidate exist
    job = await db.jobs.find_one({"id": app_data.job_id})
    candidate = await db.candidates.find_one({"id": app_data.candidate_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    app_dict = app_data.dict()
    application = Application(**app_dict)
    
    result = await db.applications.insert_one(application.dict())
    
    # Send confirmation email
    await send_email(
        candidate["email"],
        f"Application Confirmation - {job['title']}",
        f"<p>Dear {candidate['full_name']},</p><p>Your application for {job['title']} in {job['location']} has been submitted successfully.</p><p>We will review your application and get back to you soon.</p><p>Best regards,<br>GRO Early Learning Recruitment Team</p>"
    )
    
    return application

@api_router.get("/applications", response_model=List[Application])
async def get_applications(
    job_id: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    status: Optional[ApplicationStatusEnum] = Query(None)
):
    query = {}
    if job_id:
        query["job_id"] = job_id
    if candidate_id:
        query["candidate_id"] = candidate_id
    if status:
        query["status"] = status
    
    applications = await db.applications.find(query).sort("applied_at", -1).to_list(1000)
    return [Application(**app) for app in applications]

@api_router.put("/applications/{application_id}", response_model=Application)
async def update_application(application_id: str, app_update: ApplicationUpdate):
    app_dict = app_update.dict(exclude_unset=True)
    app_dict["updated_at"] = datetime.utcnow()
    
    result = await db.applications.update_one(
        {"id": application_id},
        {"$set": app_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Send status update email
    application = await db.applications.find_one({"id": application_id})
    candidate = await db.candidates.find_one({"id": application["candidate_id"]})
    job = await db.jobs.find_one({"id": application["job_id"]})
    
    status_messages = {
        "screening": "Your application is being reviewed by our team.",
        "interview": "Congratulations! We would like to schedule an interview with you.",
        "offer": "Great news! We would like to extend an offer to you.",
        "hired": "Welcome to the GRO Early Learning team!",
        "rejected": "Thank you for your interest. Unfortunately, we have decided to proceed with other candidates."
    }
    
    if app_update.status in status_messages:
        await send_email(
            candidate["email"],
            f"Application Update - {job['title']}",
            f"<p>Dear {candidate['full_name']},</p><p>{status_messages[app_update.status]}</p><p>Best regards,<br>GRO Early Learning Recruitment Team</p>"
        )
    
    updated_application = await db.applications.find_one({"id": application_id})
    return Application(**updated_application)

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get counts
    total_jobs = await db.jobs.count_documents({"status": "active"})
    total_candidates = await db.candidates.count_documents({})
    total_applications = await db.applications.count_documents({})
    
    # Applications by status
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.applications.aggregate(pipeline).to_list(1000)
    
    # Visa sponsorship pipeline
    visa_pipeline = [
        {"$group": {"_id": "$sponsorship_needed", "count": {"$sum": 1}}}
    ]
    visa_counts = await db.candidates.aggregate(visa_pipeline).to_list(1000)
    
    # Jobs by location
    location_pipeline = [
        {"$group": {"_id": "$location", "count": {"$sum": 1}}}
    ]
    location_counts = await db.jobs.aggregate(location_pipeline).to_list(1000)
    
    return {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "total_applications": total_applications,
        "applications_by_status": {item["_id"]: item["count"] for item in status_counts},
        "visa_sponsorship": {str(item["_id"]): item["count"] for item in visa_counts},
        "jobs_by_location": {item["_id"]: item["count"] for item in location_counts}
    }

# Bulk actions
@api_router.post("/applications/bulk-update")
async def bulk_update_applications(
    application_ids: List[str],
    status: ApplicationStatusEnum,
    notes: Optional[str] = None
):
    update_data = {"status": status, "updated_at": datetime.utcnow()}
    if notes:
        update_data["notes"] = notes
    
    result = await db.applications.update_many(
        {"id": {"$in": application_ids}},
        {"$set": update_data}
    )
    
    return {"updated_count": result.modified_count}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
