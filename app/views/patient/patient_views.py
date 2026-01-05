from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.patients import Patient, MedicalHistory, FamilyHistory, SocialHistory, Allergy, Immunization, VitalSign, PatientRequest
from app.models.cards import PatientCard
from app.models.employee import Employee, Role
from app.models.lab import LabRequest, LabResult
from app.models.doctor import ClerkingRecord, ClinicalNote
from app.models.medications import ActiveMedication
from datetime import datetime
from app.models.patients import SexEnum, VitalSign
from app.models.prescriptions import Prescription



patients_bp = Blueprint("patients", __name__, url_prefix="/patients", template_folder="../templates/patients")

# # LIST ALL
# ──────────────────────────────────────────────────────────────
# LIST ALL PATIENTS
# ──────────────────────────────────────────────────────────────
@patients_bp.route("/", methods=["GET"])
def list_patients():
    query = request.args.get("q", "").strip()
    if query:
        patients = Patient.query.filter(
            (Patient.first_name.ilike(f"%{query}%")) |
            (Patient.surname.ilike(f"%{query}%")) |
            (Patient.hospital_number.ilike(f"%{query}%")) |
            (Patient.phone_number.ilike(f"%{query}%")) |
            (Patient.address.ilike(f"%{query}%"))
        ).all()
    else:
        patients = Patient.query.all()
    return render_template("patients/list.html", patients=patients, query=query)

@patients_bp.route("/patients/new", methods=["GET", "POST"])
def new_patient():
    if request.method == "POST":
        hospital_number = generate_hospital_number()  # you can define this utility

        new_patient = Patient(
            hospital_number=hospital_number,
            first_name=request.form.get("first_name"),
            middle_name=request.form.get("middle_name"),
            surname=request.form.get("surname"),
            date_of_birth=request.form.get("date_of_birth"),
            sex=SexEnum.MALE,
            address=request.form.get("address"),
            phone_number=request.form.get("phone_number"),
            email=request.form.get("email"),
            marital_status=request.form.get("marital_status"),
            occupation=request.form.get("occupation"),
            religion=request.form.get("religion"),
            next_of_kin_name=request.form.get("next_of_kin_name"),
            next_of_kin_phone=request.form.get("next_of_kin_phone"),
            next_of_kin_relationship=request.form.get("next_of_kin_relationship"),
            nhis_status=request.form.get("nhis_status"),
        )
        db.session.add(new_patient)
        db.session.commit()


        card = PatientCard(
        patient_id=new_patient.id,
        blood_pressure="",
        heart_rate=None,
        respiratory_rate=None,
        temperature=None,
        oxygen_saturation=None,
        weight=None,
        height=None,
        chief_complaint="",
        history_of_present_illness="",
        past_medical_history="",
        medications="",
        allergies="",
        examination="",
        assessment="",
        plan=""
        )
        db.session.add(card)
        db.session.commit()

        flash("New patient added successfully!", "success")
        return redirect(url_for("patients.list_patients"))

    return render_template("patients/new.html")


def generate_hospital_number():
    """Generate a unique hospital number like '120/25' where 120 is sequence and 25 is year."""
    # current_year = datetime.datetime.now().year % 100
    current_year = datetime.now().year % 100
    # created_at = datetime.utcnow()  # gets '25' for 2025

    # Count existing patients for this year
    count = Patient.query.count() + 1
    hospital_number = f"{count}/{current_year}"

    # Ensure uniqueness
    while Patient.query.filter_by(hospital_number=hospital_number).first():
        count += 1
        hospital_number = f"{count}/{current_year}"

    return hospital_number





@patients_bp.route("/<int:patient_id>")
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    investigations = (
        LabRequest.query
        .filter_by(patient_id=patient.id)
        .order_by(LabRequest.created_at.desc())
        .all()
    )
    return render_template("patients/summary.html", patient=patient, investigations=investigations)


@patients_bp.route("/<int:patient_id>/update_medical_history", methods=["GET", "POST"])
def update_medical_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    # If POST request → update or create record
    if request.method == "POST":
        if not patient.medical_history:
            patient.medical_history = MedicalHistory(patient=patient)

        # Core medical history fields
        patient.medical_history.chronic_conditions = request.form.get("chronic_conditions")
        patient.medical_history.past_surgeries = request.form.get("past_surgeries")
        patient.medical_history.current_medications = request.form.get("current_medications")
        patient.medical_history.allergies = request.form.get("allergies")
        patient.medical_history.immunizations = request.form.get("immunizations")
        patient.medical_history.blood_group = request.form.get("blood_group")
        patient.medical_history.genotype = request.form.get("genotype")
        patient.medical_history.last_updated = datetime.utcnow()

        db.session.commit()
        flash("Medical history updated successfully!", "success")
        return redirect(url_for("patients.patient_detail", patient_id=patient.id))

    return render_template("patients/update_medical_history.html", patient=patient)



# ──────────────────────────────────────────────────────────────
# FAMILY HISTORY ROUTE
# ──────────────────────────────────────────────────────────────
@patients_bp.route("/<int:patient_id>/update_family_history", methods=["GET", "POST"])
# @patients_bp.route("/patients/<int:patient_id>/family_history", methods=["GET", "POST"])
def family_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    history = FamilyHistory.query.filter_by(patient_id=patient.id).first()

    if request.method == "POST":
        if not history:
            history = FamilyHistory(patient_id=patient.id)

        history.diabetes = bool(request.form.get("diabetes"))
        history.hypertension = bool(request.form.get("hypertension"))
        history.cancer = bool(request.form.get("cancer"))
        history.heart_disease = bool(request.form.get("heart_disease"))
        history.sickle_cell = bool(request.form.get("sickle_cell"))
        history.tuberculosis = bool(request.form.get("tuberculosis"))
        history.asthma = bool(request.form.get("asthma"))
        history.stroke = bool(request.form.get("stroke"))
        history.mental_illness = bool(request.form.get("mental_illness"))
        history.other_conditions = request.form.get("other_conditions")

        db.session.add(history)
        db.session.commit()
        flash("Family history updated successfully.", "success")
        return redirect(url_for("patients.patient_summary", patient_id=patient.id))

    return render_template("patients/update_family_history.html", patient=patient, history=history)



# ──────────────────────────────────────────────────────────────
# SOCIAL HISTORY ROUTE
# ──────────────────────────────────────────────────────────────
# @patients_bp.route("/<int:patient_id>/update_social_history", methods=["GET", "POST"])
@patients_bp.route("/patients/<int:patient_id>/social_history", methods=["GET", "POST"])
def update_social_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    history = SocialHistory.query.filter_by(patient_id=patient.id).first()

    if request.method == "POST":
        if not history:
            history = SocialHistory(patient_id=patient.id)

        history.occupation = request.form.get("occupation")
        history.marital_status = request.form.get("marital_status")
        history.alcohol = bool(request.form.get("alcohol"))
        history.smoking = bool(request.form.get("smoking"))
        history.drug_use = bool(request.form.get("drug_use"))
        history.living_conditions = request.form.get("living_conditions")

        db.session.add(history)
        db.session.commit()
        flash("Social history updated successfully.", "success")
        return redirect(url_for("patients.patient_summary", patient_id=patient.id))

    return render_template("patients/update_social_history.html", patient=patient, history=history)



@patients_bp.route("/<int:patient_id>/allergies", methods=["GET", "POST"])
def allergies(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        allergen = request.form.get("allergen")
        reaction = request.form.get("reaction")
        severity = request.form.get("severity")
        date_identified = request.form.get("date_identified")
        recorded_by = request.form.get("recorded_by")

        allergy = Allergy(
            patient_id=patient.id,
            allergen=allergen,
            reaction=reaction,
            severity=severity,
            date_identified=date_identified or None,
            recorded_by=recorded_by
        )
        db.session.add(allergy)
        db.session.commit()
        flash("Allergy added successfully!", "success")
        return redirect(url_for("patients.allergies", patient_id=patient.id))

    allergies_list = Allergy.query.filter_by(patient_id=patient.id).order_by(Allergy.created_at.desc()).all()
    return render_template("patients/allergies.html", patient=patient, allergies_list=allergies_list)


@patients_bp.route("/<int:patient_id>/immunizations", methods=["GET", "POST"])
def immunizations(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        vaccine_name = request.form.get("vaccine_name")
        date_administered = request.form.get("date_administered")
        next_due_date = request.form.get("next_due_date")
        administered_by = request.form.get("administered_by")
        notes = request.form.get("notes")

        if not vaccine_name or not date_administered:
            flash("Vaccine name and date administered are required.", "danger")
            return redirect(url_for("patients.immunizations", patient_id=patient.id))

        immunization = Immunization(
            patient_id=patient.id,
            vaccine_name=vaccine_name,
            date_administered=datetime.strptime(date_administered, "%Y-%m-%d").date(),
            next_due_date=datetime.strptime(next_due_date, "%Y-%m-%d").date() if next_due_date else None,
            administered_by=administered_by,
            notes=notes,
        )
        db.session.add(immunization)
        db.session.commit()

        flash("Immunization record added successfully!", "success")
        return redirect(url_for("patients.immunizations", patient_id=patient.id))

    immunizations = Immunization.query.filter_by(patient_id=patient.id).order_by(Immunization.date_administered.desc()).all()
    return render_template("patients/immunizations.html", patient=patient, immunizations=immunizations)



@patients_bp.route("/<int:patient_id>/vitals", methods=["GET", "POST"])
def vitals(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        def to_number(value):
            import re
            if not value:
                return None
            cleaned = re.sub(r"[^0-9.]", "", value)
            try:
                return int(cleaned) if "." not in cleaned else float(cleaned)
            except ValueError:
                return None

        blood_pressure = request.form.get("blood_pressure")
        heart_rate = to_number(request.form.get("heart_rate"))
        respiratory_rate = to_number(request.form.get("respiratory_rate"))
        temperature = to_number(request.form.get("temperature"))
        weight = to_number(request.form.get("weight"))
        recorded_by = request.form.get("recorded_by")

        vitals = VitalSign(
            patient_id=patient.id,
            blood_pressure=blood_pressure,
            heart_rate=heart_rate,
            respiratory_rate=respiratory_rate,
            temperature=temperature,
            weight=weight,
            recorded_by=recorded_by
        )

        db.session.add(vitals)
        db.session.commit()
        flash("Vital signs recorded successfully!", "success")
        return redirect(url_for("patients.vitals", patient_id=patient.id))

    vitals_list = VitalSign.query.filter_by(patient_id=patient.id).order_by(VitalSign.date_recorded.desc()).all()
    print("Vitals for patient", patient.id, ":", vitals_list)
    return render_template("patients/vitals.html", patient=patient, vitals=vitals_list)



@patients_bp.route("/<int:patient_id>/summary")
def patient_summary(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    # --- 📋 Basic Patient Data ---
    social_history = SocialHistory.query.filter_by(patient_id=patient.id).first()
    family_history = FamilyHistory.query.filter_by(patient_id=patient.id).first()
    vitals = (
        VitalSign.query.filter_by(patient_id=patient.id)
        .order_by(VitalSign.date_recorded.desc())
        .all()
    )
    immunizations = Immunization.query.filter_by(patient_id=patient.id).all()
    allergies = Allergy.query.filter_by(patient_id=patient.id).all()
    vital_signs = vitals

    # --- 👨‍⚕️ Doctors List (for Queueing etc) ---
    doctors = (
        Employee.query.join(Employee.role)
        .filter(Role.name == "Doctor")
        .all()
    )

    # --- 🔬 Lab Investigations ---
    investigations = (
        LabRequest.query
        .filter_by(patient_id=patient.id)
        .order_by(LabRequest.created_at.desc())
        .options(db.joinedload(LabRequest.results))
        .all()
    )

    lab_results = (
        LabResult.query.join(LabRequest, LabResult.lab_request_id == LabRequest.id)
        .filter(LabRequest.patient_id == patient.id)
        .order_by(LabResult.created_at.desc())
        .all()
    )

    # --- 🧠 Diagnoses (Clerking + Clinical Notes) ---
    clerking_diagnoses = ClerkingRecord.query.filter_by(patient_id=patient.id).all()
    clinical_notes = ClinicalNote.query.filter_by(patient_id=patient.id).all()

    diagnoses = []
    for c in clerking_diagnoses:
        if c.provisional_diagnosis:
            diagnoses.append({
                "date": c.created_at,
                "diagnosis": c.provisional_diagnosis,
                "doctor": Employee.query.get(c.created_by)
            })
    for note in clinical_notes:
        if note.diagnosis:
            diagnoses.append({
                "date": note.created_at,
                "diagnosis": note.diagnosis,
                "doctor": note.doctor
            })
    diagnoses = sorted(diagnoses, key=lambda d: d["date"], reverse=True)


# --- 💊 Medications (Prescribed by Doctors) ---
    prescriptions = ActiveMedication.query.filter(
    ActiveMedication.patient_id == patient.id,
    ActiveMedication.prescribed_by_id.isnot(None)
).order_by(ActiveMedication.date_prescribed.desc()).all()

    # Administrations (doses given by nurses)
    administrations = ActiveMedication.query.filter(
    ActiveMedication.patient_id == patient.id,
    ActiveMedication.nurse_id.isnot(None)
    ).all()


    charts = (
    ActiveMedication.query
    .filter(ActiveMedication.patient_id == patient.id,
            ActiveMedication.scheduled_time.isnot(None))
    .order_by(ActiveMedication.scheduled_time.asc())
    .all()
)
    

    administrations = (
    ActiveMedication.query
    .filter(ActiveMedication.patient_id == patient.id,
            ActiveMedication.administered.is_(True))
    .order_by(ActiveMedication.date_administered.desc())
    .all()
) 
    # --- 🧾 Render Page ---
    return render_template(
        "patients/summary.html",
        patient=patient,
        social_history=social_history,
        family_history=family_history,
        vitals=vitals,
        datetime=datetime,
        immunizations=immunizations,
        vital_signs=vital_signs,
        allergies=allergies,
        doctors=doctors,
        investigations=investigations,
        lab_results=lab_results,
        diagnoses=diagnoses,
        prescriptions=prescriptions,
        administrations=administrations,
        charts=charts
    )




from flask import render_template, make_response
from datetime import datetime

from flask import make_response, send_file
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime

@patients_bp.route("/patients/<int:patient_id>/download_summary_pdf")
def download_summary_pdf(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    vitals = VitalSign.query.filter_by(patient_id=patient_id).order_by(VitalSign.date_recorded).all()
    allergies = Allergy.query.filter_by(patient_id=patient_id).all()
    immunizations = Immunization.query.filter_by(patient_id=patient_id).all()
    family_history = FamilyHistory.query.filter_by(patient_id=patient_id).first()
    social_history = SocialHistory.query.filter_by(patient_id=patient_id).first()

    # Render the HTML template for PDF
    rendered_html = render_template(
        "patients/print_summary.html",
        patient=patient,
        vitals=vitals,
        allergies=allergies,
        immunizations=immunizations,
        family_history=family_history,
        social_history=social_history,
        generated_on=datetime.utcnow()
    )

    # Convert HTML to PDF in memory
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered_html, dest=pdf)
    pdf.seek(0)

    if pisa_status.err:
        return f"Error generating PDF: {pisa_status.err}"

    # Send PDF as downloadable file
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"{patient.full_name()}_summary.pdf",
        mimetype="application/pdf"
    )


@patients_bp.route('/by-year/<int:year>')
def patients_by_year(year):
    from app.models.patients import Patient
    patients = Patient.query.filter(db.extract('year', Patient.created_at) == year).all()
    return render_template('patients/list_by_year.html', patients=patients, year=year)

@patients_bp.route('/yearly-summary/<int:year>')
def yearly_summary(year):
    patients = Patient.query.filter(db.extract('year', Patient.created_at) == year).all()
    return render_template('patients/yearly_summary.html', patients=patients, year=year)


@patients_bp.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        # Personal Info
        patient.first_name = request.form["first_name"]
        patient.surname = request.form["surname"]
        patient.other_names = request.form.get("other_names")
        patient.date_of_birth = request.form.get("date_of_birth")
        patient.sex = request.form.get("sex").upper()
        patient.marital_status = request.form.get("marital_status")
        patient.occupation = request.form.get("occupation")
        patient.religion = request.form.get("religion")
    

        # Contact Info
        patient.address = request.form.get("address")
        patient.phone_number = request.form.get("phone_number")
        patient.email = request.form.get("email")

        # Next of Kin
        patient.next_of_kin_name = request.form.get("next_of_kin_name")
        patient.next_of_kin_phone = request.form.get("next_of_kin_phone")
        patient.next_of_kin_relationship = request.form.get("next_of_kin_relationship")

        # NHIS
        patient.nhis_status = request.form.get("nhis_status")
        

        # Commit changes
        db.session.commit()
        flash("Patient details updated successfully!", "success")
        return redirect(url_for("patients.list_patients"))

    return render_template("patients/edit_patient.html", patient=patient)


@patients_bp.route("/delete/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    try:
        # Option 1: delete all related patient cards first
        for card in patient.cards:
            db.session.delete(card)

        # Then delete the patient
        db.session.delete(patient)
        db.session.commit()
        flash("Patient and related records deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting patient: {e}", "danger")

    return redirect(url_for("patients.list_patients"))

@patients_bp.route("/patients/<int:patient_id>/update", methods=["GET", "POST"])
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        patient.first_name = request.form["first_name"]
        patient.surname = request.form["surname"]
        patient.middle_name = request.form.get("middle_name")
        # Update any other patient fields here...

        db.session.commit()
        flash("Patient record updated successfully!", "success")
        return redirect(url_for("patients.patient_summary", patient_id=patient.id))

    return render_template("patients/update_patient.html", patient=patient)


from flask import Blueprint, redirect, url_for, flash, request

from flask_login import current_user, login_required

@patients_bp.post("/patients/<int:patient_id>/submit_to_nurse")
def submit_to_nurse(patient_id):
    """Make folder visible to nurses."""
    patient = Patient.query.get_or_404(patient_id)
    patient.visible_to_nurse = True
    patient.is_pending = True  # ✅ Mark as pending for nurse
    db.session.commit()
    flash(f"{patient.full_name()} is now visible on nurses’ dashboard.", "success")
    return redirect(url_for('patients.patient_summary', patient_id=patient_id))

@patients_bp.route("/patients/<int:patient_id>/add_ward", methods=["POST"])
@login_required
def add_ward(patient_id):
    """Assign or update the ward for a patient."""
    patient = Patient.query.get_or_404(patient_id)
    ward_name = request.form.get("ward_name")

    if ward_name:
        patient.ward = ward_name
        db.session.commit()
        flash(f"Ward '{ward_name}' added for {patient.full_name()}.", "success")
    else:
        flash("Ward name cannot be empty.", "danger")

    return redirect(url_for("patients.patient_summary", patient_id=patient_id))


@patients_bp.post("/patients/<int:patient_id>/queue_to_doctor/<int:doctor_id>")
def queue_to_doctor(patient_id, doctor_id):
    patient = Patient.query.get_or_404(patient_id)
    doctor = Employee.query.get_or_404(doctor_id)

    if doctor.role.name.lower() != "doctor":
        flash("Selected employee is not a doctor.", "danger")
        return redirect(url_for('patients.patient_summary', patient_id=patient_id))

    patient.created_at = datetime.utcnow()
    patient.assigned_doctor_id = doctor.id
    patient.is_pending = True
    patient.is_active = True
    db.session.commit()

    # 🔍 TEMPORARY DEBUG
    print(f"✅ Queued {patient.full_name()} -> Doctor ID: {doctor.id}, is_pending: {patient.is_pending}")

    flash(f"{patient.full_name()} has been queued to Dr. {doctor.full_name()}.", "success")
    return redirect(url_for('patients.patient_summary', patient_id=patient_id))


# Route to delete the chart (all administered medications)
@patients_bp.route("/<int:patient_id>/delete_chart", methods=["POST"])
@login_required
def delete_chart(patient_id):
    """Deletes all administered medications for a patient and clears ward on discharge."""
    patient = Patient.query.get_or_404(patient_id)

    # 🧾 Delete all administered medications
    ActiveMedication.query.filter_by(patient_id=patient.id, administered=True).delete()

    # 🧹 Clear ward assignment (treated as discharge)
    patient.ward = None
    db.session.commit()

    flash("Medication chart deleted and ward cleared successfully!", "success")
    return redirect(url_for("patients.patient_summary", patient_id=patient.id))




from flask import request, jsonify, flash, redirect, url_for


@patients_bp.route("/<int:patient_id>/chart-medications", methods=["POST"])
@login_required
def chart_medications(patient_id):
    """Handles both new chart creation and AJAX update for administered medications."""
    patient = Patient.query.get_or_404(patient_id)

    # ✅ If this is an AJAX request marking medication as 'given'
    med_id = request.args.get("med_id") or request.form.get("med_id")
    if med_id:
        medication = ActiveMedication.query.get_or_404(med_id)
        medication.administered = True
        medication.date_administered = datetime.utcnow()
        medication.nurse_id = current_user.id
        db.session.commit()
        return jsonify(success=True, time=medication.date_administered.strftime("%I:%M %p"))

    # ✅ Otherwise, it’s a normal chart creation from nurse form
    drug_names = request.form.getlist("drug_name[]")
    doses = request.form.getlist("dose_given[]")
    routes = request.form.getlist("route[]")
    scheduled_times = request.form.getlist("scheduled_time[]")

    for i in range(len(drug_names)):
        if not drug_names[i].strip():
            continue  # skip empty rows

        med = ActiveMedication(
            patient_id=patient.id,
            drug_name=drug_names[i].strip(),
            dose_given=doses[i].strip() if doses[i] else None,
            route=routes[i].strip() if routes[i] else None,
            scheduled_time=datetime.strptime(scheduled_times[i], "%Y-%m-%dT%H:%M"),
            prescribed_by_id=current_user.id,
            administered=False  # initially not given
        )
        db.session.add(med)

    db.session.commit()
    flash("Medications charted successfully!", "success")
    return redirect(url_for("patients.patient_summary", patient_id=patient.id))


@patients_bp.route("/submit-request", methods=["POST"])
@login_required
def submit_request():
    data = request.get_json()
    request_type = data.get("request_type")
    details = data.get("details", "")

    # Save to the database
    patient_request = PatientRequest(
        patient_id=current_user.id,
        request_type=request_type,
        details=details,
        created_at=datetime.utcnow()
    )

    db.session.add(patient_request)
    db.session.commit()

    return jsonify({"status": "ok"})
