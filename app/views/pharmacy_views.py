from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models import db, Drug, DispenseRecord, Patient
from datetime import datetime
from flask_login import login_required, current_user
from decorators import role_required

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")

# List all drugs

@pharmacy_bp.route("/")
@login_required
def list_drugs():
    if not current_user.is_authenticated:
        abort(403)
    if current_user.role not in ["admin", "super_admin"]:
        abort(403)

    drugs = Drug.query.all()
    return render_template("pharmacy/list.html", drugs=drugs)

# Add a new drug to inventory
@pharmacy_bp.route("/add", methods=["GET", "POST"])
# @role_required()
def add_drug():
    if request.method == "POST":
        new_drug = Drug(
            name=request.form["name"],
            brand_name=request.form["brand_name"],   # new field
            expiry_date=datetime.strptime(request.form["expiry_date"], "%Y-%m-%d"),
            unit_cost_price=float(request.form["unit_cost_price"]),
            unit_selling_price=float(request.form["unit_selling_price"]),
            quantity_left=int(request.form["quantity_left"]),
            quantity_supplied=request.form["quantity_left"]
        )
        db.session.add(new_drug)
        db.session.commit()
        flash("Drug added successfully!", "success")
        return redirect(url_for("pharmacy.list_drugs"))
    return render_template("pharmacy/create.html")


@pharmacy_bp.route("/restock/<int:drug_id>", methods=["GET", "POST"])
# @role_required()
@login_required
def restock_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)

    if request.method == "POST":
        added_quantity = int(request.form["added_quantity"])
        if added_quantity <= 0:
            flash("Quantity must be positive.", "danger")
            return redirect(url_for("pharmacy.restock_drug", drug_id=drug.id))

        drug.quantity_left += added_quantity
        db.session.commit()
        flash(
            f"Added {added_quantity} units to {drug.brand_name} ({drug.name}).", 
            "success"
        )
        return redirect(url_for("pharmacy.list_drugs"))

    return render_template("pharmacy/restock.html", drug=drug)


@pharmacy_bp.route("/delete/<int:drug_id>", methods=["POST"])
# @role_required()
@login_required
def delete_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)
    db.session.delete(drug)
    db.session.commit()
    flash(f"Drug '{drug.name}' ({drug.brand_name}) deleted from inventory.", "success")
    return redirect(url_for("pharmacy.list_drugs"))