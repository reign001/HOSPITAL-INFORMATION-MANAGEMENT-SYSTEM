from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.patients import Patient, MedicalHistory, VitalSign, Allergy
from datetime import datetime
from app.models.medications import ActiveMedication
from flask import Blueprint, render_template
from app.models.lab import LabVisit, LabRequest
from app.models.doctor import ClerkingRecord, ClinicalNote
from app.models.message import Message
from app.models.employee import Employee, Role
from datetime import date
from sqlalchemy import func


doctor_bp = Blueprint("doctor", __name__, template_folder="../templates/doctor")

@doctor_bp.route("/dashboard")
@login_required
def dashboard():
    query = request.args.get("q", "").strip()

    # Patients assigned to this doctor
    base_query = Patient.query.filter_by(assigned_doctor_id=current_user.id)
    if query:
        base_query = base_query.filter(
            (Patient.first_name.ilike(f"%{query}%")) |
            (Patient.surname.ilike(f"%{query}%")) |
            (Patient.hospital_number.ilike(f"%{query}%"))
        )

    patients = base_query.filter_by(is_pending=True).order_by(Patient.created_at.desc()).all()

    today_appointments = Patient.query.filter_by(assigned_doctor_id=current_user.id)\
        .filter(db.func.date(Patient.created_at) == date.today()).all()

    active_patients = Patient.query.filter_by(
        assigned_doctor_id=current_user.id, is_pending=True
    ).all()

    # Pending lab requests
    pending_lab_count = db.session.query(db.func.count(LabRequest.id))\
        .join(Patient)\
        .filter(
            Patient.assigned_doctor_id == current_user.id,
            LabRequest.status == "Pending"
        ).scalar()

    # Recent clinical notes
    recent_notes = ClinicalNote.query.join(Patient)\
        .filter(Patient.assigned_doctor_id == current_user.id)\
        .order_by(ClinicalNote.created_at.desc())\
        .limit(5).all()

    latest_visit = LabVisit.query.order_by(LabVisit.id.desc()).first()

    patient_visits = {
        p.id: LabVisit.query.filter_by(patient_id=p.id)
        .order_by(LabVisit.created_at.desc())
        .first()
        for p in patients
    }

    # -------------------------------------------
    # NEW: Message notifications for the doctor
    # -------------------------------------------
    doctor_user_id = f"employee-{current_user.id}"

    # Get only unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=doctor_user_id,
        is_read=False
    ).order_by(Message.created_at.desc()).all()

    # Group by patient
    unread_summary = {}
    for msg in unread_messages:
        if msg.sender_id not in unread_summary:
            unread_summary[msg.sender_id] = []
        unread_summary[msg.sender_id].append(msg)

    # Pass the summary to the template
    # unread_summary = { "patient-3": [msg1, msg2], "patient-7": [msg3] }
    return render_template(
        "doctor/doctor_dashboard.html",
        latest_visit=latest_visit,
        patients=patients,
        today_appointments=today_appointments,
        active_patients=active_patients,
        pending_lab_count=pending_lab_count,
        recent_notes=recent_notes,
        patient_visits=patient_visits,
        query=query,
        unread_summary=unread_summary
    )






@doctor_bp.route("/clerk/<int:patient_id>", methods=["GET", "POST"])
@login_required
def clerk_patient(patient_id):
    """Allows doctor to clerk (record history and examination) for a patient."""
    patient = Patient.query.get_or_404(patient_id)

    # Fetch vitals
    vitals = (
        VitalSign.query
        .filter_by(patient_id=patient.id)
        .order_by(VitalSign.date_recorded.desc())
        .all()
    )

    # Fetch latest general medical history (basic background)
    basic_history = (
        MedicalHistory.query
        .filter_by(patient_id=patient.id)
        .order_by(MedicalHistory.created_at.desc())
        .first()
    )

    # Fetch allergies for this patient
    allergies = (
        Allergy.query
        .filter_by(patient_id=patient.id)
        .order_by(Allergy.id.desc())
        .all()
    )

    # Fetch most recent clerking record by this doctor
    existing_history = (
        MedicalHistory.query
        .filter_by(patient_id=patient.id, created_by=current_user.id)
        .order_by(MedicalHistory.created_at.desc())
        .first()
    )

    # Fetch latest lab request for this patient
    latest_lab_request = (
        LabRequest.query
        .filter_by(patient_id=patient.id)
        .order_by(LabRequest.created_at.desc())
        .first()
    )

    # Handle form submission
    if request.method == "POST":
        presenting_complaint = request.form.get("presenting_complaint")
        history_of_presenting_complaint = request.form.get("history_of_presenting_complaint")
        past_medical_history = request.form.get("past_medical_history")
        drug_history = request.form.get("drug_history")
        family_history = request.form.get("family_history")
        social_history = request.form.get("social_history")
        examination_findings = request.form.get("examination_findings")
        provisional_diagnosis = request.form.get("provisional_diagnosis")
        plan = request.form.get("plan")

        if existing_history:
            existing_history.presenting_complaint = presenting_complaint
            existing_history.history_of_presenting_complaint = history_of_presenting_complaint
            existing_history.past_medical_history = past_medical_history
            existing_history.drug_history = drug_history
            existing_history.family_history = family_history
            existing_history.social_history = social_history
            existing_history.examination_findings = examination_findings
            existing_history.provisional_diagnosis = provisional_diagnosis
            existing_history.plan = plan
            existing_history.updated_at = datetime.utcnow()
            flash("Existing clerking record updated successfully!", "success")
        else:
            new_history = ClerkingRecord(
                patient_id=patient.id,
                created_by=current_user.id,
                presenting_complaint=presenting_complaint,
                history_of_presenting_complaint=history_of_presenting_complaint,
                past_medical_history=past_medical_history,
                drug_history=drug_history,
                family_history=family_history,
                social_history=social_history,
                examination_findings=examination_findings,
                provisional_diagnosis=provisional_diagnosis,
                plan=plan,
                created_at=datetime.utcnow()
            )
            db.session.add(new_history)
            flash("Patient clerking record saved successfully!", "success")

        db.session.commit()
        return redirect(url_for("patients.patient_summary", patient_id=patient.id))

    # Render the page with latest_lab_request
    return render_template(
        "doctor/clerk_patient.html",
        patient=patient,
        vitals=vitals,
        basic_history=basic_history,
        allergies=allergies,
        history=existing_history,
        latest_lab_request=latest_lab_request  # ✅ Pass to template
    )


@doctor_bp.route("/request_investigation/<int:patient_id>", methods=["GET", "POST"])
@login_required
def request_investigation(patient_id):
    """Allows doctor to request medical investigations for a patient."""
    patient = Patient.query.get_or_404(patient_id)

    # Predefined investigation list
    common_investigations = [
        "Full Blood Count",
        "Urinalysis",
        "Electrolytes, Urea & Creatinine",
        "Liver Function Test",
        "Blood Sugar (FBS/RBS)",
        "Malaria Parasite Test",
        "Widal Test",
        "HIV Screening",
        "Hepatitis Panel",
        "Sputum AFB",
        "Chest X-Ray",
        "ECG",
        "Ultrasound Scan",
        "CT Scan",
        "MRI",
        "Stool Microscopy",
    ]

    if request.method == "POST":
        selected_tests = request.form.getlist("investigations")
        other_test = request.form.get("other_test")
        if other_test:
            selected_tests.append(other_test.strip())

        if not selected_tests:
            flash("Please select or enter at least one investigation.", "warning")
            return redirect(url_for("doctor.request_investigation", patient_id=patient.id))

        tests_str = ", ".join(selected_tests)

        # ✅ Create new LabRequest
        lab_request = LabRequest(
            patient_id=patient.id,
            doctor_id=current_user.id,
            tests_requested=tests_str,
            status="Pending",
        )

        db.session.add(lab_request)
        db.session.commit()

        flash("Investigation request submitted successfully!", "success")

        # ✅ Redirect to clerk page so latest lab request appears immediately
        return redirect(url_for("doctor.clerk_patient", patient_id=patient.id))

    return render_template(
        "doctor/investigation.html",
        patient=patient,
        investigations=common_investigations,
    )



@doctor_bp.route("/prescribe/<int:patient_id>/<string:prescription_type>", methods=["POST"])
@login_required
def prescribe_medication(patient_id, prescription_type):
    """Handles both Admit and Outpatient prescriptions."""
    patient = Patient.query.get_or_404(patient_id)

    medication_name = request.form.get("medication_name")
    dosage = request.form.get("dosage")
    frequency = request.form.get("frequency")
    duration = request.form.get("duration")
    route = request.form.get("route")
    notes = request.form.get("notes")  # optional field if you have it

    if not medication_name or not dosage or not frequency or not duration:
        flash("Please fill all required prescription fields.", "warning")
        return redirect(url_for("doctor.clerk_patient", patient_id=patient.id))

    medication = ActiveMedication(
        patient_id=patient.id,
        drug_name=medication_name.strip(),
        dosage=dosage.strip(),
        frequency=frequency.strip(),
        duration=duration.strip(),
        route=route.strip() if route else None,
        notes=notes,
        prescribed_by_id=current_user,  # ✅ assign to foreign key
        date_prescribed=datetime.utcnow()
    )

    db.session.add(medication)
    db.session.commit()

    flash(f"{prescription_type.capitalize()} prescription added successfully!", "success")
    return redirect(url_for("doctor.clerk_patient", patient_id=patient.id))


from flask import request, jsonify

@doctor_bp.route("/mark_done/<int:patient_id>", methods=["POST"])
def mark_done(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_pending = False
    db.session.commit()

    # Check if it's an AJAX request
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "patient_id": patient_id})
    
    flash(f"{patient.full_name()} has been marked as done.", "success")
    return redirect(url_for("doctor.dashboard"))


@doctor_bp.route("/send_message", methods=["GET", "POST"])
@login_required
def send_message():

    # Fetch all nurses (role = nurse)
    nurses = (
        Employee.query.join(Role)
        .filter(func.lower(Role.name) == "nurse")
        .all()
    )

    if request.method == "POST":
        receiver_id = request.form.get("receiver_id")
        subject = request.form.get("subject")
        content = request.form.get("content")

        # Validation
        if not receiver_id:
            flash("Please select a nurse to send the message to.", "warning")
            return redirect(url_for("doctor.send_message"))

        # Save message
        message = Message(
            sender_id=current_user.id,
            receiver_id=int(receiver_id),
            subject=subject,
            content=content,
            is_read=False
        )

        db.session.add(message)
        db.session.commit()

        flash("Message sent to nursing station!", "success")
        return redirect(url_for("doctor.dashboard"))

    return render_template("doctor/send_message.html", nurses=nurses)


@doctor_bp.route("/check_messages")
@login_required
def check_messages():
    doctor_id = f"employee-{current_user.id}"  # match the string format in Message table
    count = Message.query.filter_by(receiver_id=doctor_id, is_read=False).count()
    return {"unread": count}


@doctor_bp.route("/notifications")
@login_required
def doctor_notifications():
    doctor_id = f"employee-{current_user.id}"  # match the format in the table

    unread = Message.query.filter_by(receiver_id=doctor_id, is_read=False)\
                           .order_by(Message.created_at.desc()).all()

    return jsonify({
        "count": len(unread),
        "messages": [
            {
                "from": msg.sender_id,
                "subject": msg.subject,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in unread
        ]
    })




# GET messages between doctor and patient
@doctor_bp.route("/messages/<int:patient_id>")
@login_required
def get_patient_messages(patient_id):
    doctor_id = f"employee-{current_user.id}"
    patient_user_id = f"patient-{patient_id}"

    messages = Message.query.filter(
        ((Message.sender_id == doctor_id) & (Message.receiver_id == patient_user_id)) |
        ((Message.sender_id == patient_user_id) & (Message.receiver_id == doctor_id))
    ).order_by(Message.created_at.asc()).all()

    messages_list = [
        {
            "sender": "doctor" if msg.sender_id == doctor_id else "patient",
            "content": msg.content,
            "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for msg in messages
    ]

    return jsonify({"messages": messages_list})


# POST: send message from doctor to patient
@doctor_bp.route("/send-message/<int:patient_id>", methods=["POST"])
@login_required
def send_message_to_patient(patient_id):
    data = request.get_json()
    content = data.get("message", "").strip()

    if not content:
        return jsonify({"error": "empty"}), 400

    doctor_id = f"employee-{current_user.id}"
    patient_user_id = f"patient-{patient_id}"

    msg = Message(
        sender_id=doctor_id,
        receiver_id=patient_user_id,
        sender_type="EMPLOYEE",
        receiver_type="PATIENT",
        subject="Doctor Message",
        content=content,
        is_read=False,
        created_at=datetime.utcnow()
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"status": "ok"}), 200


@doctor_bp.route("/chat/<patient_id>")
@login_required
def chat_with_patient(patient_id):
    doctor_id = f"employee-{current_user.id}"
    patient_user_id = f"patient-{patient_id}"

    # Fetch all messages between this doctor and patient
    messages = Message.query.filter(
        ((Message.sender_id == doctor_id) & (Message.receiver_id == patient_user_id)) |
        ((Message.sender_id == patient_user_id) & (Message.receiver_id == doctor_id))
    ).order_by(Message.created_at.asc()).all()

    # Mark messages sent to doctor as read
    for msg in messages:
        if msg.receiver_id == doctor_id and not msg.is_read:
            msg.is_read = True

    db.session.commit()  # ✅ Save the changes

    return render_template("doctor/chat.html", patient_id=patient_id, messages=messages)


from sqlalchemy import and_, or_

@doctor_bp.route("/end-chat/<patient_id>", methods=["POST"])
@login_required
def end_chat(patient_id):
    doctor_id = f"employee-{current_user.id}"
    patient_user_id = f"patient-{patient_id}"

    # Delete only messages between this doctor and this patient
    Message.query.filter(
        or_(
            and_(Message.sender_id == doctor_id, Message.receiver_id == patient_user_id),
            and_(Message.sender_id == patient_user_id, Message.receiver_id == doctor_id)
        )
    ).delete(synchronize_session=False)

    db.session.commit()
    flash("Chat ended. All messages with this patient have been deleted.", "success")
    return redirect(url_for("doctor.dashboard"))





