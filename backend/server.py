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
SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# PostgreSQL Connection Pool
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

# Enums and Models (unchanged, omitted for brevity unless requested to show again)

# ... [All Enum and BaseModel definitions remain unchanged] ...

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

# Resume parsing functions (unchanged)

# ... [Parsing and scoring methods remain unchanged] ...

# Audit log function (unchanged)
async def log_audit_action(
    user_id: uuid.UUID,
    user_email: str,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    details: Dict[str, Any] = {},
    ip_address: Optional[str] = None
):
    async with pool.acquire() as connection:
        await connection.execute('''
            INSERT INTO audit_logs (user_id, user_email, action, entity_type, entity_id, details, ip_address, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ''', user_id, user_email, action, entity_type, entity_id, json.dumps(details), ip_address)

def render_email_template(template_content: str, merge_data: Dict[str, Any]) -> str:
    try:
        template = Template(template_content)
        return template.render(**merge_data)
    except Exception as e:
        logging.error(f"Template rendering error: {e}")
        return template_content

async def send_templated_email(template_id: uuid.UUID, recipient_email: str, merge_data: Dict[str, Any]):
    try:
        async with pool.acquire() as connection:
            template_record = await connection.fetchrow('''
                SELECT subject, content FROM email_templates WHERE id = $1 AND is_active = TRUE
            ''', template_id)
        if not template_record:
            raise Exception("Template not found or inactive")
        rendered_subject = render_email_template(template_record['subject'], merge_data)
        rendered_content = render_email_template(template_record['content'], merge_data)
        return await send_email(recipient_email, rendered_subject, rendered_content)
    except Exception as e:
        logging.error(f"Templated email sending failed: {e}")
        return False

# ADVANCED SQL SEARCH (refactored)
async def search_candidates(filters: 'AdvancedSearchFilter') -> List[Dict[str, Any]]:
    """
    Build and execute a SQL query for advanced candidate search.
    """
    query = "SELECT * FROM candidates WHERE TRUE"
    values = []
    idx = 1

    # Location filter
    if filters.locations:
        query += f" AND location = ANY(${idx})"
        values.append(filters.locations)
        idx += 1

    # Visa status filter
    if filters.visa_status:
        query += f" AND visa_status = ANY(${idx})"
        values.append([v.value for v in filters.visa_status])
        idx += 1

    if filters.sponsorship_needed is not None:
        query += f" AND sponsorship_needed = ${idx}"
        values.append(filters.sponsorship_needed)
        idx += 1

    if filters.min_experience_years is not None:
        query += f" AND experience_years >= ${idx}"
        values.append(filters.min_experience_years)
        idx += 1
    if filters.max_experience_years is not None:
        query += f" AND experience_years <= ${idx}"
        values.append(filters.max_experience_years)
        idx += 1

    if filters.rural_experience is not None:
        query += f" AND rural_experience = ${idx}"
        values.append(filters.rural_experience)
        idx += 1

    if filters.min_score is not None:
        query += f" AND score >= ${idx}"
        values.append(filters.min_score)
        idx += 1
    if filters.max_score is not None:
        query += f" AND score <= ${idx}"
        values.append(filters.max_score)
        idx += 1

    if filters.available_from is not None:
        query += f" AND availability_start >= ${idx}"
        values.append(filters.available_from)
        idx += 1

    if filters.relocation_willing:
        query += f" AND relocation_willing = ANY(${idx})"
        values.append([w.value for w in filters.relocation_willing])
        idx += 1

    if filters.required_skills:
        # PostgreSQL array overlap
        query += f" AND (skills && ${idx})"
        values.append(filters.required_skills)
        idx += 1

    if filters.application_status:
        query += f" AND status = ANY(${idx})"
        values.append([a.value for a in filters.application_status])
        idx += 1

    if filters.applied_after is not None:
        query += f" AND created_at >= ${idx}"
        values.append(filters.applied_after)
        idx += 1
    if filters.applied_before is not None:
        query += f" AND created_at <= ${idx}"
        values.append(filters.applied_before)
        idx += 1

    if filters.search_query:
        query += f""" AND (
            full_name ILIKE ${idx} OR
            email ILIKE ${idx} OR
            notes ILIKE ${idx} OR
            resume_text ILIKE ${idx} OR
            childcare_cert ILIKE ${idx}
        )"""
        values.append(f"%{filters.search_query}%")
        idx += 1

    async with pool.acquire() as connection:
        rows = await connection.fetch(query, *values)
        return [dict(row) for row in rows]

# COMPLIANCE REPORT (refactored)
async def generate_compliance_report(
    report_type: str,
    start_date: datetime,
    end_date: datetime,
    user_id: uuid.UUID
) -> Dict[str, Any]:
    async with pool.acquire() as connection:
        if report_type == "eeo":
            total_candidates = await connection.fetchval(
                "SELECT COUNT(*) FROM candidates WHERE created_at BETWEEN $1 AND $2",
                start_date, end_date
            )
            visa_status_counts = await connection.fetch(
                """SELECT visa_status, COUNT(*) AS count
                   FROM candidates
                   WHERE created_at BETWEEN $1 AND $2
                   GROUP BY visa_status""",
                start_date, end_date
            )
            hired_counts = await connection.fetch(
                """SELECT visa_status, COUNT(*) AS hired_count
                   FROM candidates
                   WHERE status = 'hired' AND created_at BETWEEN $1 AND $2
                   GROUP BY visa_status""",
                start_date, end_date
            )
            avg_score = await connection.fetch(
                """SELECT visa_status, AVG(score) AS avg_score
                   FROM candidates
                   WHERE created_at BETWEEN $1 AND $2
                   GROUP BY visa_status""",
                start_date, end_date
            )
            # Combine results as needed for your report
            return {
                "report_type": "eeo",
                "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
                "total_candidates": total_candidates,
                "visa_status_counts": [dict(row) for row in visa_status_counts],
                "hired_counts": [dict(row) for row in hired_counts],
                "avg_score": [dict(row) for row in avg_score],
            }
        # ... Add more report types as needed ...
        return {}

# ... [Rest of your FastAPI endpoint definitions and startup/shutdown events] ...
