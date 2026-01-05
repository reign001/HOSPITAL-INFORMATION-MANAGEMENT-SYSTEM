from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TimeField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
from wtforms import DateTimeField

class AllergyForm(FlaskForm):
    allergen = StringField("Allergen", validators=[DataRequired()])
    reaction = StringField("Reaction")
    severity = SelectField("Severity", choices=[("Mild", "Mild"), ("Moderate", "Moderate"), ("Severe", "Severe")])
    date_identified = DateField("Date Identified")
    submit = SubmitField("Add Allergy")


class ImmunizationForm(FlaskForm):
    vaccine_name = StringField("Vaccine Name", validators=[DataRequired()])
    date_administered = DateField("Date Administered")
    next_due_date = DateField("Next Due Date")
    administered_by = StringField("Administered By")
    submit = SubmitField("Add Immunization")


class VitalSignForm(FlaskForm):
    blood_pressure = StringField("Blood Pressure")
    heart_rate = IntegerField("Heart Rate (bpm)")
    respiratory_rate = IntegerField("Respiratory Rate")
    temperature = FloatField("Temperature (°C)")
    weight = FloatField("Weight (kg)")
    submit = SubmitField("Record Vitals")
