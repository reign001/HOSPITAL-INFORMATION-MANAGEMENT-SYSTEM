from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models import *
from app.views.auth import login_required
from app.views.pharmacy_views import pharmacy_bp
from decorators import role_required

dispensary_bp = Blueprint("dispensary", __name__, template_folder="../templates")

@dispensary_bp.route("/")
# @role_required()
def list_dispensary_items():
    # Later connect to DB
    items = [
        {"id": 1, "name": "Paracetamol Syrup", "quantity": 50},
        {"id": 2, "name": "Vitamin C Tablets", "quantity": 100},
    ]
    return render_template("dispensary/dispense.html", items=items)



@pharmacy_bp.route("/dispense", methods=["GET", "POST"])
# @role_required()
@login_required
def dispense_drug():
    drugs = Drug.query.filter(
        Drug.quantity_left > 0,
        Drug.expiry_date >= date.today()
    ).all()

    if request.method == "POST":
        # Get patient details
        patient_name = request.form.get("patient_name")
        middle_name = request.form.get("middle_name")
        surname = request.form.get("surname")
        patient_age = request.form.get("patient_age")
        hospital_number = request.form.get("hospital_number")
        amount_paid = request.form.get("amount_paid", 0.0)
        amount_paid = float(amount_paid) if amount_paid else 0.0

        sex = request.form.get("sex")  # safely map to "M" or "F"

        address = request.form.get("address")
        phone_number = request.form.get("phone_number")
        nhis_status = request.form.get("nhis_status", "NON_NHIS")

        # Find or create the patient
        patient = Patient.query.filter_by(hospital_number=hospital_number).first()
        if not patient:
            patient = Patient(
                first_name=patient_name,
                middle_name=middle_name,
                surname=surname,
                age=patient_age,
                hospital_number=hospital_number,
                sex=sex,
                address=address,
                phone_number=phone_number,
                nhis_status=nhis_status,
            )
            db.session.add(patient)
            db.session.flush()  # ensures patient.id is available

        total_due = 0.0
        total_balance = 0.0

        for drug in drugs:
            if str(drug.id) in request.form.getlist("drug_ids[]"):
                qty = int(request.form.get(f"qty_{drug.id}", 0))
                if qty > 0 and drug.quantity_left >= qty:
                    # Reduce stock
                    drug.quantity_left -= qty

                    # Calculate costs
                    subtotal_cost = drug.unit_cost_price * qty
                    subtotal_due = drug.unit_selling_price * qty

                    # Distribute payment across items (simplified)
                    record_amount_paid = min(amount_paid, subtotal_due)
                    record_balance = subtotal_due - record_amount_paid
                    amount_paid -= record_amount_paid

                    # Save dispense record
                    dispense_record = DispenseRecord(
                        patient_id=patient.id,
                        drug_id=drug.id,
                        quantity_dispensed=qty,
                        total_cost=subtotal_cost,
                        amount_paid=record_amount_paid,
                        balance=record_balance,
                    )
                    db.session.add(dispense_record)

                    total_due += subtotal_due
                    total_balance += record_balance

        db.session.commit()

        flash(
            f"Drugs dispensed to {patient.first_name} {patient.surname} "
            f"(HN: {patient.hospital_number}). "
            f"Total Amount: ₦{total_due:,.2f}, Balance: ₦{total_balance:,.2f}",
            "success",
        )

        return redirect(url_for("pharmacy.dispense_drug"))

    return render_template("dispensary/dispense.html", drugs=drugs)


from sqlalchemy.orm import joinedload

# def get_dispense_summary(period="day"):
#     now = datetime.utcnow()

#     # Start with the base query
#     query = DispenseRecord.query.options(
#         joinedload(DispenseRecord.patient),
#         joinedload(DispenseRecord.drug)
#     ).all()

#     if period == "day":
#         today = date.today()
#         query = query.filter(func.date(DispenseRecord.dispensed_at) == today)
#     elif period == "week":
#         start_of_week = now - timedelta(days=now.weekday())
#         query = query.filter(DispenseRecord.dispensed_at >= start_of_week)
#     elif period == "month":
#         start_of_month = datetime(now.year, now.month, 1)
#         query = query.filter(DispenseRecord.dispensed_at >= start_of_month)

#     # Totals
#     records = query.all()
#     total_drugs_dispensed = sum(r.quantity_dispensed for r in records)
#     total_amount_paid = sum(r.amount_paid or 0 for r in records)
#     total_cost = sum(r.total_cost or 0 for r in records)

#     return {
#         "total_drugs_dispensed": total_drugs_dispensed,
#         "total_amount_paid": total_amount_paid,
#         "total_cost": total_cost,
#         "records": records
#     }

def get_dispense_summary(period="day", year=None, month=None):
    now = datetime.utcnow()
    query = DispenseRecord.query

    if period == "day":
        today = date.today()
        query = query.filter(func.date(DispenseRecord.dispensed_at) == today)

    elif period == "week":
        start_of_week = now - timedelta(days=now.weekday())
        query = query.filter(DispenseRecord.dispensed_at >= start_of_week)

    elif period == "month":
        # default to current month
        start_of_month = datetime(now.year, now.month, 1)
        query = query.filter(DispenseRecord.dispensed_at >= start_of_month)

    elif period == "specific_month" and year and month:
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)
        query = query.filter(
            DispenseRecord.dispensed_at >= start_of_month,
            DispenseRecord.dispensed_at < end_of_month
        )

    records = query.all()

    return {
        "total_drugs_dispensed": sum(r.quantity_dispensed for r in records),
        "total_amount_paid": sum(r.amount_paid or 0 for r in records),
        "total_cost": sum(r.total_cost or 0 for r in records),
        "records": records,
    }




@dispensary_bp.route("/records/<string:period>")
@dispensary_bp.route("/records/<string:period>/<int:year>/<int:month>")
def dispensary_records(period, year=None, month=None):
    summary = get_dispense_summary(period, year, month)
    months = get_available_months()  # NEW
    
    return render_template(
        "dispensary/records.html",
        summary=summary,
        period=period,
        year=year,
        month=month,
        months=months
    )
import calendar
def get_available_months():
    results = (
        db.session.query(
            func.extract('year', DispenseRecord.dispensed_at).label("year"),
            func.extract('month', DispenseRecord.dispensed_at).label("month")
        )
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    months = []
    for r in results:
        year = int(r.year)
        month_num = int(r.month)
        month_name = calendar.month_name[month_num]  # e.g. 9 -> "September"
        months.append((year, month_num, month_name))
    return months


@dispensary_bp.route("/dispensary")
@login_required
def dispensary_view():
    prescriptions = Prescription.query.filter_by(is_dispensed=False).all()
    return render_template("dispensary/prescriptions.html", prescriptions=prescriptions)



