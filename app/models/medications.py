from datetime import datetime
from app import db

from datetime import datetime
from app import db

class ActiveMedication(db.Model):
    __tablename__ = "active_medications"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    # 💊 Prescription details
    drug_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(50))  # e.g., "Every 8 hours"
    duration = db.Column(db.String(50))   # e.g., "5 days"
    route = db.Column(db.String(50))      # e.g., "Oral", "IM", "IV"

    # 🕓 New: time the medication *should* be given
    scheduled_time = db.Column(db.DateTime, nullable=True)

    # 🩺 Prescription metadata
    date_prescribed = db.Column(db.DateTime, default=datetime.utcnow)
    prescribed_by_id = db.Column(db.Integer, db.ForeignKey("employee.id"))
    prescribed_by = db.relationship("Employee", foreign_keys=[prescribed_by_id], backref=db.backref("prescribed_medications", lazy=True))

    # 💉 Administration details (done by nurse)
    date_administered = db.Column(db.DateTime, nullable=True)
    dose_given = db.Column(db.String(100), nullable=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=True)
    nurse = db.relationship(
        "Employee",
        foreign_keys=[nurse_id],
        backref=db.backref("administered_medications", lazy=True)
    )

    # ⚙️ Status tracking
    administered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🔗 Relationship
    patient = db.relationship(
        "Patient",
        backref=db.backref("active_medications", cascade="all, delete-orphan", lazy=True)
    )

    def __repr__(self):
        return f"<ActiveMedication {self.drug_name} for {self.patient.full_name()}>"
    



def get_active_medications():
    pass



from app import db
from datetime import datetime

class MedicationAdministration(db.Model):
    __tablename__ = "medication_administration"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))  # e.g. "500 mg" or "1 g"
    route = db.Column(db.String(20))   # IV, IM, Subcute, Subl, Oral
    administration_time = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    nurse = db.relationship("User", backref="administrations")
    patient = db.relationship("Patient", backref="med_admin_records")

    


if __name__ == "__main__":
    print("This module defines models and helpers for a HIMS. Import into your Flask app.")
