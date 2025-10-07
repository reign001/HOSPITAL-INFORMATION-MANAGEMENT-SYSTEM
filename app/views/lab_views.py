from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import LabVisit, LabRequest
from app.forms import LabVisitForm
from decorators import role_required

lab_bp = Blueprint("lab", __name__, url_prefix="/lab")


# ✅ Lab homepage (add new visit + show list + totals)
@lab_bp.route("/", methods=["GET", "POST"])
# @role_required()
def lab_index():
    form = LabVisitForm()
    if form.validate_on_submit():
        visit = LabVisit(
            patient_name=form.patient_name.data,
            patient_surname=form.patient_surname.data,
            patient_age=form.patient_age.data,
            sex=form.sex.data,
            nhis_status=form.nhis_status.data,
            inpatient_status=form.inpatient_status.data,
            phone_number=form.phone_number.data,
            sample=form.sample.data,
            referring_physician=form.referring_physician.data,
            laboratory_number=form.laboratory_number.data,
            investigations=form.investigations.data,
            amount_paid=form.amount_paid.data,
            created_at=datetime.utcnow()
        )
        db.session.add(visit)
        db.session.commit()
        flash("Lab visit added successfully!", "success")
        return redirect(url_for("lab.lab_index"))

    # Get all visits
    visits = LabVisit.query.order_by(LabVisit.created_at.desc()).all()

    # Current date
    today = datetime.utcnow().date()

    # Daily total
    daily_total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) == today
    ).scalar() or 0

    # Monthly total
    monthly_total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.extract("year", LabVisit.created_at) == today.year,
        func.extract("month", LabVisit.created_at) == today.month
    ).scalar() or 0

    return render_template(
        "lab/lab_index.html",
        form=form,
        visits=visits,
        daily_total=daily_total,
        monthly_total=monthly_total,
        today=today  # ✅ Pass to template
    )


# ✅ Detail page for a single lab visit
@lab_bp.route("/<int:visit_id>")
# @role_required()
def lab_detail(visit_id):
    visit = LabVisit.query.get_or_404(visit_id)
    return render_template("lab/lab_detail.html", visit=visit)


# ✅ Delete a lab visit
@lab_bp.route("/delete/<int:visit_id>", methods=["POST"])
# @role_required()
def delete_lab_visit(visit_id):
    visit = LabVisit.query.get_or_404(visit_id)
    db.session.delete(visit)
    db.session.commit()
    flash("Lab visit deleted successfully!", "danger")
    return redirect(url_for("lab.lab_index"))

@lab_bp.route("/laboratory")
def laboratory_view():
    requests = LabRequest.query.filter_by(is_completed=False).all()
    return render_template("lab/requests.html", requests=requests)