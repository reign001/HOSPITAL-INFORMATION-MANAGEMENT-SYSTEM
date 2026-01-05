from app import db
from datetime import datetime



from enum import Enum

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    sender_type = db.Column(db.Enum("EMPLOYEE", "PATIENT", name="usertype"), nullable=False)
    receiver_type = db.Column(db.Enum("EMPLOYEE", "PATIENT", name="usertype"), nullable=False)

    subject = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Conditional relationships
    sender_employee = db.relationship(
        "Employee",
        primaryjoin="and_(Message.sender_id==foreign(Employee.id), Message.sender_type=='EMPLOYEE')",
        viewonly=True
    )
    receiver_employee = db.relationship(
        "Employee",
        primaryjoin="and_(Message.receiver_id==foreign(Employee.id), Message.receiver_type=='EMPLOYEE')",
        viewonly=True
    )

    sender_patient = db.relationship(
        "Patient",
        primaryjoin="and_(Message.sender_id==foreign(Patient.id), Message.sender_type=='PATIENT')",
        viewonly=True
    )
    receiver_patient = db.relationship(
        "Patient",
        primaryjoin="and_(Message.receiver_id==foreign(Patient.id), Message.receiver_type=='PATIENT')",
        viewonly=True
    )


