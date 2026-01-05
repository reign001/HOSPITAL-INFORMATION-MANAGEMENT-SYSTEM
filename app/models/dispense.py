from app import db
from datetime import datetime
class DispenseRecord(db.Model):
     __tablename__ = "dispense_records"

     id = db.Column(db.Integer, primary_key=True)
     patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
     drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), nullable=False)  # FK to Drug

     quantity_dispensed = db.Column(db.Integer, nullable=False)
     total_cost = db.Column(db.Float, nullable=False)   # based on cost price * quantity
     amount_paid = db.Column(db.Float, nullable=True)   # can be null
     balance = db.Column(db.Float, nullable=True)       # amount remaining if not fully paid
     dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)

     # Relationships
     patient = db.relationship("Patient", back_populates="dispensary_records")
     drug = db.relationship("Drug", back_populates="dispenses")

     def __repr__(self):
         return f"<DispenseRecord {self.patient.full_name()} - {self.drug.name}>"
