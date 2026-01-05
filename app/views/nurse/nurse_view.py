from flask import Blueprint, render_template, redirect, request, url_for, flash, jsonify, abort
from app.models.lab import LabRequest
from app.models.message import Message
from app import db
from datetime import datetime
from app.models.medications import MedicationAdministration
from app.models.medications import ActiveMedication
from app.models.medications import get_active_medications
from datetime import datetime
from app.models.patients import Patient, PatientCard, PatientNote
from app.models.patients import get_patient_note
from app.models.nurse import Task, NurseNote
from sqlalchemy import func
from flask_login import current_user
from datetime import timedelta







nurse_bp = Blueprint("nurse", __name__, url_prefix="/nurse")



current_time = datetime.now().strftime("%I:%M %p")
from flask_login import login_required, current_user

@nurse_bp.route("/dashboard")
def dashboard():
    """Nurse dashboard showing summary and pending medication alerts."""

    # Allow both nurses and admins
    allowed_roles = ["nurse", "admin", "doctor"]
    if not hasattr(current_user, "role") or current_user.role.name.lower() not in allowed_roles:
        flash("Access denied: Only nurses and admins can access this page.", "danger")
        return redirect(url_for("auth.login"))

    now = datetime.now()

    # 1️⃣ Fetch all patients visible to nurse
    patients = Patient.query.filter_by(visible_to_nurse=True, is_pending=True).all()

    # 2️⃣ Count upcoming medications in the next 30 mins
    upcoming_meds = ActiveMedication.query.filter(
        ActiveMedication.scheduled_time.isnot(None),
        ActiveMedication.scheduled_time > now,
        ActiveMedication.scheduled_time <= now + timedelta(minutes=30),
        ActiveMedication.administered == False
    ).count()

    # 3️⃣ Get pending (overdue) medications
    pending_meds = (
        ActiveMedication.query
        .join(Patient, Patient.id == ActiveMedication.patient_id)
        .filter(
            ActiveMedication.scheduled_time.isnot(None),
            ActiveMedication.scheduled_time < now,
            ActiveMedication.administered == False,
            Patient.visible_to_nurse == True
        )
        .all()
    )
    pending_medications_count = len(pending_meds)

    # 4️⃣ Vital alerts
    vitals_alert = (
        PatientCard.query.filter(
            (PatientCard.heart_rate < 50) |
            (PatientCard.heart_rate > 120) |
            (PatientCard.blood_pressure == "Abnormal") |
            (PatientCard.temperature > 38)
        ).count()
    )

    # 5️⃣ Pending lab requests
    pending_lab = LabRequest.query.filter_by(status="pending").count()

    # 6️⃣ Nurse inbox: unread messages
    unread_count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()

    return render_template(
        "nurse/dashboard.html",
        upcoming_meds=upcoming_meds,
        pending_medications_count=pending_medications_count,
        pending_lab=pending_lab,
        patients=patients,
        vitals_alert=vitals_alert,
        unread_count=unread_count,
        current_time=now
    )







@nurse_bp.route("/patients")
def list_patients():
    """List patients that have been submitted (visible_to_nurse=True)."""
    patients = (
        Patient.query
        .filter_by(visible_to_nurse=True)
        .order_by(Patient.created_at.desc())
        .all()
    )
    return render_template("nurse/patients_list.html", patients=patients)



@nurse_bp.route("/patient/<int:patient_id>/edit_vitals", methods=["GET", "POST"])
def edit_vitals(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    card = patient.cards[-1] if patient.cards else None

    if request.method == "POST":
        card.blood_pressure = request.form.get("blood_pressure")
        card.heart_rate = request.form.get("heart_rate") or None
        card.respiratory_rate = request.form.get("respiratory_rate") or None
        card.temperature = request.form.get("temperature") or None
        card.oxygen_saturation = request.form.get("oxygen_saturation")
        card.weight = request.form.get("weight") or None
        card.height = request.form.get("height") or None
        if card.weight and card.height:
            card.bmi = round(card.weight / ((card.height/100)**2), 2)
        card.last_updated = datetime.utcnow()
        db.session.commit()
        flash("Vitals updated", "success")
        return redirect(url_for("nurse.patient_card", patient_id=patient.id))

    return render_template("nurse/edit_vitals.html", patient=patient, card=card)

@nurse_bp.route("/patient/<int:patient_id>")
def patient_card(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    active_medications = get_active_medications(patient.id)  # function to fetch active meds
    patient_notes = get_patient_note(patient.id)            # function to fetch notes
    return render_template(
        "patients/patient_card.html",
        patient=patient,
        active_medications=active_medications,
        patient_notes=patient_notes
    )

@nurse_bp.route("/medication/<int:med_id>/administer", methods=["POST"])
def mark_administered(med_id):
    med = MedicationAdministration.query.get_or_404(med_id)
    med.administered = True
    db.session.commit()
    flash("Medication marked as administered", "success")
    return redirect(request.referrer)


@nurse_bp.route("/tasks")
def tasks():
    # Example: fetch nurse-specific tasks and notes
    # Replace with your actual models
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    notes = PatientNote.query.filter_by(nurse_id=current_user.id).all()
    return render_template("nurse/tasks.html", tasks=tasks, notes=notes)


@nurse_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """
    Nurse profile settings: view and update their profile.
    """
    nurse = current_user  # current logged-in nurse

    if request.method == "POST":
        # Update nurse profile
        nurse.first_name = request.form.get("first_name", nurse.first_name)
        nurse.surname = request.form.get("surname", nurse.surname)
        nurse.email = request.form.get("email", nurse.email)
        nurse.phone_number = request.form.get("phone_number", nurse.phone_number)
        
        try:
            db.session.commit()
            flash("Profile updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")

        return redirect(url_for("nurse.settings"))

    return render_template("nurse/settings.html", nurse=nurse)


@nurse_bp.route("/search", methods=["GET"])
def search():
    """
    Nurse search for patients from dashboard.
    """
    query = request.args.get("q", "")  # 'q' is the search input name in the form
    patients = []

    if query:
        # Search by first name, surname, or hospital number
        search_term = f"%{query}%"
        patients = Patient.query.filter(
            db.or_(
                Patient.first_name.ilike(search_term),
                Patient.surname.ilike(search_term),
                Patient.hospital_number.ilike(search_term)
            )
        ).all()

    return render_template("nurse/search_results.html", patients=patients, query=query)

@nurse_bp.route("/patients/<int:patient_id>/add_notes", methods=["GET", "POST"])
def add_notes(patient_id):
    """Allow nurse to add notes for a patient."""
    patient = Patient.query.get_or_404(patient_id)

    if request.method == "POST":
        note_content = request.form.get("note")
        if note_content:
            new_note = NurseNote(
                patient_id=patient.id,
                nurse_id=current_user.id,
                content=note_content,
                created_at=datetime.utcnow()
            )
            db.session.add(new_note)
            db.session.commit()
            flash("Note added successfully!", "success")
            return redirect(url_for('nurse.dashboard'))

    return render_template("nurse/add_notes.html", patient=patient)


@nurse_bp.route("/mark_done/<int:patient_id>", methods=["POST"])
def mark_done(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_pending = False
    db.session.commit()
    return jsonify({"success": True, "patient_id": patient_id})

@nurse_bp.route("/inbox")
def inbox():
    messages = (
        Message.query
        .filter_by(receiver_id=current_user.id)
        .order_by(Message.created_at.desc())
        .all()
    )

    return render_template("nurse/inbox.html", messages=messages)


@nurse_bp.route("/message/<int:message_id>")
def read_message(message_id):
    msg = Message.query.get_or_404(message_id)

    # Ensure the logged-in user is the receiver
    if msg.receiver_id != current_user.id:
        abort(403)

    # Mark as read
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()

    return render_template("nurse/read_message.html", msg=msg)


@nurse_bp.route("/message/<int:message_id>/reply", methods=["GET", "POST"])
def reply_message(message_id):
    original = Message.query.get_or_404(message_id)

    if request.method == "POST":
        content = request.form.get("content")

        reply = Message(
            sender_id=current_user.id,
            receiver_id=original.sender_id,
            subject=f"RE: {original.subject}",
            content=content,
            is_read=False
        )

        db.session.add(reply)
        db.session.commit()

        flash("Reply sent!", "success")
        return redirect(url_for('nurse.inbox'))

    return render_template("nurse/reply.html", original=original)

