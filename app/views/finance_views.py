from flask import Blueprint, render_template
from decorators import role_required

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
# from app.modelsx import FinanceRecord, HMOPayment, db, update_finance_record

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
# from app.modelsx import FinanceRecord, FinanceLog
from app import db
from datetime import datetime


finance_bp = Blueprint("finance", __name__, url_prefix="/finance")
finance_bp = Blueprint("finance", __name__, template_folder="../templates")

@finance_bp.route("/daily")
@login_required
# @superadmin_required
def daily_finance():
    # refresh today’s record
    record = update_finance_record()

    hmos = HMOPayment.query.filter_by(finance_id=record.id).all()
    return render_template("finance/list.html", record=record, hmos=hmos)


@finance_bp.route("/add_hmo", methods=["POST"])
@login_required
# @superadmin_required
def add_hmo():
    hmo_name = request.form.get("hmo_name")
    amount_str = request.form.get("amount")

    # Validate inputs
    if not hmo_name or not amount_str:
        flash("HMO name and amount are required.", "danger")
        return redirect(url_for("finance.daily_finance"))

    try:
        amount = float(amount_str)
    except ValueError:
        flash("Invalid amount entered. Please enter a valid number.", "danger")
        return redirect(url_for("finance.daily_finance"))

    # Get today's finance record
    record = update_finance_record()

    # Create HMO payment
    hmo_payment = HMOPayment(
        hmo_name=hmo_name,
        amount=amount,
        notes=request.form.get("notes")  # optional field
    )
    db.session.add(hmo_payment)

    # Update finance record
    record.hmos_total = (record.hmos_total or 0) + amount
    record.compute_total()

    db.session.commit()
    flash("HMO payment added successfully.", "success")
    return redirect(url_for("finance.daily_finance"))

@finance_bp.route("/delete/<int:record_id>")
@login_required
# @superadmin_required
def delete_record(record_id):
    record = FinanceRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Finance record deleted", "info")
    return redirect(url_for("finance.daily_finance"))



@finance_bp.route("/history", methods=["GET", "POST"])
@login_required
def finance_history():
    # Only super_admins can access
    if current_user.role != "super_admin":
        flash("Access denied. Super admin only.", "danger")
        return redirect(url_for("index"))

    query = FinanceLog.query.order_by(FinanceLog.record_date.desc())

    # Search filters
    search_date = request.args.get("date")      # exact YYYY-MM-DD
    search_month = request.args.get("month")    # YYYY-MM
    search_year = request.args.get("year")      # YYYY

    if search_date:
        try:
            dt = datetime.strptime(search_date, "%Y-%m-%d").date()
            query = query.filter(FinanceLog.record_date == dt)
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "warning")

    if search_month:
        try:
            dt = datetime.strptime(search_month, "%Y-%m")
            query = query.filter(
                db.extract("year", FinanceLog.record_date) == dt.year,
                db.extract("month", FinanceLog.record_date) == dt.month,
            )
        except ValueError:
            flash("Invalid month format. Use YYYY-MM.", "warning")

    if search_year:
        try:
            yr = int(search_year)
            query = query.filter(db.extract("year", FinanceLog.record_date) == yr)
        except ValueError:
            flash("Invalid year format.", "warning")

    logs = query.all()
    return render_template("finance/finance_history.html", logs=logs)
