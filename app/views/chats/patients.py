from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.employee import Employee
from app.models.patients import Patient
from app.models.message import Message
from flask import abort
from sqlalchemy import func
from app.models.employee import Employee, Role




patients_chat_bp = Blueprint("patient_chat", __name__, url_prefix="/chats/patients")


def patient_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, "hospital_number"):
            flash("Access denied.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function



@patients_chat_bp.route("/dashboard")
@login_required
def dashboard():
    if not str(current_user.get_id()).startswith("patient-"):
        abort(403)
    return render_template("patient/dashboard.html", patient=current_user)





@patients_chat_bp.route("/inbox")
@patient_required
def inbox():
    patient = current_user
    pid = str(patient.id)

    messages = Message.query.filter(
        (Message.sender_id == pid) | (Message.receiver_id == pid)
    ).order_by(Message.created_at.desc()).all()

    return render_template("patient/inbox.html", messages=messages)


@login_required
@patient_required
@patients_chat_bp.route("/select_doctor")
def select_doctor():
    # Query all active employees with role 'doctor'
    doctors = (
        Employee.query
        .join(Role, Employee.role_id == Role.id)
        .filter(Role.name.ilike("doctor"), Employee.is_active.is_(True))
        .all()
    )

    # Pass the list of Employee objects to the template
    return render_template("patient/select_doctor.html", doctors=doctors)



@patients_chat_bp.route("/chat/<doctor_id>")
@login_required
@patient_required
def chat(doctor_id):
    patient = current_user

    # Ensure IDs are strings
    doctor_id = str(doctor_id)
    patient_id = str(patient.id)

    doctor = Employee.query.get_or_404(doctor_id)

    # Fetch all messages between patient and this doctor
    messages = Message.query.filter(
        ((Message.sender_id == patient_id) & (Message.receiver_id == doctor_id)) |
        ((Message.sender_id == doctor_id) & (Message.receiver_id == patient_id))
    ).order_by(Message.created_at.asc()).all()

    # Mark doctor → patient messages as read
    for msg in messages:
        if msg.receiver_id == patient_id and not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template("patient/chat.html", doctor=doctor, messages=messages)


@patients_chat_bp.route("/load-messages/<int:doctor_id>")
@login_required
@patient_required
def load_messages(doctor_id):
    patient = current_user

    # Convert IDs to the new string-based format
    patient_id = f"patient-{patient.id}"
    doctor_uid = f"employee-{doctor_id}"

    # Query for all messages between patient and doctor
    messages = Message.query.filter(
        ((Message.sender_id == patient_id) & (Message.receiver_id == doctor_uid)) |
        ((Message.sender_id == doctor_uid) & (Message.receiver_id == patient_id))
    ).order_by(Message.created_at.asc()).all()

    # Build HTML response
    html = ""
    for m in messages:
        sender_name = (
            "You" if m.sender_id == patient_id else "Doctor"
        )

        bubble_class = (
            "bg-primary text-white ms-auto text-end"
            if m.sender_id == patient_id
            else "bg-light"
        )

        html += f"""
        <div class='d-flex mb-2 {"justify-content-end" if m.sender_id == patient_id else "justify-content-start"}'>
            <div class='p-2 rounded {bubble_class}' style="max-width:70%;">
                <strong>{sender_name}:</strong> {m.content}
                <br>
                <small class='text-muted'>{m.created_at.strftime('%H:%M')}</small>
            </div>
        </div>
        """

    return html



@patients_chat_bp.route("/send-message/<doctor_id>", methods=["POST"])
@login_required
@patient_required
def send_message(doctor_id):

    patient_user_id = f"patient-{current_user.id}"
    doctor_user_id = f"employee-{doctor_id}"

    data = request.get_json()
    content = data.get("message", "").strip()

    if not content:
        return jsonify({"error": "empty"}), 400

    msg = Message(
        sender_id=patient_user_id,
        receiver_id=doctor_user_id,
        sender_type="PATIENT",
        receiver_type="EMPLOYEE",
        subject="Patient Message",
        content=content,
        is_read=False,
        created_at=datetime.utcnow()
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"status": "ok"}), 200

@patients_chat_bp.route("/messages/<doctor_id>")
@login_required
@patient_required
def get_messages(doctor_id):

    patient_user_id = f"patient-{current_user.id}"
    doctor_user_id = f"employee-{doctor_id}"

    messages = Message.query.filter(
        ((Message.sender_id == patient_user_id) & (Message.receiver_id == doctor_user_id)) |
        ((Message.sender_id == doctor_user_id) & (Message.receiver_id == patient_user_id))
    ).order_by(Message.created_at.asc()).all()

    messages_list = [
        {
            "sender": "patient" if msg.sender_id == patient_user_id else "doctor",
            "content": msg.content,
            "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for msg in messages
    ]

    return jsonify({"messages": messages_list})


