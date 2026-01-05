from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import db, User
from app.models.patients import Patient
from app.models.employee import Employee, check_password_hash
from app.extensions import login_manager
from sqlalchemy import func



auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("patient-"):
        return Patient.query.get(int(user_id.split("-")[1]))
    elif user_id.startswith("employee-"):
        return Employee.query.get(int(user_id.split("-")[1]))
    elif user_id.startswith("admin-"):
        return User.query.get(int(user_id.split("-")[1]))
    return None

# @auth_bp.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         identifier = request.form.get("identifier").lower()
#         password = request.form.get("password")

#         patient = Patient.query.filter_by(email=identifier).first()
#         if patient and password == patient.hospital_number:
#             login_user(patient)
#             return redirect(url_for("patients.dashboard"))

#         flash("Invalid credentials", "danger")
#         return redirect(url_for("auth.login"))

#     return render_template("admin/login.html")



# User logout
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


ALLOWED_ROLES = {"doctor", "nurse", "admin"}

# User login
# User login

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        if not identifier or not password:
            flash("Please enter both identifier and password.", "danger")
            return redirect(url_for("auth.login"))

        identifier = identifier.strip().lower()

        # -------------------------------
        # 1️⃣ Superadmin login (username)
        # -------------------------------
        superadmin = User.query.filter(func.lower(User.username) == identifier).first()
        if superadmin and superadmin.check_password(password):
            login_user(superadmin)
            return redirect(url_for("auth.index"))

        # -------------------------------
        # 2️⃣ Employee login (email)
        # -------------------------------
        employee = Employee.query.join(Employee.role).filter(
            func.lower(Employee.email) == identifier
        ).first()

        if employee:
            emp_role = employee.role.name.lower() if employee.role else None
            if emp_role not in ALLOWED_ROLES:
                flash("You are not authorized to access this system.", "danger")
                return redirect(url_for("auth.login"))

            if employee.check_password(password):
                login_user(employee)
                # Redirect based on role
                if emp_role == "doctor":
                    return redirect(url_for("doctor.dashboard"))
                elif emp_role == "nurse":
                    return redirect(url_for("nurse.dashboard"))
                elif emp_role == "admin":
                    return redirect(url_for("admin.dashboard"))

        # -------------------------------
        # 3️⃣ Patient login (email)
        # -------------------------------
        patient = Patient.query.filter(func.lower(Patient.email) == identifier).first()
        if patient and password == patient.hospital_number:
            login_user(patient)
            return redirect(url_for("patient_chat.dashboard"))

        # -------------------------------
        # 4️⃣ No match
        # -------------------------------
        flash("Invalid username/email or password.", "danger")
        return redirect(url_for("auth.login"))

    # GET request
    return render_template("admin/login.html")


@auth_bp.route("/")
def index():
    from app.models.lab import LabVisit
    latest_visit = LabVisit.query.order_by(LabVisit.id.desc()).first()
    return render_template("index.html", latest_visit=latest_visit)