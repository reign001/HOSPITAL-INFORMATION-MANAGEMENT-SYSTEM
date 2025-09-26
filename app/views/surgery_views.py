from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import OperationDiary
from datetime import datetime
from flask import flash
from app.models import Patient
from decorators import role_required

surgery_bp = Blueprint("surgery", __name__, url_prefix="/surgery")

# Add new surgery record
@surgery_bp.route("/add", methods=["GET", "POST"])
def add_surgery():
    if request.method == "POST":
        patient_name = request.form["patient_name"].strip()
        surname=request.form["surname"]
        patient_age=request.form["age"]
        patient_sex = request.form["patient_sex"].capitalize()  # ensure enum matches
        hospital_number = request.form["hospital_number"].strip()

        # Validate enum
        if patient_sex not in ["Male", "Female", "Other"]:
            flash("Invalid sex value. Choose Male, Female, or Other.", "danger")
            return redirect(url_for("surgery.add_surgery"))

        # Try to find existing patient
        patient = Patient.query.filter_by(first_name=patient_name, hospital_number=hospital_number).first()
        if not patient:
            # If patient does not exist, create new patient
            patient = Patient(
                first_name=patient_name,
                surname=request.form["surname"],
                hospital_number=hospital_number,
                sex=patient_sex.capitalize(),
                age=patient_age
            )
            db.session.add(patient)
            db.session.commit()  # commit to get patient.id

        # Create surgery record
        surgery = OperationDiary(
            patient_id=patient.id,
            patient_name=patient_name,
            surname=surname,
            hospital_number=hospital_number,
            patient_sex=patient_sex.capitalize(),
            patient_age=patient_age,
            diagnosis=request.form.get("diagnosis"),
            surgery_done=request.form.get("surgery_done"),
            findings=request.form.get("findings"),
            estimated_blood_loss=request.form.get("estimated_blood_loss"),
            anesthesia_type=request.form.get("anesthesia_type"),
            surgeon_name=request.form.get("surgeon_name"),
            assistant_name=request.form.get("assistant_name"),
            anaesthetist_name=request.form.get("anaesthetist_name"),
            duration_minutes=request.form.get("duration_minutes"),
            post_op_condition=request.form.get("post_op_condition"),
            notes=request.form.get("notes"),
            start_time=datetime.strptime(request.form["start_time"], "%Y-%m-%d")
        )

        db.session.add(surgery)
        db.session.commit()
        flash("Surgery record added successfully!", "success")
        return redirect(url_for("surgery.history"))

    return render_template("surgery/surgery_record.html")

# Update surgery record

@surgery_bp.route("/update/<int:surgery_id>", methods=["POST"])
def update_surgery(surgery_id):
    surgery = OperationDiary.query.get_or_404(surgery_id)
    for field in request.form:
        setattr(surgery, field, request.form[field])
    db.session.commit()
    return redirect(url_for("surgery.history"))

# Surgical history with search + summary

@surgery_bp.route("/history")
def history():
    q = request.args.get("q")
    query = OperationDiary.query

    if q:
        query = query.filter(
            OperationDiary.patient_name.ilike(f"%{q}%") |
            OperationDiary.hospital_number.ilike(f"%{q}%")
        )

    # Retrieve the 'patient_sex' parameter from the request
    patient_sex = request.args.get("patient_sex", "").capitalize()

    # Validate and filter by 'patient_sex' if provided
    if patient_sex in ['Male', 'Female', 'Other']:
        query = query.filter(OperationDiary.patient_sex == patient_sex)

    # Execute the query
    surgeries = query.all()

    # Monthly & yearly stats
    now = datetime.utcnow()
    monthly_total = OperationDiary.query.filter(
        db.extract("year", OperationDiary.start_time) == now.year,
        db.extract("month", OperationDiary.start_time) == now.month
    ).count()
    yearly_total = OperationDiary.query.filter(
        db.extract("year", OperationDiary.start_time) == now.year
    ).count()

    return render_template(
        "surgery/history.html", surgeries=surgeries, monthly_total=monthly_total, yearly_total=yearly_total)



@surgery_bp.route('/history/<int:id>')
def details(id):
    op = OperationDiary.query.get_or_404(id)
    return render_template('surgery/details.html', op=op)