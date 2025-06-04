// MongoDB initialization script for production
db = db.getSiblingDB('gro_ats_production');

// Create application user
db.createUser({
  user: 'groats_app',
  pwd: 'secure_app_password_here',
  roles: [
    {
      role: 'readWrite',
      db: 'gro_ats_production'
    }
  ]
});

// Create indexes for better performance
db.jobs.createIndex({ "status": 1, "location": 1 });
db.jobs.createIndex({ "created_at": -1 });
db.jobs.createIndex({ "sponsorship_eligible": 1 });

db.candidates.createIndex({ "email": 1 }, { unique: true });
db.candidates.createIndex({ "score": -1 });
db.candidates.createIndex({ "visa_status": 1, "sponsorship_needed": 1 });
db.candidates.createIndex({ "location": 1, "rural_experience": 1 });
db.candidates.createIndex({ "created_at": -1 });

db.applications.createIndex({ "job_id": 1, "candidate_id": 1 });
db.applications.createIndex({ "status": 1 });
db.applications.createIndex({ "applied_at": -1 });

db.interviews.createIndex({ "candidate_id": 1, "job_id": 1 });
db.interviews.createIndex({ "scheduled_date": 1 });
db.interviews.createIndex({ "status": 1 });

db.webhook_logs.createIndex({ "sent_at": -1 });
db.webhook_logs.createIndex({ "job_id": 1 });

db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "entity_type": 1, "entity_id": 1 });

print("Database initialization completed successfully");