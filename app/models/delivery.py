
from app import db
from datetime import datetime 




class Delivery(db.Model):
    __tablename__ = 'deliveries'

    id = db.Column(db.Integer, primary_key=True)
    mother_name = db.Column(db.String(120), nullable=False)
    mother_age = db.Column(db.Integer, nullable=True)  
    nhis_status = db.Column(db.String(20), nullable=False, default="NON-NHIS")  # NHIS / NON-NHIS
    delivery_date = db.Column(db.Date, default=datetime.utcnow)
    delivery_time = db.Column(db.Time, nullable=True)

    delivery_type = db.Column(db.String(50), nullable=False)  # Normal / CS
    cs_indication = db.Column(db.String(255), nullable=True)  # Only if CS

    baby_gender = db.Column(db.String(10), nullable=False)
    baby_weight = db.Column(db.Float, nullable=True)  # kg

    mother_condition = db.Column(db.String(255), nullable=True)
    baby_condition = db.Column(db.String(255), nullable=True)
# ----------------------