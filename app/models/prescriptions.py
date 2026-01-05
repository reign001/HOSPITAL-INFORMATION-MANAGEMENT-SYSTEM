from datetime import datetime
from app import db

class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    medication_name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")
    prescription_type = db.Column(db.String(20), nullable=False)  # "Admit" or "Outpatient"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship("Patient", backref="prescriptions")
    doctor = db.relationship("User", backref="prescriptions")

    def __repr__(self):
        return f"<Prescription {self.medication_name} for Patient {self.patient_id}>"
