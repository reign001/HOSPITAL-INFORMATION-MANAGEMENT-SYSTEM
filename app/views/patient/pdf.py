from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from app.models.patients import Patient,VitalSign, Allergy, Immunization, FamilyHistory, SocialHistory
from flask import render_template, make_response
from app.views.patient.patient_views import patients_bp

@patients_bp.route("/patients/<int:patient_id>/summary/pdf")
def download_summary_pdf(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    vitals = VitalSign.query.filter_by(patient_id=patient_id).order_by(VitalSign.date_recorded.desc()).all()
    allergies = Allergy.query.filter_by(patient_id=patient_id).all()
    immunizations = Immunization.query.filter_by(patient_id=patient_id).all()
    family_history = FamilyHistory.query.filter_by(patient_id=patient_id).first()
    social_history = SocialHistory.query.filter_by(patient_id=patient_id).first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    elements = []

    # --- Header ---
    elements.append(Paragraph("<b>DUNAMIS MEDICAL CENTER</b>", styles["Title"]))
    elements.append(Paragraph("Patient Summary Report", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    # --- Patient Info ---
    elements.append(Paragraph("<b>Patient Information</b>", styles["Heading3"]))
    patient_info = [
        ["Full Name", patient.full_name()],
        ["Hospital Number", patient.hospital_number],
        ["Age", str(patient.age)],
        ["Sex", patient.sex.value],
        ["Phone", patient.phone_number or ""],
        ["Address", patient.address or ""],
    ]
    t = Table(patient_info, colWidths=[2 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * inch))

    # --- Medical History ---
    elements.append(Paragraph("<b>Medical History</b>", styles["Heading3"]))
    elements.append(Paragraph(getattr(patient, "medical_history", "No record."), styles["BodyText"]))
    elements.append(Spacer(1, 0.1 * inch))

    # --- Family & Social History ---
    elements.append(Paragraph("<b>Family & Social History</b>", styles["Heading3"]))
    elements.append(Paragraph(f"<b>Family:</b> {family_history.details if family_history else 'No record.'}", styles["BodyText"]))
    elements.append(Paragraph(f"<b>Social:</b> {social_history.details if social_history else 'No record.'}", styles["BodyText"]))
    elements.append(Spacer(1, 0.2 * inch))

    # --- Allergies ---
    elements.append(Paragraph("<b>Allergies</b>", styles["Heading3"]))
    if allergies:
        for a in allergies:
            elements.append(Paragraph(f"- {a.substance}: Reaction {a.reaction} (Severity: {a.severity})", styles["BodyText"]))
    else:
        elements.append(Paragraph("No allergies recorded.", styles["BodyText"]))
    elements.append(Spacer(1, 0.2 * inch))

    # --- Immunizations ---
    elements.append(Paragraph("<b>Immunizations</b>", styles["Heading3"]))
    if immunizations:
        data = [["Vaccine", "Date Given", "Notes"]]
        for imm in immunizations:
            data.append([
                imm.vaccine_name,
                imm.date_given.strftime("%Y-%m-%d") if imm.date_given else "",
                imm.notes or "",
            ])
        table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No immunizations recorded.", styles["BodyText"]))
    elements.append(Spacer(1, 0.2 * inch))

    # --- Recent Vitals ---
    elements.append(Paragraph("<b>Recent Vitals</b>", styles["Heading3"]))
    if vitals:
        data = [["Date", "BP", "HR", "Resp", "Temp (°C)", "Weight (kg)"]]
        for v in vitals[:10]:  # limit to recent 10
            data.append([
                v.date_recorded.strftime("%Y-%m-%d %H:%M"),
                v.blood_pressure,
                v.heart_rate,
                v.respiratory_rate,
                v.temperature,
                v.weight,
            ])
        table = Table(data, colWidths=[1.2*inch]*6)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No vitals recorded.", styles["BodyText"]))

    doc.build(elements)

    pdf_value = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_value)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=Patient_Summary_{patient.hospital_number}.pdf"
    return response
