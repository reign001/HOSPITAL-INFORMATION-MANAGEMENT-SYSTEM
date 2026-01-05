from datetime import datetime
from sqlalchemy import extract
from sqlalchemy import Enum as SAEnum
from app import db
from enum import Enum



class NHISStatus(Enum):
    NHIS = "NHIS"
    NON_NHIS = "Non-NHIS"

class SexEnum(Enum):
    MALE = "Male"
    FEMALE = "Female"

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    hospital_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    cards = db.relationship("PatientCard", backref="patient", cascade="all, delete-orphan", passive_deletes=True)
    # Basic demographics
    first_name = db.Column(db.String(120), nullable=False)
    middle_name = db.Column(db.String(120))
    surname = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date)
    sex = db.Column(SAEnum(SexEnum, name="sexenum", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    address = db.Column(db.String(256))
    phone_number = db.Column(db.String(32))
    email = db.Column(db.String(120))
    marital_status = db.Column(db.String(50))
    occupation = db.Column(db.String(120))
    religion = db.Column(db.String(120))
    next_of_kin_name = db.Column(db.String(120))
    next_of_kin_phone = db.Column(db.String(32))
    next_of_kin_relationship = db.Column(db.String(120))
    nhis_status = db.Column(db.Enum(NHISStatus), nullable=False, default=NHISStatus.NON_NHIS)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=True)
    assigned_doctor = db.relationship("Employee", backref="patients_assigned", foreign_keys=[assigned_doctor_id])
    visible_to_nurse = db.Column(db.Boolean, default=False)
    is_pending = db.Column(db.Boolean, default=True)
    ward = db.Column(db.String(100), nullable=True)  # 🏥 New ward field
    is_discharged = db.Column(db.Boolean, default=False)

    # Relationships
    medical_history = db.relationship("MedicalHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    family_history = db.relationship("FamilyHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    social_history = db.relationship("SocialHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    allergies = db.relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    immunizations = db.relationship("Immunization", back_populates="patient", cascade="all, delete-orphan")
    vital_signs = db.relationship("VitalSign", back_populates="patient", cascade="all, delete-orphan")
    
    # Existing links
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
            "age": self.calculate_age(),
            "sex": self.sex.value,
            "nhis_status": self.nhis_status.value,
            "phone": self.phone_number,
        }

    def calculate_age(self):
        if not self.date_of_birth:
            return None
        today = datetime.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @staticmethod
    def patients_by_year(year):
        return Patient.query.filter(extract("year", Patient.created_at) == year).all()
    

    def get_id(self):
        return f"patient-{self.id}"

    def __init_relationships__(self):
        from app.models.operation import OperationDiary
        self.operations = db.relationship(
            "OperationDiary",
            back_populates="patient",
            cascade="all, delete-orphan"
        )

    @property
    def is_authenticated(self):
        return True

    @property
    def active(self):
        return self.is_active  # reuse your existing column

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        # Return a unique string for Flask-Login
        return f"patient-{self.id}"


def get_patient_note():
    pass

class MedicalHistory(db.Model):
    __tablename__ = "medical_history"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("employee.id"))
    chronic_conditions = db.Column(db.Text)
    past_surgeries = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    immunizations = db.Column(db.Text)
    blood_group = db.Column(db.String(10))
    genotype = db.Column(db.String(10))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="medical_history")


class FamilyHistory(db.Model):
    __tablename__ = "family_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"))
    hypertension = db.Column(db.Boolean, default=False)
    diabetes = db.Column(db.Boolean, default=False)
    cancer = db.Column(db.Boolean, default=False)
    heart_disease = db.Column(db.Boolean, default=False)
    stroke = db.Column(db.Boolean, default=False)
    sickle_cell = db.Column(db.Boolean, default=False)
    tuberculosis = db.Column(db.Boolean, default=False)
    asthma = db.Column(db.Boolean, default=False)
    mental_illness = db.Column(db.Boolean, default=False)
    other_conditions = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="family_history")




class SocialHistory(db.Model):
    __tablename__ = "social_history"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    smoking = db.Column(db.Boolean, default=False)
    alcohol = db.Column(db.Boolean, default=False)
    drug_use = db.Column(db.Boolean, default=False)
    occupation = db.Column(db.String(120))
    marital_status = db.Column(db.String(50))
    living_conditions = db.Column(db.Text)

    patient = db.relationship("Patient", back_populates="social_history")


class Allergy(db.Model):
    __tablename__ = "allergies"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"))
    allergen = db.Column(db.String(120), nullable=False)
    reaction = db.Column(db.String(255))
    severity = db.Column(db.String(50))  # e.g. Mild, Moderate, Severe
    date_identified = db.Column(db.Date)
    recorded_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="allergies")



class Immunization(db.Model):
    __tablename__ = "immunizations"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"))
    vaccine_name = db.Column(db.String(120), nullable=False)
    date_administered = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date)
    administered_by = db.Column(db.String(120))
    notes = db.Column(db.Text)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", back_populates="immunizations")



class VitalSign(db.Model):
    __tablename__ = "vital_signs"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)

    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    blood_pressure = db.Column(db.String(20))  # e.g., 120/80 mmHg
    heart_rate = db.Column(db.Integer)  # bpm
    respiratory_rate = db.Column(db.Integer)
    temperature = db.Column(db.Float)  # °C
    weight = db.Column(db.Float)  # kg
    recorded_by = db.Column(db.String(120))
    patient = db.relationship("Patient", back_populates="vital_signs")



class PatientNote(db.Model):
    __tablename__ = "patient_note"

    id = db.Column(db.Integer, primary_key=True)  # ✅ REQUIRED PRIMARY KEY
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PatientRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    request_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_seen = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="Pending")
    admin_note = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    patient = db.relationship("Patient", backref=db.backref("requests", lazy=True))

    

from app.models.cards import PatientCard
from app.models.employee import Employee
