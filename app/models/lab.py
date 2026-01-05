from datetime import datetime, date, timedelta
from sqlalchemy import func  
from sqlalchemy import func
from datetime import date
from decimal import Decimal
import enum
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Enum as SAEnum
from app import db, login_manager
from sqlalchemy import extract
from flask_login import UserMixin
from app.models.patients import Patient

class LabVisit(db.Model):
    __tablename__ = "lab_visit"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True)

    # cached info
    patient_name = db.Column(db.String(120))
    patient_surname = db.Column(db.String(120))
    patient_age = db.Column(db.Integer)
    sex = db.Column(db.String(10))
    nhis_status = db.Column(db.String(20))  # NHIS / Non-NHIS
    inpatient_status = db.Column(db.String(20))  # Inpatient / Outpatient
    phone_number = db.Column(db.String(20))

    sample = db.Column(db.String(120))
    referring_physician = db.Column(db.String(120))
    laboratory_number = db.Column(db.String(50), unique=True)

    investigations = db.Column(db.Text, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False, default=0.0)
    result = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    patient = db.relationship("Patient", back_populates="lab_visits")
    lab_requests = db.relationship("LabRequest", back_populates="visit")

    def __repr__(self):
        return f"<LabVisit {self.patient_name} {self.patient_surname} - {self.investigations}>"
    

from datetime import datetime
from app import db

class LabRequest(db.Model):
    __tablename__ = "lab_requests"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("lab_visit.id"), nullable=True)

    # A comma-separated or JSON list of investigations requested
    tests_requested = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    status = db.Column(db.String(20), default="Pending")  # Pending, Processing, Completed
    is_completed = db.Column(db.Boolean, default=False)

    # Relationship to LabResult
    results = db.relationship("LabResult", back_populates="lab_request", cascade="all, delete-orphan")

    # Relationships
    patient = db.relationship("Patient", backref="lab_requests")
    doctor = db.relationship("User", backref="lab_requests")
    visit = db.relationship("LabVisit", back_populates="lab_requests")

    def __repr__(self):
        return f"<LabRequest {self.id} - {self.status}>"


class LabResult(db.Model):
    __tablename__ = "lab_results"

    id = db.Column(db.Integer, primary_key=True)
    lab_request_id = db.Column(db.Integer, db.ForeignKey("lab_requests.id"), nullable=False)

    test_name = db.Column(db.String(120), nullable=False)
    result_value = db.Column(db.Text, nullable=True)
    normal_range = db.Column(db.String(100), nullable=True)
    comments = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_by = db.Column(db.String(120), nullable=True)  # e.g., lab tech name or user ID

    # Relationship back to request
    lab_request = db.relationship("LabRequest", back_populates="results")

    def __repr__(self):
        return f"<LabResult {self.test_name} for Request {self.lab_request_id}>"


