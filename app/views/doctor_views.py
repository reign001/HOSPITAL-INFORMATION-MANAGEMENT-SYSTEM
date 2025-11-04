from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Patient, PatientCard, Prescription, LabRequest, LabVisit
from flask import Blueprint, render_template


doctor_bp = Blueprint("doctor", __name__, template_folder="../templates/doctor")

@doctor_bp.route("/dashboard")
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

    # Build dictionaries mapping patient.id → latest visit/request
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
        "doctor/dashboard.html",
        patients=patients,
        patient_visits=patient_visits,
        patient_requests=patient_requests,
        query=query
    )


@doctor_bp.route("/doctor/patient/<int:patient_id>/card", methods=["GET", "POST"])
@login_required
def update_patient_card(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    card = PatientCard.query.filter_by(patient_id=patient.id).first()

    # Ensure card exists in DB
    if not card:
        card = PatientCard(patient_id=patient.id)
        db.session.add(card)
        db.session.commit()

    if request.method == "POST":
        notes = request.form.get("notes")
        card.notes = notes
        db.session.commit()
        flash("Patient card updated", "success")
        return redirect(url_for("doctor.dashboard"))

    return render_template("doctor/patient_card.html", patient=patient, card=card)



@doctor_bp.route("/doctor/patient/<int:patient_id>/prescription", methods=["GET", "POST"])
@login_required
def create_prescription(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        drugs = request.form.get("drugs")
        prescription = Prescription(patient_id=patient.id, doctor_id=current_user.id, drugs=drugs)
        db.session.add(prescription)
        db.session.commit()
        flash("Prescription submitted", "success")
        return redirect(url_for("doctor.dashboard"))

    return render_template("doctor/prescription_form.html", patient=patient)

from datetime import datetime
@doctor_bp.route("/doctor/patient/<int:patient_id>/lab", methods=["GET", "POST"])
@login_required
def create_lab_request(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        tests = request.form.get("tests")

        # ✅ Create LabRequest with explicit "Pending" status
        request_form = LabRequest(
            patient_id=patient.id,
            doctor_id=current_user.id,
            tests_requested=tests,
            status="Pending",  # ← ADD THIS LINE
            created_at=datetime.utcnow()  # ← also good to include timestamp explicitly
        )

        db.session.add(request_form)
        db.session.commit()
        flash("Lab request submitted successfully!", "success")
        return redirect(url_for("doctor.dashboard"))

    return render_template("doctor/lab_request_form.html", patient=patient)

