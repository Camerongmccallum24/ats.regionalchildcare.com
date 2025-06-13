from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
import httpx
import asyncio
import hashlib
import hmac
import asyncpg

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key") # Using the provided SECRET_KEY env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# PostgreSQL Connection Pool
# Using the provided environment variables for PostgreSQL connection
DATABASE_URL = f"postgresql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_DATABASE']}?sslmode={os.environ['DB_SSLMODE']}"

pool: Optional[asyncpg.Pool] = None

async def create_db_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

async def close_db_pool():
    global pool
    if pool:
        await pool.close()

# SendGrid setup
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))

# Careers site webhook configuration
CAREERS_SITE_URL = os.environ.get('CAREERS_SITE_URL', 'https://childcare-career-hub.lovable.app')
CAREERS_WEBHOOK_SECRET = os.environ.get('CAREERS_WEBHOOK_SECRET', 'gro-careers-webhook-2025')
CAREERS_WEBHOOK_TIMEOUT = 30  # seconds

# Get ATS Domain from environment variables
ATS_DOMAIN = os.environ.get("ATS_DOMAIN", "localhost")

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

# Models - These models define the structure of data for API requests and responses
# and map to the PostgreSQL table schemas we defined.
class Job(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
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
    application_id: uuid.UUID
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
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
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    filename: str
    document_type: DocumentTypeEnum
    file_url: str  # Base64 encoded or URL
    file_size: Optional[int] = None
    mime_type: str
    uploaded_by: str
    related_entity_id: uuid.UUID  # candidate_id, job_id, etc.
    related_entity_type: str  # "candidate", "job", etc.
    is_confidential: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    user_email: str
    action: AuditActionEnum
    entity_type: str  # "candidate", "job", "application", etc.
    entity_id: uuid.UUID
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceReport(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
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

# Webhook Models
class JobWebhookPayload(BaseModel):
    """Job data formatted for careers site webhook"""
    job_id: uuid.UUID
    title: str
    location: str
    description: str
    requirements: List[str]
    salary_range: Optional[str] = None
    employment_type: str = "Full-time"
    sponsorship_eligible: bool = False
    relocation_support: bool = False
    housing_support: bool = False
    company_name: str = "GRO Early Learning"
    company_description: str = "Leading childcare provider in rural Queensland"
    contact_email: str = "careers@groearlylearning.com"
    application_url: str = ""
    posted_date: datetime
    expires_date: Optional[datetime] = None
    status: str = "active"

class WebhookLog(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    webhook_url: str
    payload: Dict[str, Any]
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    job_id: Optional[uuid.UUID]

class Application(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    status: ApplicationStatusEnum = ApplicationStatusEnum.new
    cover_letter: Optional[str] = None
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    cover_letter: Optional[str] = None

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

# Advanced helper functions
async def log_audit_action(
    user_id: uuid.UUID,
    user_email: str,
    action: AuditActionEnum,
    entity_type: str,
    entity_id: uuid.UUID,
    details: Dict[str, Any] = {},
    ip_address: Optional[str] = None
):
    """Log audit trail for compliance"""
    async with pool.acquire() as connection:
        await connection.execute('''
            INSERT INTO audit_logs (user_id, user_email, action, entity_type, entity_id, details, ip_address, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ''', user_id, user_email, action.value, entity_type, entity_id, json.dumps(details), ip_address)


def render_email_template(template_content: str, merge_data: Dict[str, Any]) -> str:
    """Render email template with merge fields"""
    try:
        template = Template(template_content)
        return template.render(**merge_data)
    except Exception as e:
        logging.error(f"Template rendering error: {e}")
        return template_content

async def send_templated_email(template_id: uuid.UUID, recipient_email: str, merge_data: Dict[str, Any]):
    """Send email using template with merge fields"""
    try:
        async with pool.acquire() as connection:
            template_record = await connection.fetchrow('''
                SELECT subject, content FROM email_templates WHERE id = $1 AND is_active = TRUE
            ''', template_id)

        if not template_record:
            raise Exception("Template not found or inactive")

        template = EmailTemplate(
            id=template_id,
            name="", # Not needed for sending
            subject=template_record['subject'],
            content=template_record['content'],
            template_type=TemplateTypeEnum.application_received, # Not needed for sending
            created_by="", # Not needed for sending
            created_at=datetime.utcnow(), # Not needed for sending
            updated_at=datetime.utcnow() # Not needed for sending
        )


        # Render template with merge data
        rendered_subject = render_email_template(template.subject, merge_data)
        rendered_content = render_email_template(template.content, merge_data)

        # Send email
        return await send_email(recipient_email, rendered_subject, rendered_content)
    except Exception as e:
        logging.error(f"Templated email sending failed: {e}")
        return False

# Note: build_advanced_search_query would need significant refactoring to build SQL queries
# from the filter model instead of MongoDB queries. This is a complex task and would require
# detailed knowledge of how you want to map the filters to SQL.
# Leaving the MongoDB version for now, but it needs to be replaced.
def build_advanced_search_query(filters: AdvancedSearchFilter) -> Dict[str, Any]:
    """Build MongoDB query from advanced search filters"""
    query = {}

    # Location filters
    if filters.locations:
        query["location"] = {"$in": filters.locations}

    # Visa and sponsorship filters
    if filters.visa_status:
        query["visa_status"] = {"$in": [status.value for status in filters.visa_status]}
    if filters.sponsorship_needed is not None:
        query["sponsorship_needed"] = filters.sponsorship_needed

    # Experience filters
    if filters.min_experience_years is not None or filters.max_experience_years is not None:
        exp_query = {}
        if filters.min_experience_years is not None:
            exp_query["$gte"] = filters.min_experience_years
        if filters.max_experience_years is not None:
            exp_query["$lte"] = filters.max_experience_years
        query["experience_years"] = exp_query

    if filters.rural_experience is not None:
        query["rural_experience"] = filters.rural_experience

    # Score filters
    if filters.min_score is not None or filters.max_score is not None:
        score_query = {}
        if filters.min_score is not None:
            score_query["$gte"] = filters.min_score
        if filters.max_score is not None:
            score_query["$lte"] = filters.max_score
        query["score"] = score_query

    # Availability filters
    if filters.available_from is not None:
        query["availability_start"] = {"$gte": filters.available_from}

    # Relocation filters
    if filters.relocation_willing:
        query["relocation_willing"] = {"$in": [willingness.value for willingness in filters.relocation_willing]}

    # Skills filters
    if filters.required_skills:
        query["skills"] = {"$in": filters.required_skills}

    # Status filters
    if filters.application_status:
        query["status"] = {"$in": [status.value for status in filters.application_status]}

    # Date filters
    if filters.applied_after is not None or filters.applied_before is not None:
        date_query = {}
        if filters.applied_after is not None:
            date_query["$gte"] = filters.applied_after
        if filters.applied_before is not None:
            date_query["$lte"] = filters.applied_before
        query["created_at"] = date_query

    # Text search
    if filters.search_query:
        # This part needs significant translation to PostgreSQL's full-text search or LIKE clauses
        # For simplicity, a basic LIKE search is shown as an example. This might not be performant
        # on large datasets and a proper full-text search setup in PostgreSQL is recommended.
        search_regex = f"%{filters.search_query}%"
        query["$or"] = [
            {"full_name": {"$regex": filters.search_query, "$options": "i"}},
            {"email": {"$regex": filters.search_query, "$options": "i"}},
            {"notes": {"$regex": filters.search_query, "$options": "i"}},
            {"resume_text": {"$regex": filters.search_query, "$options": "i"}},
            {"childcare_cert": {"$regex": filters.search_query, "$options": "i"}}
        ]

    return query


# Note: generate_compliance_report uses MongoDB aggregation pipelines.
# These need to be rewritten as SQL queries or use a library that provides similar
# aggregation capabilities for PostgreSQL if needed.
# Leaving the MongoDB version for now, but it needs to be replaced.
async def generate_compliance_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    user_id: uuid.UUID # Assuming user_id is UUID now
) -> Dict[str, Any]:
    """Generate compliance reports for EEO, visa sponsorship, etc."""
    async with pool.acquire() as connection:
        if report_type == "eeo":
            # EEO compliance report - needs translation to SQL aggregation
            # Example SQL query structure (needs full implementation):
            # SELECT visa_status, COUNT(*), COUNT(CASE WHEN status = 'hired' THEN 1 END), AVG(score)
            # FROM candidates WHERE created_at BETWEEN $1 AND $2 GROUP BY visa_status
            # total_candidates = await connection.fetchval("SELECT COUNT(*) FROM candidates WHERE created_at BETWEEN $1 AND $2", start_date, end_date)
            # eeo_data = await connection.fetch(...)
        return
                "report_type": "eeo",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },