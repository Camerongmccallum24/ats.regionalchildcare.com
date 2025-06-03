from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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
from jinja2 import Template
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get("SECRET_KEY", "gro-early-learning-secret-key-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

class InterviewStatusEnum(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    rescheduled = "rescheduled"

class InterviewTypeEnum(str, Enum):
    phone = "phone"
    video = "video"
    in_person = "in_person"

class UserRoleEnum(str, Enum):
    admin = "admin"
    recruiter = "recruiter"
    manager = "manager"
    viewer = "viewer"

class TemplateTypeEnum(str, Enum):
    application_received = "application_received"
    interview_invitation = "interview_invitation"
    status_update = "status_update"
    offer_letter = "offer_letter"
    rejection_letter = "rejection_letter"
    welcome_email = "welcome_email"
    reminder = "reminder"

class DocumentTypeEnum(str, Enum):
    resume = "resume"
    cover_letter = "cover_letter"
    certificate = "certificate"
    identification = "identification"
    visa_document = "visa_document"
    reference = "reference"
    other = "other"

class AuditActionEnum(str, Enum):
    create = "create"
    update = "update"
    delete = "delete"
    view = "view"
    download = "download"
    send_email = "send_email"
    schedule_interview = "schedule_interview"

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
    resume_text: Optional[str] = None  # Parsed resume content
    skills: List[str] = []  # Extracted skills
    education: Optional[str] = None  # Extracted education
    work_history: Optional[str] = None  # Extracted work history
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

class Interview(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    application_id: str
    candidate_id: str
    job_id: str
    interviewer_name: str
    interviewer_email: str
    scheduled_date: datetime
    duration_minutes: int = 60
    interview_type: InterviewTypeEnum = InterviewTypeEnum.video
    meeting_link: Optional[str] = None
    location: Optional[str] = None  # For in-person interviews
    status: InterviewStatusEnum = InterviewStatusEnum.scheduled
    notes: Optional[str] = None
    feedback: Optional[str] = None
    technical_score: Optional[float] = None  # 1-10 scale
    cultural_fit_score: Optional[float] = None  # 1-10 scale
    visa_suitability_score: Optional[float] = None  # 1-10 scale
    overall_recommendation: Optional[str] = None  # hire, reject, second_interview
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class InterviewCreate(BaseModel):
    application_id: str
    interviewer_name: str
    interviewer_email: str
    scheduled_date: datetime
    duration_minutes: int = 60
    interview_type: InterviewTypeEnum = InterviewTypeEnum.video
    meeting_link: Optional[str] = None
    location: Optional[str] = None

class InterviewUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    status: Optional[InterviewStatusEnum] = None
    notes: Optional[str] = None
    feedback: Optional[str] = None
    technical_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    visa_suitability_score: Optional[float] = None
    overall_recommendation: Optional[str] = None

# Advanced Phase 3 Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: UserRoleEnum
    is_active: bool = True
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    email: str
    full_name: str
    role: UserRoleEnum
    password: str

class EmailTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    content: str
    template_type: TemplateTypeEnum
    merge_fields: List[str] = []  # Available merge fields like {{candidate_name}}, {{job_title}}
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    content: str
    template_type: TemplateTypeEnum
    merge_fields: List[str] = []

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    document_type: DocumentTypeEnum
    file_url: str  # Base64 encoded or URL
    file_size: Optional[int] = None
    mime_type: str
    uploaded_by: str
    related_entity_id: str  # candidate_id, job_id, etc.
    related_entity_type: str  # "candidate", "job", etc.
    is_confidential: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    action: AuditActionEnum
    entity_type: str  # "candidate", "job", "application", etc.
    entity_id: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str  # "eeo", "visa_sponsorship", "hiring_audit"
    start_date: datetime
    end_date: datetime
    data: Dict[str, Any]
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class AdvancedSearchFilter(BaseModel):
    # Location filters
    locations: Optional[List[str]] = None
    
    # Visa and sponsorship filters
    visa_status: Optional[List[VisaStatusEnum]] = None
    sponsorship_needed: Optional[bool] = None
    
    # Experience filters
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    rural_experience: Optional[bool] = None
    
    # Qualification filters
    certifications: Optional[List[str]] = None
    education_level: Optional[List[str]] = None
    
    # Score filters
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    
    # Availability filters
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None
    
    # Relocation filters
    relocation_willing: Optional[List[RelocationWillingnessEnum]] = None
    
    # Skills filters
    required_skills: Optional[List[str]] = None
    
    # Status filters
    application_status: Optional[List[ApplicationStatusEnum]] = None
    
    # Date filters
    applied_after: Optional[datetime] = None
    applied_before: Optional[datetime] = None
    
    # Text search
    search_query: Optional[str] = None  # Search in name, email, notes, resume text

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

# Resume parsing functions
def parse_pdf_resume(file_content: bytes) -> dict:
    """Extract text and basic information from PDF resume"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        # Basic information extraction
        info = {
            "text": text,
            "skills": extract_skills_from_text(text),
            "education": extract_education_from_text(text),
            "work_history": extract_work_history_from_text(text)
        }
        return info
    except Exception as e:
        logging.error(f"Failed to parse PDF: {e}")
        return {"text": "", "skills": [], "education": None, "work_history": None}

def extract_skills_from_text(text: str) -> List[str]:
    """Extract childcare-related skills from resume text"""
    childcare_skills = [
        "early childhood education", "child development", "curriculum planning",
        "behavior management", "first aid", "cpr", "working with children check",
        "montessori", "steiner", "reggio emilia", "play-based learning",
        "observation", "documentation", "family engagement", "multicultural",
        "special needs", "inclusive practices", "outdoor play", "nutrition",
        "safety procedures", "team collaboration", "communication"
    ]
    
    found_skills = []
    text_lower = text.lower()
    for skill in childcare_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return found_skills

def extract_education_from_text(text: str) -> Optional[str]:
    """Extract education information from resume text"""
    education_patterns = [
        r"certificate.*early childhood",
        r"diploma.*early childhood",
        r"bachelor.*education",
        r"master.*education",
        r"cert.*iii.*early childhood",
        r"cert.*iv.*early childhood"
    ]
    
    for pattern in education_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None

def extract_work_history_from_text(text: str) -> Optional[str]:
    """Extract basic work history from resume text"""
    # Look for common work history indicators
    work_patterns = [
        r"(educator|teacher|assistant|coordinator|director|supervisor).*(\d{4}|\d{1,2}\s+years?)",
        r"(\d{4})\s*-\s*(\d{4}|present)",
        r"(\d{1,2})\s+years?\s+experience"
    ]
    
    work_info = []
    for pattern in work_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        work_info.extend(matches)
    
    return str(work_info) if work_info else None

def enhanced_calculate_candidate_score(candidate: Candidate, job: Job = None) -> float:
    """Enhanced rules-based scoring for candidates with more sophisticated logic"""
    score = 0.0
    
    # Experience score (0-3 points) - weighted higher
    if candidate.experience_years >= 5:
        score += 3.0
    elif candidate.experience_years >= 3:
        score += 2.5
    elif candidate.experience_years >= 1:
        score += 1.5
    elif candidate.experience_years > 0:
        score += 0.5
    
    # Visa eligibility (0-3 points)
    if not candidate.sponsorship_needed:
        score += 3.0
    elif candidate.visa_status == VisaStatusEnum.temporary:
        score += 1.5
    elif candidate.visa_status == VisaStatusEnum.needs_sponsorship:
        score += 0.5  # Still possible but requires work
    
    # Rural experience bonus (0-2 points)
    if candidate.rural_experience:
        score += 2.0
    
    # English proficiency (0-1.5 points)
    if candidate.english_level == EnglishLevelEnum.native:
        score += 1.5
    elif candidate.english_level == EnglishLevelEnum.fluent:
        score += 1.2
    elif candidate.english_level == EnglishLevelEnum.good:
        score += 0.8
    else:
        score += 0.3
    
    # Qualifications bonus (0-1 point)
    if candidate.childcare_cert:
        if "certificate iii" in candidate.childcare_cert.lower():
            score += 1.0
        elif "diploma" in candidate.childcare_cert.lower():
            score += 1.2
        elif "bachelor" in candidate.childcare_cert.lower():
            score += 1.5
    
    # Skills bonus (0-0.5 points)
    if candidate.skills:
        score += min(len(candidate.skills) * 0.1, 0.5)
    
    # Availability and willingness (0-0.5 points)
    if candidate.relocation_willing == RelocationWillingnessEnum.yes:
        score += 0.5
    elif candidate.relocation_willing == RelocationWillingnessEnum.maybe:
        score += 0.2
    
    return min(score, 10.0)  # Cap at 10

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

# Visa pre-qualification function
def evaluate_visa_sponsorship_eligibility(candidate: Candidate) -> dict:
    """Enhanced visa sponsorship pre-qualification"""
    result = {
        "eligible": False,
        "reason": "",
        "visa_pathway": None,
        "requirements": [],
        "score": 0
    }
    
    # Check basic eligibility
    if not candidate.sponsorship_needed:
        result["eligible"] = True
        result["reason"] = "No sponsorship required"
        result["score"] = 10
        return result
    
    # Age factor (assuming under 45 is preferred)
    age_score = 3  # Default assume good age
    
    # English requirement
    english_score = 0
    if candidate.english_level in [EnglishLevelEnum.native, EnglishLevelEnum.fluent]:
        english_score = 3
    elif candidate.english_level == EnglishLevelEnum.good:
        english_score = 2
        result["requirements"].append("IELTS test may be required")
    else:
        english_score = 0
        result["requirements"].append("English proficiency improvement required")
    
    # Experience score
    exp_score = 0
    if candidate.experience_years >= 3:
        exp_score = 3
    elif candidate.experience_years >= 1:
        exp_score = 2
        result["requirements"].append("Skills assessment required")
    else:
        exp_score = 0
        result["requirements"].append("Minimum 1 year experience required")
    
    # Qualifications
    qual_score = 0
    if candidate.childcare_cert:
        if any(qual in candidate.childcare_cert.lower() for qual in ["certificate iii", "diploma", "bachelor"]):
            qual_score = 3
        else:
            qual_score = 1
            result["requirements"].append("Australian qualification assessment required")
    else:
        result["requirements"].append("Relevant childcare qualification required")
    
    total_score = age_score + english_score + exp_score + qual_score
    result["score"] = total_score
    
    # Determine visa pathway and eligibility
    if total_score >= 9:
        result["eligible"] = True
        result["visa_pathway"] = "482 Temporary Skill Shortage visa → 186 Permanent"
        result["reason"] = "Strong candidate for visa sponsorship"
    elif total_score >= 6:
        result["eligible"] = True
        result["visa_pathway"] = "482 Temporary Skill Shortage visa"
        result["reason"] = "Eligible with some requirements to meet"
    else:
        result["eligible"] = False
        result["reason"] = "Does not meet minimum requirements for sponsorship"
        
    return result

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
    candidate.score = enhanced_calculate_candidate_score(candidate)
    
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
    
    # Recalculate score with enhanced algorithm
    temp_candidate = Candidate(**{**candidate_dict, "id": candidate_id})
    candidate_dict["score"] = enhanced_calculate_candidate_score(temp_candidate)
    
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

# Resume upload and parsing
@api_router.post("/candidates/{candidate_id}/upload-resume")
async def upload_resume(candidate_id: str, file: UploadFile = File(...)):
    # Check if candidate exists
    candidate = await db.candidates.find_one({"id": candidate_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse resume based on file type
        parsed_data = {"text": "", "skills": [], "education": None, "work_history": None}
        
        if file.filename.lower().endswith('.pdf'):
            parsed_data = parse_pdf_resume(file_content)
        else:
            # For non-PDF files, store as base64
            parsed_data["text"] = "Non-PDF file uploaded"
        
        # Convert file to base64 for storage
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        resume_url = f"data:{file.content_type};base64,{file_base64}"
        
        # Update candidate with parsed resume data
        update_data = {
            "resume_url": resume_url,
            "resume_text": parsed_data["text"],
            "skills": parsed_data["skills"],
            "education": parsed_data["education"],
            "work_history": parsed_data["work_history"],
            "updated_at": datetime.utcnow()
        }
        
        # Recalculate score with enhanced algorithm
        temp_candidate = Candidate(**{**candidate, **update_data})
        update_data["score"] = enhanced_calculate_candidate_score(temp_candidate)
        
        await db.candidates.update_one(
            {"id": candidate_id},
            {"$set": update_data}
        )
        
        return {
            "message": "Resume uploaded and parsed successfully",
            "parsed_skills": parsed_data["skills"],
            "education": parsed_data["education"],
            "new_score": update_data["score"]
        }
        
    except Exception as e:
        logging.error(f"Resume upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process resume")

# Visa sponsorship evaluation
@api_router.get("/candidates/{candidate_id}/visa-evaluation")
async def get_visa_evaluation(candidate_id: str):
    candidate = await db.candidates.find_one({"id": candidate_id})
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate_obj = Candidate(**candidate)
    evaluation = evaluate_visa_sponsorship_eligibility(candidate_obj)
    
    return evaluation

# Interview management
@api_router.post("/interviews", response_model=Interview)
async def create_interview(interview_data: InterviewCreate):
    # Verify application exists
    application = await db.applications.find_one({"id": interview_data.application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Create interview
    interview_dict = interview_data.dict()
    interview_dict["candidate_id"] = application["candidate_id"]
    interview_dict["job_id"] = application["job_id"]
    
    # Generate meeting link for video interviews
    if interview_data.interview_type == InterviewTypeEnum.video and not interview_data.meeting_link:
        interview_dict["meeting_link"] = f"https://meet.grolearning.com/interview-{interview_dict['id'][:8]}"
    
    interview = Interview(**interview_dict)
    
    await db.interviews.insert_one(interview.dict())
    
    # Send interview invitation email
    candidate = await db.candidates.find_one({"id": interview.candidate_id})
    job = await db.jobs.find_one({"id": interview.job_id})
    
    if candidate and job:
        interview_details = f"""
        <p>Dear {candidate['full_name']},</p>
        <p>We are pleased to invite you for an interview for the position of {job['title']} in {job['location']}.</p>
        <p><strong>Interview Details:</strong></p>
        <ul>
            <li>Date & Time: {interview.scheduled_date.strftime('%A, %B %d, %Y at %I:%M %p')}</li>
            <li>Duration: {interview.duration_minutes} minutes</li>
            <li>Type: {interview.interview_type.value.replace('_', ' ').title()}</li>
        """
        
        if interview.meeting_link:
            interview_details += f"<li>Meeting Link: <a href='{interview.meeting_link}'>{interview.meeting_link}</a></li>"
        elif interview.location:
            interview_details += f"<li>Location: {interview.location}</li>"
            
        interview_details += f"""
        </ul>
        <p>Interviewer: {interview.interviewer_name}</p>
        <p>Please confirm your attendance by replying to this email.</p>
        <p>Best regards,<br>GRO Early Learning Recruitment Team</p>
        """
        
        await send_email(
            candidate["email"],
            f"Interview Invitation - {job['title']}",
            interview_details
        )
    
    return interview

@api_router.get("/interviews", response_model=List[Interview])
async def get_interviews(
    application_id: Optional[str] = Query(None),
    candidate_id: Optional[str] = Query(None),
    status: Optional[InterviewStatusEnum] = Query(None)
):
    query = {}
    if application_id:
        query["application_id"] = application_id
    if candidate_id:
        query["candidate_id"] = candidate_id
    if status:
        query["status"] = status
    
    interviews = await db.interviews.find(query).sort("scheduled_date", 1).to_list(1000)
    return [Interview(**interview) for interview in interviews]

@api_router.put("/interviews/{interview_id}", response_model=Interview)
async def update_interview(interview_id: str, interview_update: InterviewUpdate):
    update_dict = interview_update.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.interviews.update_one(
        {"id": interview_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Send status update email if status changed
    if "status" in update_dict:
        interview = await db.interviews.find_one({"id": interview_id})
        candidate = await db.candidates.find_one({"id": interview["candidate_id"]})
        
        if candidate:
            status_messages = {
                "completed": "Your interview has been completed. We will be in touch with next steps soon.",
                "cancelled": "Your interview has been cancelled. We will contact you to reschedule.",
                "rescheduled": "Your interview has been rescheduled. Please check the new details."
            }
            
            if update_dict["status"] in status_messages:
                await send_email(
                    candidate["email"],
                    f"Interview Update - {update_dict['status'].title()}",
                    f"<p>Dear {candidate['full_name']},</p><p>{status_messages[update_dict['status']]}</p><p>Best regards,<br>GRO Early Learning Team</p>"
                )
    
    updated_interview = await db.interviews.find_one({"id": interview_id})
    return Interview(**updated_interview)

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
