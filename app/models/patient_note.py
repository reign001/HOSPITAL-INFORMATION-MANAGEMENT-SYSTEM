from datetime import datetime
from app import db

class PatientNote(db.Model):
    __tablename__ = "patient_notes"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    patient = db.relationship("Patient", backref=db.backref("notes", cascade="all, delete-orphan", lazy=True))

    def __repr__(self):
        return f"<PatientNote {self.id} for {self.patient.full_name()}>"
