# fix_labvisit_patient_ids.py
from app import create_app, db
from app.modelsx import LabVisit, Patient
from datetime import datetime

app = create_app()

def generate_hospital_number():
    """Generate a unique hospital number automatically"""
    count = Patient.query.count() + 1
    return f"AUTO/{count:03d}"

with app.app_context():
    print("🔍 Checking LabVisit records with missing patient_id...")

    visits = LabVisit.query.filter_by(patient_id=None).all()
    if not visits:
        print("✅ All LabVisit records are already linked to patients.")
        exit()

    print(f"Found {len(visits)} visit(s) without a patient_id.")
    linked_count = 0
    created_count = 0

    for v in visits:
        first = (v.patient_name or "").strip().lower()
        last = (v.patient_surname or "").strip().lower()

        # Try to find an existing patient
        patient = (
            Patient.query.filter(
                db.func.lower(Patient.first_name) == first,
                db.func.lower(Patient.surname) == last
            ).first()
        )

        if not patient:
            # Create a new patient automatically
            hospital_number = generate_hospital_number()
            patient = Patient(
                hospital_number=hospital_number,
                first_name=v.patient_name or "Unknown",
                surname=v.patient_surname or "Unknown",
                age=v.patient_age or 0,
                sex=v.sex or "Male",
                address=None,
                phone_number=v.phone_number,
                nhis_status="NHIS",
                created_at=datetime.utcnow()
            )
            db.session.add(patient)
            db.session.flush()  # Get the new patient.id
            created_count += 1
            print(f"🆕 Created new patient: {patient.first_name} {patient.surname} (HN: {hospital_number})")

        # Link LabVisit → Patient
        v.patient_id = patient.id
        db.session.add(v)
        linked_count += 1
        print(f"✅ Linked LabVisit for {v.patient_name} {v.patient_surname} → Patient ID {patient.id}")

    db.session.commit()

    print("\n🎯 Done!")
    print(f"🔗 Linked {linked_count} visit(s)")
    print(f"🧍 Created {created_count} new patient(s)")
