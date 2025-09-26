from app import db
from app.models import User

user = User.query.filter_by(username="superadmin").first()
if user:
    user.set_password("supersecure123")
    db.session.commit()
    print("✅ Superadmin password reset to: supersecure123")
else:
    print("⚠️ No superadmin found!")
