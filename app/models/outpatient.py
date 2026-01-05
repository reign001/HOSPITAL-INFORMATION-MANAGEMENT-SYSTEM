from app import db
from datetime import datetime

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