from datetime import datetime
from app import db

class PatientCard(db.Model):
    __tablename__ = "patient_cards"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Vital signs (nurse entry)
    blood_pressure = db.Column(db.String(20))
    heart_rate = db.Column(db.Integer)
    respiratory_rate = db.Column(db.Integer)
    temperature = db.Column(db.Float)
    oxygen_saturation = db.Column(db.String(20))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    bmi = db.Column(db.Float)


    # Clinical Details
    chief_complaint = db.Column(db.Text)
    history_of_present_illness = db.Column(db.Text)
    past_medical_history = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)


    # Examination findings (doctor entry)
    examination = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)

    # Lab & investigation results
    investigations = db.Column(db.Text)
    lab_results = db.Column(db.Text)
    imaging_results = db.Column(db.Text)

    # Backref to patient
    # patient = db.relationship("Patient", backref=db.backref("cards", cascade="all, delete-orphan", lazy=True))

    def __repr__(self):
        return f"<PatientCard {self.id} for {self.patient.first_name} {self.patient.surname}>"
