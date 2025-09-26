from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TimeField, SubmitField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
from wtforms import DateTimeField

class StaffForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired()])
    sex = SelectField("Sex", choices=[("Male", "Male"), ("Female", "Female")], validators=[DataRequired()])
    marital_status = SelectField("Marital Status", choices=[
        ("Single", "Single"), ("Married", "Married"), ("Divorced", "Divorced"), ("Widowed", "Widowed")
    ], validators=[Optional()])

    date_of_employment = DateField("Date of Employment", validators=[DataRequired()])
    office_location = StringField("Office Location", validators=[Optional()])
    position = StringField("Position", validators=[Optional()])
    department = StringField("Department", validators=[Optional()])

    issues = TextAreaField("Issues", validators=[Optional()])
    qualifications = TextAreaField("Qualifications", validators=[Optional()])
    schools_attended = TextAreaField("Schools Attended", validators=[Optional()])

    phone_number = StringField("Phone Number", validators=[Optional()])
    email = StringField("Email", validators=[Optional(), Email()])
    address = TextAreaField("Address", validators=[Optional()])

    submit = SubmitField("Save")


from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class LabVisitForm(FlaskForm):
    patient_name = StringField("First Name", validators=[DataRequired()])
    patient_surname = StringField("Surname", validators=[DataRequired()])
    patient_age = IntegerField("Age", validators=[DataRequired()])
    sex = SelectField("Sex", choices=[("Male", "Male"), ("Female", "Female")], validators=[DataRequired()])
    nhis_status = SelectField("NHIS Status", choices=[("NHIS", "NHIS"), ("Non-NHIS", "Non-NHIS")], validators=[DataRequired()])
    inpatient_status = SelectField("Patient Type", choices=[("Inpatient", "Inpatient"), ("Outpatient", "Outpatient")], validators=[DataRequired()])
    phone_number = StringField("Phone Number", validators=[Optional()])
    sample = StringField("Sample", validators=[Optional()])
    referring_physician = StringField("Referring Physician", validators=[Optional()])
    laboratory_number = StringField("Laboratory Number", validators=[DataRequired()])
    investigations = TextAreaField("Investigations Done", validators=[DataRequired()])
    amount_paid = FloatField("Amount Paid", validators=[DataRequired()])

    submit = SubmitField("Save")


from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class InPatientForm(FlaskForm):
    hospital_number = StringField("Hospital Number", validators=[Optional()])
    patient_id = SelectField("Select Patient", coerce=int, validators=[DataRequired()])
    patient_name = StringField("Patient Name")
    sex = StringField("Sex")
    age = StringField("Age")
    diagnosis = StringField("Diagnosis")
    medications_given = StringField("Medications Given")
    discharged_at = DateField("Discharged On", format="%Y-%m-%d", render_kw={"type": "date"})
    admitted_on = DateField("Admitted On", format="%Y-%m-%d", render_kw={"type": "date"})
    condition = StringField("Condition")

    discharge = BooleanField("Discharged?")
    referred = BooleanField("Referred?")
    rip = BooleanField("RIP?")

    submit = SubmitField("Add Inpatient")


class OutPatientForm(FlaskForm):
    patient_name = StringField("Patient Name", validators=[DataRequired()])
    sex = SelectField("Sex", choices=[("Male", "Male"), ("Female", "Female")], validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired()])
    address = StringField("Address", validators=[Optional()])
    medications_given = TextAreaField("Medications Given", validators=[Optional()])
    nhis_status = SelectField("NHIS Status", choices=[("NHIS", "NHIS"), ("NON-NHIS", "NON-NHIS")], default="NON-NHIS")   # ✅ checkbox
    submit = SubmitField("Save")


class DeliveryForm(FlaskForm):
    mother_name = StringField("Mother's Name", validators=[DataRequired()])
    mother_age = IntegerField("Mother's Age", validators=[Optional()])
    nhis_status = SelectField("NHIS Status", choices=[("NHIS", "NHIS"), ("NON-NHIS", "NON-NHIS")], default="NON-NHIS")

    delivery_date = DateField("Delivery Date", validators=[DataRequired()])
    delivery_time = TimeField("Delivery Time", validators=[Optional()])

    delivery_type = SelectField("Delivery Type", choices=[("Normal", "Normal"), ("CS", "Caesarean Section")], validators=[DataRequired()])
    cs_indication = StringField("Indication for CS", validators=[Optional()])

    baby_gender = SelectField("Baby Gender", choices=[("Male", "Male"), ("Female", "Female")], validators=[DataRequired()])
    baby_weight = FloatField("Baby Weight (kg)", validators=[Optional()])

    mother_condition = StringField("Mother's Condition", validators=[Optional()])
    baby_condition = StringField("Baby's Condition", validators=[Optional()])

    submit = SubmitField("Save")
