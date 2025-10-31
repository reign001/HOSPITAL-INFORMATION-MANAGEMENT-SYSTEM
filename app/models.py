"""
Flask + SQLAlchemy models and helpers for a Hospital Information Management System (HIMS).
Single-file starter module containing:
- Models (Patient, OperationDiary, InPatient, OutPatient, Drug, DispenseRecord, LabTest, LabVisit, User, Role)
- Relationships and constraints
- Helper functions for daily/monthly summaries (financials, drug usage, NHIS percent)

Usage:
- Drop into a Flask app and register Flask-SQLAlchemy as `db`.
- This is a starting point and intentionally opinionated; adapt to your needs.

Notes:
- Use Alembic (flask-migrate) for migrations in production.
- Add authentication/authorization for user actions (creating, dispensing, payments) in views.

"""
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

from flask_sqlalchemy import SQLAlchemy



class SexEnum(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class NHISStatus(Enum):
    NHIS = "NHIS"
    NON_NHIS = "NON_NHIS"


# --------------------------
# Core models
# --------------------------
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="staff")  
    # roles: super_admin, admin, staff, etc.

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_super_admin(self):
        return self.role == "super_admin"

    def is_admin(self):
        return self.role in ["admin", "super_admin"]  # super_admins also count as admins
    
    def is_nurse(self):
        return self.role in ["nurse_admin", "Nursing_Admin", "super_admin"]

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------
# Users / Staff (simple)
# --------------------------

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))


class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    hospital_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(120), nullable=False)
    middle_name = db.Column(db.String(120))
    surname = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(SAEnum(SexEnum, name="sexenum", values_callable=lambda obj: [e.value for e in obj]),
    nullable=False,
    default=SexEnum.MALE.value
)
    address = db.Column(db.String(256))
    phone_number = db.Column(db.String(32))
    nhis_status = db.Column(db.Enum(NHISStatus), nullable=False, default=NHISStatus.NON_NHIS)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    operations = db.relationship("OperationDiary", back_populates="patient", cascade="all, delete-orphan")
    inpatient_records = db.relationship("InPatientRecord", back_populates="patient", cascade="all, delete-orphan")
    outpatient_records = db.relationship("OutPatientRecord", back_populates="patient", cascade="all, delete-orphan")
    dispensary_records = db.relationship("DispenseRecord", back_populates="patient", cascade="all, delete-orphan")
    lab_visits = db.relationship("LabVisit", back_populates="patient", cascade="all, delete-orphan")

    def full_name(self):
        parts = [self.first_name, self.middle_name, self.surname]
        return " ".join([p for p in parts if p])

    def to_dict(self):
        return {
            "id": self.id,
            "hospital_number": self.hospital_number,
            "name": self.full_name(),
            "age": self.age,
            "sex": self.sex.value,
            "nhis_status": self.nhis_status.value,
            "phone": self.phone_number,
        }
    
    @staticmethod
    def patients_by_year(year):
        return Patient.query.filter(extract("year", Patient.created_at) == year).all()
    

# Doctor/User model assumed to exist, adjust accordingly

class PatientCard(db.Model):
    __tablename__ = "patient_cards"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, unique=True)
    notes = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship("Patient", backref=db.backref("card", uselist=False))


class Prescription(db.Model):
    __tablename__ = "prescriptions"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    drugs = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_dispensed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default="Pending")
    patient = db.relationship("Patient", backref="prescriptions")
    doctor = db.relationship("User", backref="prescriptions")


class LabRequest(db.Model):
    __tablename__ = "lab_requests"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    visit_id = db.Column(db.Integer, db.ForeignKey("lab_visit.id"), nullable=True)

    tests_requested = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="Pending")

    # relationships
    patient = db.relationship("Patient", backref="lab_requests")
    doctor = db.relationship("User", backref="lab_requests")
    visit = db.relationship("LabVisit", back_populates="lab_requests")

    def __repr__(self):
        return f"<LabRequest {self.id} - {self.status}>"


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

class OperationDiary(db.Model):
    __tablename__ = "operation_diary"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)

    # Patient snapshot
    patient_name = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(256), nullable=False, server_default="Unknown")
    patient_age = db.Column(db.Integer)
    patient_sex = db.Column(db.String(10), nullable=False)
    hospital_number = db.Column(db.String(64))

    # Surgery details
    diagnosis = db.Column(db.Text)
    surgery_done = db.Column(db.Text)
    findings = db.Column(db.Text)
    estimated_blood_loss = db.Column(db.String(64))
    anesthesia_type = db.Column(db.String(128))

    surgeon_name = db.Column(db.String(256))
    assistant_name = db.Column(db.String(256))
    anaesthetist_name = db.Column(db.String(256))

    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)

    post_op_condition = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="operations")

    def compute_duration(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() // 60)
            return self.duration_minutes
        return None


class InPatientRecord(db.Model):
    __tablename__ = "inpatients"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    hospital_number = db.Column(db.String(50)) 
    patient_name = db.Column(db.String(256), nullable=False)
    sex = db.Column(db.String(20)) 
    age = db.Column(db.Integer)
    diagnosis = db.Column(db.Text)
    medications_given = db.Column(db.Text)
    condition = db.Column(db.Text)
    discharge = db.Column(db.Boolean, default=False)
    referred = db.Column(db.Boolean, default=False)
    rip = db.Column(db.Boolean, default=False)
    admitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    discharged_at = db.Column(db.DateTime)

    patient = db.relationship("Patient", back_populates="inpatient_records")


class OutPatientRecord(db.Model):
    __tablename__ = "outpatients"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True)
    patient_name = db.Column(db.String(256), nullable=False)
    sex = db.Column(db.String(10))  
    age = db.Column(db.Integer)
    medications_given = db.Column(db.Text)
    address = db.Column(db.String(256))
    nhis_status = db.Column(db.String(20), nullable=False, default="NON-NHIS")
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship("Patient", back_populates="outpatient_records")


class Delivery(db.Model):
    __tablename__ = 'deliveries'

    id = db.Column(db.Integer, primary_key=True)
    mother_name = db.Column(db.String(120), nullable=False)
    mother_age = db.Column(db.Integer, nullable=True)  
    nhis_status = db.Column(db.String(20), nullable=False, default="NON-NHIS")  # NHIS / NON-NHIS
    delivery_date = db.Column(db.Date, default=datetime.utcnow)
    delivery_time = db.Column(db.Time, nullable=True)

    delivery_type = db.Column(db.String(50), nullable=False)  # Normal / CS
    cs_indication = db.Column(db.String(255), nullable=True)  # Only if CS

    baby_gender = db.Column(db.String(10), nullable=False)
    baby_weight = db.Column(db.Float, nullable=True)  # kg

    mother_condition = db.Column(db.String(255), nullable=True)
    baby_condition = db.Column(db.String(255), nullable=True)
# --------------------------
# Pharmacy models
# --------------------------

class Drug(db.Model):
    __tablename__ = "drugs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand_name = db.Column(db.String(256), nullable=True)
    expiry_date = db.Column(db.Date, nullable=False)
    unit_cost_price = db.Column(db.Float, nullable=False)
    unit_selling_price = db.Column(db.Float, nullable=False)
    quantity_left = db.Column(db.Integer, nullable=False)
    quantity_supplied = db.Column(db.Integer, nullable=False)

    # relationship to DispenseRecord
    dispenses = db.relationship("DispenseRecord", back_populates="drug", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Drug {self.name} ({self.brand_name})>"

    @property
    def dispensed_today(self):
        today = datetime.utcnow().date()
        return sum(
            d.quantity_dispensed for d in self.dispenses
            if d.dispensed_at.date() == today
        )

    @property
    def dispensed_month(self):
        now = datetime.utcnow()
        return sum(
            d.quantity_dispensed for d in self.dispenses
            if d.dispensed_at.year == now.year and d.dispensed_at.month == now.month
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand_name": self.brand_name,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "unit_cost_price": float(self.unit_cost_price),
            "unit_selling_price": float(self.unit_selling_price),
            "quantity_left": self.quantity_left,
            "dispensed_today": self.dispensed_today,
            "dispensed_month": self.dispensed_month,
        }


class DispenseRecord(db.Model):
    __tablename__ = "dispense_records"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), nullable=False)  # FK to Drug

    quantity_dispensed = db.Column(db.Integer, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)   # based on cost price * quantity
    amount_paid = db.Column(db.Float, nullable=True)   # can be null
    balance = db.Column(db.Float, nullable=True)       # amount remaining if not fully paid
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship("Patient", back_populates="dispensary_records")
    drug = db.relationship("Drug", back_populates="dispenses")

    def __repr__(self):
        return f"<DispenseRecord {self.patient.full_name()} - {self.drug.name}>"






# ----------------------
# Utility functions
# ----------------------

def get_daily_lab_total():
    today = date.today()
    total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) == today
    ).scalar()
    return total or 0.0


def get_weekly_lab_total():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)          # Sunday

    total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) >= start_of_week,
        func.date(LabVisit.created_at) <= end_of_week
    ).scalar()
    return total or 0.0


def get_monthly_lab_total():
    today = date.today()
    start_of_month = today.replace(day=1)

    total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) >= start_of_month,
        func.extract("year", LabVisit.created_at) == today.year,
        func.extract("month", LabVisit.created_at) == today.month
    ).scalar()
    return total or 0.0



class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20))

    date_of_employment = db.Column(db.Date, nullable=False)
    office_location = db.Column(db.String(150))
    position = db.Column(db.String(150))
    department = db.Column(db.String(150))

    issues = db.Column(db.Text)  # e.g. HR issues, disciplinary records
    qualifications = db.Column(db.Text)  # certificates, degrees
    schools_attended = db.Column(db.Text)

    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    address = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Staff {self.first_name} {self.surname}>"


from datetime import datetime, date
from app import db


class FinanceRecord(db.Model):
    __tablename__ = "finance_records"

    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.Date, default=date.today, unique=True)

    dispensary_total = db.Column(db.Float, default=0.0)
    laboratory_total = db.Column(db.Float, default=0.0)
    hmos_total = db.Column(db.Float, default=0.0)

    total_income = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = db.relationship("FinanceLog", back_populates="finance_record", cascade="all, delete-orphan")

    def compute_total(self):
        """Recalculate total income."""
        self.total_income = (self.dispensary_total or 0) + (self.laboratory_total or 0) + (self.hmos_total or 0)

    def __repr__(self):
        return f"<FinanceRecord {self.record_date} - Total: {self.total_income}>"



class HMOPayment(db.Model):
    __tablename__ = "hmo_payments"

    id = db.Column(db.Integer, primary_key=True)
    hmo_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finance_id = db.Column(db.Integer, db.ForeignKey("finance_records.id", ondelete="CASCADE"))
    finance_record = db.relationship("FinanceRecord", backref="hmo_payments")


class FinanceLog(db.Model):
    __tablename__ = "finance_logs"

    id = db.Column(db.Integer, primary_key=True)
    finance_record_id = db.Column(db.Integer, db.ForeignKey("finance_records.id", ondelete="CASCADE"))

    record_date = db.Column(db.Date, nullable=False)
    section = db.Column(db.String(50))  # dispensary / laboratory / hmos / update / delete
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    finance_record = db.relationship("FinanceRecord", back_populates="logs")

    def __repr__(self):
        return f"<FinanceLog {self.record_date} - {self.section} - {self.amount}>"

from sqlalchemy import func
from datetime import date, timedelta
from app.models import DispenseRecord, LabVisit, FinanceRecord

def calculate_daily_dispensary_total(day=None):
    if not day:
        day = date.today()
    total = db.session.query(func.sum(DispenseRecord.amount_paid)).filter(
        func.date(DispenseRecord.dispensed_at) == day
    ).scalar()
    return total or 0.0

def calculate_daily_lab_total(day=None):
    if not day:
        day = date.today()
    total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) == day
    ).scalar()
    return total or 0.0

def update_finance_record(day=None):
    if not day:
        day = date.today()

    dispensary_total = calculate_daily_dispensary_total(day)
    lab_total = calculate_daily_lab_total(day)

    # check if finance record exists
    record = FinanceRecord.query.filter_by(record_date=day).first()
    if not record:
        record = FinanceRecord(record_date=day)

    record.dispensary_total = dispensary_total
    record.laboratory_total = lab_total
    record.compute_total()

    db.session.add(record)
    db.session.commit()
    return record


class MedicationAdministration(db.Model):
    __tablename__ = "medication_administration"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))  # e.g. "500 mg" or "1 g"
    route = db.Column(db.String(20))   # IV, IM, Subcute, Subl, Oral
    administration_time = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    nurse = db.relationship("User", backref="administrations")
    patient = db.relationship("Patient", backref="med_admin_records")


if __name__ == "__main__":
    print("This module defines models and helpers for a HIMS. Import into your Flask app.")
