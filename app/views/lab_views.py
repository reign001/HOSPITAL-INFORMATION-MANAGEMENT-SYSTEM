from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import LabVisit, LabRequest, Patient
from app.forms import LabVisitForm
from app.views.doctor_views import doctor_bp
from decorators import role_required

lab_bp = Blueprint("lab", __name__, url_prefix="/lab")


# ✅ Lab homepage (add new visit + show list + totals)
@lab_bp.route("/", methods=["GET", "POST"])
# ✅ Lab homepage (add new visit + show list + totals)
@lab_bp.route("/", methods=["GET", "POST"])
def lab_index():
    form = LabVisitForm()
    patient = Patient.query.first()

    # -------------------------------
    # ✅ Handle form submission (create new LabVisit)
    # -------------------------------
    if form.validate_on_submit():
        # Try to find patient by ID or name
        patient = None
        if hasattr(form, "patient_id") and form.patient_id.data:
            patient = Patient.query.get(form.patient_id.data)
        else:
            patient = Patient.query.filter_by(
                first_name=form.patient_name.data.strip(),
                surname=form.patient_surname.data.strip()  # ✅ use 'surname', not 'last_name'
            ).first()

        if not patient:
            flash("⚠️ Patient not found. Please register the patient first.", "warning")
            return redirect(url_for("patient.register"))

        # Create new LabVisit
        visit = LabVisit(
            patient_id=patient.id,
            patient_name=patient.first_name,
            patient_surname=patient.surname,
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
        flash("✅ Lab visit added successfully!", "success")
        return redirect(url_for("lab.lab_index"))

    # -------------------------------
    # ✅ Handle GET request
    # -------------------------------

    # Retrieve pending lab requests
    pending_requests = LabRequest.query.filter_by(status="Pending").order_by(LabRequest.created_at.desc()).all()

    if pending_requests:
        # ✅ If there are pending requests → render request page directly
        return render_template("lab/request.html", requests=pending_requests)

    # ✅ Otherwise → show the default lab_index.html page
    visits = LabVisit.query.order_by(LabVisit.created_at.desc()).all()

    today = datetime.utcnow().date()

    # ✅ Daily total
    daily_total = db.session.query(func.sum(LabVisit.amount_paid)).filter(
        func.date(LabVisit.created_at) == today
    ).scalar() or 0

    # ✅ Monthly total
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
        today=today,
        patient=patient
    )




@lab_bp.route("/<int:visit_id>/<int:request_id>")
def lab_detail(visit_id, request_id):
    lab_visit = LabVisit.query.get(visit_id)
    lab_request = LabRequest.query.get(request_id)

    print("Showing details for visit:", visit_id, "and request:", request_id)

    # ✅ If either record is missing, show a proper message instead of redirecting
    if not lab_visit or not lab_request:
        flash("⚠️ Could not find that lab record.", "warning")
        return redirect(url_for("lab.lab_index"))

    # ✅ Avoid endless redirect loop — always render the template here
    return render_template(
        "lab/lab_detail.html",
        visit=lab_visit,
        lab_request=lab_request
    )



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

@lab_bp.route("/doctor/patient/<int:patient_id>/lab", methods=["GET", "POST"])
def lab_requests(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    pending_requests = LabRequest.query.filter_by(status="Pending").order_by(LabRequest.created_at.desc()).all()
    if request.method == "POST":
        tests = request.form.get("tests")

        # ✅ 1. Try to find an existing visit for this patient
        visit = LabVisit.query.filter_by(patient_name=patient.first_name).order_by(LabVisit.created_at.desc()).first()

        # ✅ 2. If no existing visit, create one automatically
        if not visit:
            visit = LabVisit(
                patient_name=patient.first_name,
                patient_id=patient.id,
                patient_surname=patient.last_name,
                patient_age=patient.age,
                sex=patient.sex,
                nhis_status=patient.nhis_status if hasattr(patient, "nhis_status") else "N/A",
                inpatient_status="Outpatient",
                phone_number=patient.phone_number,
                referring_physician=current_user.full_name if hasattr(current_user, "full_name") else "Doctor",
                laboratory_number=None,
                investigations=tests,
                amount_paid=0,
                created_at=datetime.utcnow()
            )
            db.session.add(visit)
            db.session.flush()  # ensures visit.id is available before commit

        # ✅ 3. Create the lab request linked to the visit
        lab_request = LabRequest(
            patient_id=patient.id,
            doctor_id=current_user.id,
            tests_requested=tests,
            visit_id=visit.id
        )
        db.session.add(lab_request)
        db.session.commit()

        flash("Lab request successfully created!", "success")
        return redirect(url_for("lab.lab_detail", visit_id=visit.id))  # ✅ Always safe now!

    return render_template("lab/request.html", patient=patient, requests=pending_requests)


@lab_bp.route("/process/<int:request_id>", methods=["GET", "POST"])
def process_lab_request(request_id):
    lab_request = LabRequest.query.get_or_404(request_id)

    # Auto-create a visit if missing
    if not lab_request.visit_id:
        patient = lab_request.patient
        if not patient:
            flash("⚠️ This lab request has no valid patient record.", "warning")
            return redirect(url_for("lab.lab_index"))

        visit = LabVisit(
            patient_id=patient.id,
            patient_name=patient.first_name,
            patient_surname=patient.surname,
            patient_age=patient.age or 0,
            sex=(patient.sex.value if hasattr(patient.sex, "value") else patient.sex),
            nhis_status=(patient.nhis_status.value if hasattr(patient.nhis_status, "value") else patient.nhis_status),
            phone_number=patient.phone_number,
            investigations=lab_request.tests_requested,
            referring_physician=(lab_request.doctor.username if lab_request.doctor else None),
            laboratory_number=f"LAB-{int(datetime.utcnow().timestamp())}",
            created_at=datetime.utcnow(),
        )
        db.session.add(visit)
        db.session.flush()
        lab_request.visit_id = visit.id
        db.session.commit()

    # Process POST (save result + other fields)
    if request.method == "POST":
        result = request.form.get("result")
        patient_type = request.form.get("patient_type")
        sample_type = request.form.get("sample_type")
        amount_paid = request.form.get("amount_paid")

        if not result:
            flash("⚠️ Please enter a result before submitting.", "warning")
            return redirect(url_for("lab.process_lab_request", request_id=request_id))

        # Save on LabRequest
        lab_request.result = result
        lab_request.patient_type = patient_type
        lab_request.sample_type = sample_type
        # convert amount_paid to numeric if present
        lab_request.amount_paid = float(amount_paid) if amount_paid else None
        lab_request.status = "Completed"
        lab_request.processed_at = datetime.utcnow()

        # Also save on LabVisit
        visit = LabVisit.query.get(lab_request.visit_id) if lab_request.visit_id else None
        if visit:
            visit.result = result
            # use same field names as your model: here I assume LabVisit has patient_type, sample, amount_paid
            visit.patient_type = patient_type
            visit.sample = sample_type  # LabVisit.sample column
            visit.amount_paid = float(amount_paid) if amount_paid else None
            db.session.add(visit)

        db.session.add(lab_request)
        db.session.commit()
        flash("✅ Lab request processed successfully!", "success")

        return redirect(url_for("lab.lab_detail", visit_id=lab_request.visit_id, request_id=request_id))

    # GET -> show form
    return render_template("lab/process_lab_request.html", request=lab_request)


