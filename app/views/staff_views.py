from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Staff
from app.forms import StaffForm
from decorators import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

# List all staff

@staff_bp.route("/")
def list_staff():
    staff_members = Staff.query.all()
    return render_template("staff/staff_list.html", staff_members=staff_members)

# Add new staff

@staff_bp.route("/add", methods=["GET", "POST"])
def add_staff():
    form = StaffForm()
    if form.validate_on_submit():
        new_staff = Staff(
            first_name=form.first_name.data,
            surname=form.surname.data,
            age=form.age.data,
            sex=form.sex.data,
            marital_status=form.marital_status.data,
            date_of_employment=form.date_of_employment.data,
            office_location=form.office_location.data,
            position=form.position.data,
            department=form.department.data,
            issues=form.issues.data,
            qualifications=form.qualifications.data,
            schools_attended=form.schools_attended.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
            address=form.address.data
        )
        db.session.add(new_staff)
        db.session.commit()
        flash("Staff member added successfully!", "success")
        return redirect(url_for("staff.list_staff"))
    return render_template("staff/staff_form.html", form=form, title="Add Staff")

# Update staff

@staff_bp.route("/update/<int:id>", methods=["GET", "POST"])
def update_staff(id):
    staff = Staff.query.get_or_404(id)
    form = StaffForm(obj=staff)
    if form.validate_on_submit():
        form.populate_obj(staff)
        db.session.commit()
        flash("Staff member updated successfully!", "success")
        return redirect(url_for("staff.list_staff"))
    return render_template("staff/staff_form.html", form=form, title="Update Staff")



# Delete staff
@staff_bp.route("/delete/<int:id>", methods=["POST"])
def delete_staff(id):
    staff = Staff.query.get_or_404(id)
    db.session.delete(staff)
    db.session.commit()
    flash("Staff member deleted successfully!", "danger")
    return redirect(url_for("staff.list_staff"))

# View staff details

@staff_bp.route("/<int:id>")
def staff_detail(id):
    staff = Staff.query.get_or_404(id)
    return render_template("staff/staff_detail.html", staff=staff)
