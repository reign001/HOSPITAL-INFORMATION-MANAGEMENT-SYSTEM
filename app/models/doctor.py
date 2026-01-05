from app import db
from datetime import datetime




class ClerkingRecord(db.Model):
    __tablename__ = "clerking_record"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)

    presenting_complaint = db.Column(db.Text, nullable=True)
    history_of_presenting_complaint = db.Column(db.Text, nullable=True)
    past_medical_history = db.Column(db.Text, nullable=True)
    drug_history = db.Column(db.Text, nullable=True)
    family_history = db.Column(db.Text, nullable=True)
    social_history = db.Column(db.Text, nullable=True)
    examination_findings = db.Column(db.Text, nullable=True)
    provisional_diagnosis = db.Column(db.Text, nullable=True)
    plan = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


class ClinicalNote(db.Model):
    __tablename__ = "clinical_note"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    diagnosis = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship("Patient", backref="clinical_notes")
    doctor = db.relationship("Employee", backref="notes_created")



from app.models.patients import Patient