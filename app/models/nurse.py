from app import db
from datetime import datetime


class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True)  # ✅ REQUIRED PRIMARY KEY
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)





class NurseNote(db.Model):
    __tablename__ = "note_note"

    id = db.Column(db.Integer, primary_key=True)  # ✅ REQUIRED PRIMARY KEY
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
