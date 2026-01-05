# from app import db
# from app.modelsx import User

# user = User.query.filter_by(username="superadmin").first()
# if user:
#     user.set_password("supersecure123")
#     db.session.commit()
#     print("✅ Superadmin password reset to: supersecure123")
# else:
#     print("⚠️ No superadmin found!")

# from app import  app, db
# from app.models import Patient
# with app.app_context():
        
            
#             p.is_pending = True
#     db.session.commit()


# from app import create_app
# from app.extensions import db
# from app.models.employee import Role

# app = create_app()

# with app.app_context():
#     for r in Role.query.all():
#         r.name = r.name.lower()
#     db.session.commit()
#     print("Roles normalized to lowercase.")


from app import create_app
from app.extensions import db
from app.models.employee import Employee, Role

app = create_app()

with app.app_context():
    for e in Employee.query.all():
        print(e.id, e.first_name, e.role.name)