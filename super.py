from app import db
from app.models import User

# Create superadmin if not exists
superadmin = User.query.filter_by(username="superadmin").first()
if not superadmin:
    superadmin = User(
        username="superadmin",
        role="superadmin"   # 🔑 make sure role column exists
    )
    superadmin.set_password("supersecure123")
    db.session.add(superadmin)
    db.session.commit()
    print("✅ Superadmin created with password: supersecure123")
else:
    print("⚡ Superadmin already exists")
