from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from app import db
from app.models.delivery import Delivery
from app.forms import *
from decorators import role_required

delivery_bp = Blueprint('delivery', __name__, url_prefix='/deliveries')


# List all deliveries
@delivery_bp.route('/')
def list_deliveries():
    deliveries = Delivery.query.order_by(Delivery.delivery_date.desc()).all()

    # Stats: deliveries this month & this year
    now = datetime.utcnow()
    current_month = now.strftime("%B")   # Full month name (e.g., September)
    current_year = now.year
    monthly_count = Delivery.query.filter(
        db.extract('month', Delivery.delivery_date) == now.month,
        db.extract('year', Delivery.delivery_date) == now.year
    ).count()

    yearly_count = Delivery.query.filter(
        db.extract('year', Delivery.delivery_date) == now.year
    ).count()

    return render_template(
        'delivery/list.html',
        deliveries=deliveries,
        monthly_count=monthly_count,
        yearly_count=yearly_count,
        current_month=current_month,
        current_year=current_year
    )


# Add a new delivery
@delivery_bp.route('/add', methods=['GET', 'POST'])
def add_delivery():
    form = DeliveryForm()

    if form.validate_on_submit():
        delivery_date = form.delivery_date.data
        delivery_time = form.delivery_time.data

        # Combine date and time safely
        if delivery_date and delivery_time:
            delivery_datetime = datetime.combine(delivery_date, delivery_time)
        else:
            delivery_datetime = delivery_date  # fallback if time is not given

        new_delivery = Delivery(
            mother_name=form.mother_name.data,
            mother_age=form.mother_age.data,
            baby_gender=form.baby_gender.data,
            delivery_type=form.delivery_type.data,
            cs_indication=form.cs_indication.data if form.delivery_type.data == "CS" else None,
            delivery_time=form.delivery_time.data,
            delivery_date=delivery_datetime,
            baby_weight=form.baby_weight.data,
            mother_condition=form.mother_condition.data,
            baby_condition=form.baby_condition.data,
            nhis_status=form.nhis_status.data
        )

        db.session.add(new_delivery)
        db.session.commit()
        flash("Delivery record added successfully!", "success")
        return redirect(url_for('delivery.list_deliveries'))

    return render_template('delivery/add.html', form=form)

# View detail of a delivery
@delivery_bp.route('/<int:delivery_id>')
def delivery_detail(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    return render_template('delivery/delivery_detail.html', delivery=delivery)


# Edit delivery
@delivery_bp.route('/<int:delivery_id>/edit', methods=['GET', 'POST'])
def edit_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    form = DeliveryForm(obj=delivery)
    # delivery = Delivery.query.get_or_404(delivery_id)

    if request.method == 'POST':
        delivery.mother_name = request.form['mother_name']
        delivery.baby_gender = request.form['baby_gender']
        delivery.delivery_type = request.form['delivery_type']
        delivery.indication_for_cs = (
            request.form.get('indication_for_cs')
            if delivery.delivery_type == "CS"
            else None
        )
        delivery_date = request.form['delivery_date']
        delivery_time = request.form['delivery_time']
        delivery.delivery_date = datetime.strptime(
            f"{delivery_date} {delivery_time}", "%Y-%m-%d %H:%M"
        )
        delivery.baby_weight = request.form['baby_weight']
        delivery.mother_condition = request.form['mother_condition']
        delivery.baby_condition = request.form['baby_condition']
        delivery.nhis_status = request.form['nhis_status']

        db.session.commit()
        flash("Delivery record updated successfully!", "success")
        return redirect(url_for('delivery.list_deliveries'))

    return render_template('delivery/edit.html', delivery=delivery, form=form)


# Delete delivery
@delivery_bp.route('/<int:delivery_id>/delete', methods=['POST'])
def delete_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    db.session.delete(delivery)
    db.session.commit()
    flash("Delivery record deleted successfully!", "danger")
    return redirect(url_for('delivery.list_deliveries'))
