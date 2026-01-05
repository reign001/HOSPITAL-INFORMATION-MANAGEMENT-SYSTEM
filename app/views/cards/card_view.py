from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models import PatientCard, Patient
from app.views.patient.patient_views import patients_bp

cards_bp = Blueprint("cards", __name__, url_prefix="/cards")

# List all cards for a patient
@cards_bp.route("/patient/<int:patient_id>")
def list_cards(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("cards/list.html", patient=patient, cards=patient.cards)

# View a specific card
@cards_bp.route("/<int:card_id>")
def card_detail(card_id):
    card = PatientCard.query.get_or_404(card_id)
    return render_template("cards/detail.html", card=card)

# Create a new card
@cards_bp.route("/new/<int:patient_id>", methods=["GET", "POST"])
def new_card(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        card = PatientCard(
            patient=patient,
            blood_pressure=request.form.get("blood_pressure"),
            heart_rate=request.form.get("heart_rate"),
            respiratory_rate=request.form.get("respiratory_rate"),
            temperature=request.form.get("temperature"),
            oxygen_saturation=request.form.get("oxygen_saturation"),
            weight=request.form.get("weight"),
            height=request.form.get("height"),
            chief_complaint=request.form.get("chief_complaint"),
            history_of_present_illness=request.form.get("history_of_present_illness"),
            past_medical_history=request.form.get("past_medical_history"),
            medications=request.form.get("medications"),
            allergies=request.form.get("allergies"),
            examination=request.form.get("examination"),
            assessment=request.form.get("assessment"),
            plan=request.form.get("plan")
        )
        db.session.add(card)
        db.session.commit()
        flash("Patient card created successfully!", "success")
        return redirect(url_for("cards.card_detail", card_id=card.id))
    return render_template("cards/new.html", patient=patient)

# Edit a card
@cards_bp.route("/edit/<int:card_id>", methods=["GET", "POST"])
def edit_card(card_id):
    card = PatientCard.query.get_or_404(card_id)
    if request.method == "POST":
        card.blood_pressure = request.form.get("blood_pressure")
        card.heart_rate = request.form.get("heart_rate")
        card.respiratory_rate = request.form.get("respiratory_rate")
        card.temperature = request.form.get("temperature")
        card.oxygen_saturation = request.form.get("oxygen_saturation")
        card.weight = request.form.get("weight")
        card.height = request.form.get("height")
        card.chief_complaint = request.form.get("chief_complaint")
        card.history_of_present_illness = request.form.get("history_of_present_illness")
        card.past_medical_history = request.form.get("past_medical_history")
        card.medications = request.form.get("medications")
        card.allergies = request.form.get("allergies")
        card.examination = request.form.get("examination")
        card.assessment = request.form.get("assessment")
        card.plan = request.form.get("plan")

        db.session.commit()
        flash("Patient card updated successfully!", "success")
        return redirect(url_for("cards.card_detail", card_id=card.id))
    return render_template("cards/edit.html", card=card)


from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.patients import Patient
from app.models.cards import PatientCard
from app.models.medications import ActiveMedication
from app.models.patient_note import PatientNote
from datetime import datetime

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patients_bp.route("/<int:patient_id>/card", methods=["GET", "POST"])
def patient_card(patient_id):
    """
    Show the patient card for a given patient.
    Handles adding patient notes and marking medications as administered.
    """
    patient = Patient.query.get_or_404(patient_id)
    card = PatientCard.query.filter_by(patient_id=patient_id).first()
    
    if not card:
        # If card does not exist, create it
        card = PatientCard(patient_id=patient.id)
        db.session.add(card)
        db.session.commit()

    # Handle POST requests
    if request.method == "POST":
        # 1️⃣ Add a patient note
        note_content = request.form.get("note_content")
        if note_content:
            note = PatientNote(
                patient_id=patient.id,
                content=note_content
            )
            db.session.add(note)
        
        # 2️⃣ Mark medication as administered
        med_id = request.form.get("administer_med_id")
        if med_id:
            med = ActiveMedication.query.get(int(med_id))
            if med and med.patient_id == patient.id:
                med.administered = True
                med.last_updated = datetime.utcnow()
        
        db.session.commit()
        flash("Updates saved successfully!", "success")
        return redirect(url_for("patients.patient_card", patient_id=patient.id))

    # GET request: prepare data for display
    active_meds = ActiveMedication.query.filter_by(patient_id=patient.id).all()
    pending_meds = [m for m in active_meds if not m.administered]
    notes = PatientNote.query.filter_by(patient_id=patient.id).order_by(PatientNote.created_at.desc()).all()

    return render_template(
        "patients/patient_card.html",
        patient=patient,
        card=card,
        active_meds=active_meds,
        pending_meds=pending_meds,
        notes=notes
    )
