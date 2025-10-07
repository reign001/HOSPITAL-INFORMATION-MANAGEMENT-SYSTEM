from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Patient, PatientCard, Prescription, LabRequest
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
    
    return render_template("doctor/dashboard.html", patients=patients, query=query)


@doctor_bp.route("/doctor/patient/<int:patient_id>/card", methods=["GET", "POST"])
@login_required
def update_patient_card(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    card = PatientCard.query.filter_by(patient_id=patient.id).first()
    if not card:
        card = PatientCard(patient_id=patient.id)

    if request.method == "POST":
        notes = request.form.get("notes")
        card.notes = notes
        db.session.add(card)
        db.session.commit()
        flash("Patient card updated", "success")
        return redirect(url_for("doctor.doctor_dashboard"))

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
        return redirect(url_for("doctor.doctor_dashboard"))

    return render_template("doctor/prescription_form.html", patient=patient)


@doctor_bp.route("/doctor/patient/<int:patient_id>/lab", methods=["GET", "POST"])
@login_required
def create_lab_request(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        tests = request.form.get("tests")
        request_form = LabRequest(patient_id=patient.id, doctor_id=current_user.id, tests_requested=tests)
        db.session.add(request_form)
        db.session.commit()
        flash("Lab request submitted", "success")
        return redirect(url_for("doctor.doctor_dashboard"))

    return render_template("doctor/lab_request_form.html", patient=patient)
