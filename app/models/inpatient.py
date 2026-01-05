from app import db
from datetime import datetime

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


