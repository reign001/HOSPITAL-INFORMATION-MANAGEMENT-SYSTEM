from app import db
from datetime import datetime



class Drug(db.Model):
    __tablename__ = "drugs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    brand_name = db.Column(db.String(256), nullable=True)
    expiry_date = db.Column(db.Date, nullable=False)
    unit_cost_price = db.Column(db.Float, nullable=False)
    unit_selling_price = db.Column(db.Float, nullable=False)
    quantity_left = db.Column(db.Integer, nullable=False)
    quantity_supplied = db.Column(db.Integer, nullable=False)

    # relationship to DispenseRecord
    dispenses = db.relationship("DispenseRecord", back_populates="drug", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Drug {self.name} ({self.brand_name})>"

    @property
    def dispensed_today(self):
        today = datetime.utcnow().date()
        return sum(
            d.quantity_dispensed for d in self.dispenses
            if d.dispensed_at.date() == today
        )

    @property
    def dispensed_month(self):
        now = datetime.utcnow()
        return sum(
            d.quantity_dispensed for d in self.dispenses
            if d.dispensed_at.year == now.year and d.dispensed_at.month == now.month
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand_name": self.brand_name,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "unit_cost_price": float(self.unit_cost_price),
            "unit_selling_price": float(self.unit_selling_price),
            "quantity_left": self.quantity_left,
            "dispensed_today": self.dispensed_today,
            "dispensed_month": self.dispensed_month,
        }
