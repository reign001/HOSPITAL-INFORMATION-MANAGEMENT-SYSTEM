# routes/outpatient.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from datetime import datetime
from app import db
from app.models.outpatient import OutPatientRecord
from app.forms import OutPatientForm
from decorators import role_required

outpatient_bp = Blueprint("outpatient", __name__, url_prefix="/outpatients")


@outpatient_bp.route("/", methods=["GET", "POST"])
# @role_required()
def list_outpatients():
    form = OutPatientForm()
    if form.validate_on_submit():
        new_record = OutPatientRecord(
            patient_name=form.patient_name.data,
            sex=form.sex.data,
            age=form.age.data,
            address=form.address.data,
            medications_given=form.medications_given.data,
            nhis_status=form.nhis_status.data
        )
        db.session.add(new_record)
        db.session.commit()
        flash("Outpatient record added successfully!", "success")
        return redirect(url_for("outpatient.list_outpatients"))

    # 📊 Summary filters
    today = datetime.utcnow().date()
    daily_total = OutPatientRecord.query.filter(db.func.date(OutPatientRecord.visited_at) == today).count()
    monthly_total = OutPatientRecord.query.filter(db.extract("month", OutPatientRecord.visited_at) == today.month).count()
    yearly_total = OutPatientRecord.query.filter(db.extract("year", OutPatientRecord.visited_at) == today.year).count()

    nhis_count = OutPatientRecord.query.filter_by(nhis_status="NHIS").count()
    non_nhis_count = OutPatientRecord.query.filter_by(nhis_status="NON-NHIS").count()

    outpatients = OutPatientRecord.query.order_by(OutPatientRecord.visited_at.desc()).all()

    return render_template(
        "outpatient/list.html",
        form=form,
        outpatients=outpatients,
        daily_total=daily_total,
        monthly_total=monthly_total,
        yearly_total=yearly_total,
        nhis_count=nhis_count,
        non_nhis_count=non_nhis_count,
    )


@outpatient_bp.route("/<int:patient_id>")
# @role_required()
def outpatient_detail(patient_id):
    patient = OutPatientRecord.query.get_or_404(patient_id)
    return render_template("outpatient/detail.html", patient=patient)


@outpatient_bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
# @role_required()
def edit_outpatient(patient_id):
    patient = OutPatientRecord.query.get_or_404(patient_id)
    form = OutPatientForm(obj=patient)

    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash("Outpatient record updated!", "success")
        return redirect(url_for("outpatient.list_outpatients"))

    return render_template("outpatient/edit.html", form=form)


@outpatient_bp.route("/<int:patient_id>/delete", methods=["POST"])
# @role_required()
def delete_outpatient(patient_id):
    patient = OutPatientRecord.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash("Outpatient record deleted!", "danger")
    return redirect(url_for("outpatient.list_outpatients"))

