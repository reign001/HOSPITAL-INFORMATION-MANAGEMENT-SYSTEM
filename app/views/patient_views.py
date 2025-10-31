from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Patient, SexEnum, NHISStatus
from sqlalchemy import extract, func
from datetime import datetime
from decorators import role_required

patient_bp = Blueprint("patients", __name__, template_folder="../templates/patients")

# # LIST ALL
@patient_bp.route("/")
def list_patients():
    query = request.args.get("q", "").strip()
    if query:
        patients = Patient.query.filter(
            (Patient.first_name.ilike(f"%{query}%")) |
            (Patient.surname.ilike(f"%{query}%")) |
            (Patient.hospital_number.ilike(f"%{query}%"))|
            (Patient.phone_number.ilike(f"%{query}%"))|
            (Patient.address.ilike(f"%{query}%"))
        ).all()
    else:
        patients = Patient.query.all()
    return render_template("patients/list.html", patients=patients, query=query)



# # DETAIL
@patient_bp.route("/<int:patient_id>")
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patients/detail.html", patient=patient)

# CREATE
@patient_bp.route("/new", methods=["GET", "POST"])
def new_patient():
    if request.method == "POST":
        try:
            patient = Patient(
                first_name=request.form["first_name"],
                middle_name=request.form.get("middle_name"),
                surname=request.form["surname"],
                age=int(request.form["age"]),
                sex=SexEnum(request.form["sex"]),
                address=request.form["address"],
                phone_number=request.form["phone"],
                nhis_status=NHISStatus(request.form["nhis_status"]),
                hospital_number=request.form["hospital_number"],
            )
            db.session.add(patient)
            db.session.commit()
            flash("Patient added successfully!", "success")
            return redirect(url_for("patients.list_patients"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("patients/create.html")

# UPDATE
@patient_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        try:
            patient.first_name = request.form["first_name"]
            patient.middle_name = request.form.get("middle_name")
            patient.surname = request.form["surname"]
            patient.age = int(request.form["age"])
            patient.sex = SexEnum(request.form["sex"])
            patient.address = request.form["address"]
            patient.phone_number = request.form["phone"]
            patient.nhis_status = NHISStatus(request.form["nhis_status"])
            patient.hospital_number = request.form["hospital_number"]

            db.session.commit()
            flash("Patient updated successfully!", "success")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    return render_template("patients/form.html", patient=patient)

# DELETE
@patient_bp.route("/<int:patient_id>/delete", methods=["POST"])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Patient deleted successfully!", "success")
    return redirect(url_for("patients.list_patients"))

# # SEARCh
@patient_bp.route("/search", methods=["GET", "POST"])
def search_patients():
    query = request.args.get("q")
    results = []
    if query:
        results = Patient.query.filter(
            (Patient.surname.ilike(f"%{query}%")) |
            (Patient.phone_number.ilike(f"%{query}%")) |
            (Patient.address.ilike(f"%{query}%"))
        ).all()
    return render_template("patients/search.html", results=results, query=query)

# # YEARLY REPORT
@patient_bp.route("/yearly/<int:year>")
def patients_by_year(year):
    patients = Patient.patients_by_year(year)
    total = len(patients)
    return render_template("patients/yearly.html", patients=patients, year=year, total=total)

# TOTALS SUMMARY (per year)
@patient_bp.route("/yearly-summary")
def yearly_summary():
    summary = db.session.query(
        extract("year", Patient.created_at).label("year"),
        func.count(Patient.id).label("total")
    ).group_by("year").order_by("year").all()
    return render_template("patients/summary.html", summary=summary)
