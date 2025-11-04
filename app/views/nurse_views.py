# app/views/nurse/routes.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import db, Patient, MedicationAdministration, PatientCard, Prescription, LabVisit, LabRequest

nurse_bp = Blueprint("nurse", __name__, url_prefix="/nurse")

# --- Access control decorator (optional) ---
def nurse_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ["nurse_admin", "Nursing_Admin", "super_admin"]:
            flash("Access denied: Nurses only.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated


# -----------------------------
# Nurse Dashboard
# -----------------------------
@nurse_bp.route("/dashboard")
@login_required
def dashboard():
    query = request.args.get("q", "").strip()
    
    if query:
        patients = Patient.query.filter(
            (Patient.first_name.ilike(f"%{query}%")) |
            (Patient.surname.ilike(f"%{query}%")) |
            (Patient.hospital_number.ilike(f"%{query}%"))
        ).all()
    else:
        patients = Patient.query.all()

    # Get most recent lab visits and requests for each patient
    patient_visits = {
        p.id: LabVisit.query.filter_by(patient_id=p.id)
                            .order_by(LabVisit.created_at.desc())
                            .first()
        for p in patients
    }

    patient_requests = {
        p.id: LabRequest.query.filter_by(patient_id=p.id)
                              .order_by(LabRequest.created_at.desc())
                              .first()
        for p in patients
    }

    return render_template(
        "nurse/dashboard.html",
        patients=patients,
        patient_visits=patient_visits,
        patient_requests=patient_requests,
        query=query
    )


# -----------------------------
# View Doctor's Prescription Sheet (Read-only)
# -----------------------------
@nurse_bp.route("/patient/<int:patient_id>/prescription")
@login_required
def view_prescription(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    prescription = Prescription.query.filter_by(patient_id=patient.id).order_by(Prescription.created_at.desc()).first()

    if not prescription:
        flash("⚠️ No prescription found for this patient yet.", "warning")
        return redirect(url_for("nurse.dashboard"))

    return render_template(
        "nurse/view_prescription.html",  # separate template for nurses
        patient=patient,
        prescription=prescription
    )


# -----------------------------
# View or Update Patient Folder (Read/Write)
# -----------------------------
@nurse_bp.route("/patient/<int:patient_id>/card", methods=["GET", "POST"])
def update_patient_card(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    card = PatientCard.query.filter_by(patient_id=patient.id).first()

    if not card:
        card = PatientCard(patient_id=patient.id)
        db.session.add(card)
        db.session.commit()

    if request.method == "POST":
        notes = request.form.get("notes")
        card.notes = notes
        db.session.commit()
        flash("✅ Patient card updated successfully.", "success")
        return redirect(url_for("nurse.dashboard"))

    return render_template("doctor/patient_card.html", patient=patient, card=card)


# --- View/Update Patient Folder ---
@nurse_bp.route("/folder/<int:patient_id>", methods=["GET", "POST"])
@login_required
def patient_folder(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    # Always make sure the patient has a card
    card = PatientCard.query.filter_by(patient_id=patient.id).first()
    if not card:
        card = PatientCard(patient_id=patient.id)
        db.session.add(card)
        db.session.commit()

    if request.method == "POST":
        note = request.form.get("note") or request.form.get("notes")  # handle either field name
        if note:
            card.notes = note  # <-- write to PatientCard.notes, not Patient.notes
            db.session.commit()
            flash("✅ Patient folder updated successfully!", "success")
        else:
            flash("⚠️ No note entered!", "warning")

    return render_template("doctor/patient_card.html", patient=patient, card=card)



# --- Medication Administration Chart ---
@nurse_bp.route("/chart/<int:patient_id>", methods=["GET", "POST"])
# @login_required
# @nurse_required
def medication_chart(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        med = MedicationAdministration(
            patient_id=patient_id,
            nurse_id=current_user.id,
            medication_name=request.form.get("medication_name"),
            dosage=request.form.get("dosage"),
            route=request.form.get("route"),
            notes=request.form.get("notes")
        )
        db.session.add(med)
        db.session.commit()
        flash("Medication administration recorded!", "success")

    records = MedicationAdministration.query.filter_by(patient_id=patient_id).all()
    return render_template("nurse/medication_chart.html", patient=patient, records=records)
