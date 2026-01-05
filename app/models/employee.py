from datetime import datetime, date
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy import Enum as SQLAEnum

class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    permissions = db.Column(db.Text, nullable=True)

    def has_permission(self, perm_name):
        if not self.permissions:
            return False
        return perm_name in self.permissions.split(",")
    
    def get_id(self):
        return f"admin-{self.id}"

    def __repr__(self):
        return f"<Role {self.name}>"

# Enum for shifts
class ShiftEnum(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    NIGHT = "Night"

class Employee(db.Model, UserMixin):
    __tablename__ = "employee"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    other_names = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    department = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    shift = db.Column(SQLAEnum(ShiftEnum, name="shiftenum", create_type=True), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    role = db.relationship("Role", backref=db.backref("employees", lazy=True))

    def full_name(self):
        return f"{self.first_name} {self.surname}"

    def can(self, permission):
        return self.role and self.role.has_permission(permission)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def role_name(self):
        return self.role.name.lower() if self.role else None
    
    def get_id(self):
        return f"employee-{self.id}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name(),
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "role": self.role.name if self.role else None
        }

    def __repr__(self):
        return f"<Employee {self.full_name()} - {self.role.name}>"

class EmployeeShift(db.Model):
    __tablename__ = "employee_shift"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    shift = db.Column(SQLAEnum(ShiftEnum, name="shiftenum", create_type=False), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)

    employee = db.relationship("Employee", backref=db.backref("shifts", lazy=True))

    def __repr__(self):
        return f"<{self.employee.full_name()} - {self.shift} on {self.date}>"
