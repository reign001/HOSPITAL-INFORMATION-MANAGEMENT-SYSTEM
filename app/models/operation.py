from datetime import datetime
from app import db

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