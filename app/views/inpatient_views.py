
# from app.modelsx import InPatientRecord
from flask import jsonify
from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime
from app.models.inpatient import InPatientRecord
from sqlalchemy import func
from app import db
# from app.modelsx import InPatientRecord
from app.models.patients import Patient
from app.forms import InPatientForm
from decorators import role_required


inpatient_bp = Blueprint("inpatient", __name__, url_prefix="/inpatients")



@inpatient_bp.route("/", methods=["GET", "POST"])
def list_inpatients():
    search_query = request.args.get("q", "")
    form = InPatientForm()

    # Populate patient dropdown
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.all()]

    if form.validate_on_submit():
        patient_id = form.patient_id.data  # Already coerced to int

        if not patient_id:
            flash("Please select a valid patient.", "danger")
            return redirect(url_for("inpatient.list_inpatients"))

        # Create new inpatient record
        new_patient = InPatientRecord(
            patient_id=patient_id,
            hospital_number=form.hospital_number.data,
            patient_name=form.patient_name.data,
            sex=form.sex.data,
            age=form.age.data,
            diagnosis=form.diagnosis.data,
            medications_given=form.medications_given.data,
            condition=form.condition.data,
            admitted_at=form.admitted_on.data,
            discharged_at=datetime.utcnow() if form.discharge.data else None,
            discharge=form.discharge.data,
            referred=form.referred.data,
            rip=form.rip.data
        )
        db.session.add(new_patient)
        db.session.commit()
        flash("✅ New inpatient record added successfully!", "success")
        return redirect(url_for("inpatient.list_inpatients"))
    else:
        if form.errors:
            print("❌ Form errors:", form.errors)

    # Searching
    query = InPatientRecord.query
    if search_query:
        query = query.filter(InPatientRecord.patient_name.ilike(f"%{search_query}%"))

    inpatients = query.order_by(InPatientRecord.admitted_at.desc()).all()

    # Totals
    now = datetime.utcnow()
    monthly_total = InPatientRecord.query.filter(
        db.extract("month", InPatientRecord.admitted_at) == now.month,
        db.extract("year", InPatientRecord.admitted_at) == now.year
    ).count()
    yearly_total = InPatientRecord.query.filter(
        db.extract("year", InPatientRecord.admitted_at) == now.year
    ).count()

    return render_template("inpatient/list.html", inpatients=inpatients, monthly_total=monthly_total,
        yearly_total=yearly_total, now=now, form=form)




# ✅ Detail page
@inpatient_bp.route("/<int:patient_id>")
def inpatient_detail(patient_id):
    patient = InPatientRecord.query.get_or_404(patient_id)
    return render_template("inpatient/detail.html", patient=patient)


# ✅ Edit patient
@inpatient_bp.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_inpatient(patient_id):
    patient = InPatientRecord.query.get_or_404(patient_id)
    form = InPatientForm(obj=patient)

    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash("Inpatient record updated successfully!", "success")
        return redirect(url_for("inpatient.list_inpatients"))

    return render_template("inpatient/edit.html", form=form, patient=patient)


# ✅ Delete patient
@inpatient_bp.route("/delete/<int:patient_id>", methods=["POST"])
def delete_inpatient(patient_id):
    patient = InPatientRecord.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Inpatient record deleted successfully!", "danger")
    return redirect(url_for("inpatient.list_inpatients"))

@inpatient_bp.route("/lookup_patient")
def lookup_patient():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "No query provided"}), 400

    # Try hospital number first
    patient = Patient.query.filter_by(hospital_number=q).first()

    # If not found, try name (partial match)
    if not patient:
        patient = Patient.query.filter(Patient.full_name.ilike(f"%{q}%")).first()

    if patient:
        return jsonify({
            "id": patient.id,
            "hospital_number": patient.hospital_number,
            "name": patient.full_name,
            "sex": patient.sex.value if patient.sex else None,
            "age": patient.age
        })

    return jsonify({"error": "Patient not found"}), 404

