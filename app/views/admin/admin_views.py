from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from datetime import date
from app.models.employee import Employee, Role, ShiftEnum, EmployeeShift
from app.models.user import User
from app.models.patients import PatientRequest
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@property
def is_superadmin(self):
    return self.role and self.role.name.lower() == "superadmin"

@admin_bp.route("/")
def dashboard():
    # --- Pagination Setup ---
    page = request.args.get('page', 1, type=int)
    per_page = 15
    employees_pag = Employee.query.paginate(page=page, per_page=per_page, error_out=False)
    employees = employees_pag.items

    # --- Stats ---
    active_count = Employee.query.filter_by(is_active=True).count()
    inactive_count = Employee.query.filter_by(is_active=False).count()
    roles = Role.query.all()

    # --- Role Distribution ---
    role_distribution = (
        db.session.query(Role.name, func.count(Employee.id).label('count'))
        .join(Employee, Employee.role_id == Role.id)
        .group_by(Role.name)
        .all()
    )

    # --- Today's Shift Roster ---
    import calendar
    today = date.today()
    year = today.year
    month = today.month
    num_days = calendar.monthrange(year, month)[1]
    days_of_month = [date(year, month, day) for day in range(1, num_days + 1)]

    shift_roster = {
        "Morning": [s.employee for s in EmployeeShift.query.filter_by(shift=ShiftEnum.MORNING, date=today).all()],
        "Afternoon": [s.employee for s in EmployeeShift.query.filter_by(shift=ShiftEnum.AFTERNOON, date=today).all()],
        "Night": [s.employee for s in EmployeeShift.query.filter_by(shift=ShiftEnum.NIGHT, date=today).all()]
    }

    roster_for_template = {shift_name: [assignment.employee for assignment in assignments] 
                           for shift_name, assignments in shift_roster.items()}

    # --- Patient Requests ---
    unread_requests_count = PatientRequest.query.filter_by(is_seen=False).count()
    


    # --- Full Page Render ---
    return render_template(
        "admin/dashboard.html",
        employees=employees,
        employees_pag=employees_pag,
        roles=roles,
        active_count=active_count,
        inactive_count=inactive_count,
        role_distribution=role_distribution,
        shift_roster=roster_for_template,
        today=today,
        days_of_month=days_of_month,
        unread_requests_count=unread_requests_count,
    )




@admin_bp.route("/add-employee", methods=["GET", "POST"])
def add_employee():
    roles = Role.query.all()
    users= User.query.all()

    if request.method == "POST":
        first_name = request.form.get("first_name")
        surname = request.form.get("surname")
        email = request.form.get("email")
        password = request.form.get("password")
        role_id = request.form.get("role_id")
        department = request.form.get("department")
        license_number = request.form.get("license_number")

        # ✅ Create new employee
        new_employee = Employee(
            first_name=first_name,
            surname=surname,
            email=email,
            role_id=role_id,
            department=department,
            license_number=license_number,
            is_active=True
        )
        # ✅ Hash the password
        new_employee.set_password(password)

        db.session.add(new_employee)
        db.session.commit()
        flash(f"Employee {first_name} {surname} added successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/add_employee.html", roles=roles, users=users)



@admin_bp.route("/edit_employee/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    roles = Role.query.all()

    if request.method == "POST":
        employee.first_name = request.form["first_name"]
        employee.surname = request.form["surname"]
        employee.email = request.form["email"]
        employee.role_id = request.form["role_id"]
        employee.department = request.form.get("department")
        employee.license_number = request.form.get("license_number")
        db.session.commit()
        flash("Employee updated successfully!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/edit_employee.html", employee=employee, roles=roles)


@admin_bp.route("/delete_employee/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash(f"Employee {employee.full_name()} has been deleted.", "success")
    return redirect(url_for("admin.dashboard"))



@admin_bp.route("/assign_shift", methods=["GET", "POST"])
def assign_shift():
    today = date.today()
    employees = Employee.query.all()

    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        shift = request.form.get("shift")

        # Ensure shift is valid
        if shift not in [s.name for s in ShiftEnum]:
            flash("Invalid shift selected", "danger")
            return redirect(url_for("admin.assign_shift"))

        # Check if already assigned
        existing = EmployeeShift.query.filter_by(employee_id=employee_id, date=today).first()
        if existing:
            existing.shift = shift
        else:
            new_assignment = EmployeeShift(employee_id=employee_id, shift=shift, date=today)
            db.session.add(new_assignment)
        
        db.session.commit()
        flash("Shift assigned successfully", "success")
        return redirect(url_for("admin.assign_shift"))

    # Build shift roster for template
    shift_roster = {}
    for s in ShiftEnum:
        shift_roster[s.name] = EmployeeShift.query.filter_by(shift=s.name, date=today).all()

    return render_template(
        "admin/assign_shift.html",
        employees=employees,
        shifts=ShiftEnum,
        today=today,
        shift_roster=shift_roster
    )


from collections import defaultdict
from datetime import datetime, timedelta

# Example: Generate empty month roster
def generate_month_roster(year, month, shifts_list, employees):
    from calendar import monthrange

    days_in_month = monthrange(year, month)[1]
    roster = defaultdict(dict)

    for day_num in range(1, days_in_month + 1):
        date = datetime(year, month, day_num)
        for shift in shifts_list:
            # Initially no employees assigned
            roster[date][shift] = []
    return roster


@admin_bp.route("/requests")
def view_requests():
    requests = PatientRequest.query.order_by(PatientRequest.created_at.desc()).all()
    # patient_requests = PatientRequest.query.order_by(PatientRequest.created_at.desc()).all()
    unread_requests_count = PatientRequest.query.filter_by(is_seen=False).count()
    pending_requests = PatientRequest.query.filter_by(status="Pending").all()
    pending_requests_count = len(pending_requests)

    return render_template("admin/requests.html", requests=requests, unread_requests_count=unread_requests_count,
                           pending_requests=pending_requests, pending_requests_count=pending_requests_count)


@admin_bp.route("/requests/mark_seen/<int:request_id>", methods=["POST"])
def mark_request_seen(request_id):
    req = PatientRequest.query.get_or_404(request_id)
    req.is_seen = True
    db.session.commit()
    return jsonify({"status": "ok"})

@admin_bp.route("/update-request/<int:request_id>", methods=["POST"])
@login_required
def update_request(request_id):
    request_obj = PatientRequest.query.get_or_404(request_id)
    
    status = request.form.get("status")
    admin_note = request.form.get("admin_note", "")

    if status not in ["Granted", "Denied"]:
        flash("Invalid status", "danger")
        return redirect(url_for("admin.dashboard"))

    request_obj.status = status
    request_obj.admin_note = admin_note
    db.session.commit()

    flash(f"Request #{request_obj.id} updated to {status}.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/clear-request-notifications", methods=["POST"])
@login_required
def clear_request_notifications():

    unread = PatientRequest.query.filter_by(is_seen=False).all()

    for req in unread:
        req.is_seen = True

    db.session.commit()

    flash("Request notifications cleared.", "success")
    return redirect(url_for("admin.dashboard"))