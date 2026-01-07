from flask import Flask, render_template
from app.extensions import db, migrate, login_manager
from sqlalchemy import func



def create_app():
    import os
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_BeF3DsWwOnq5@ep-tiny-shape-ah6paoay-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)
    # app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_BeF3DsWwOnq5@ep-tiny-shape-ah6paoay-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    # app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres:John4u.com@localhost:5432/hospital_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallbacksecret")
    # "supersecret"

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # redirect unauthorized users to login

    # Import models AFTER db is initialized
    from app.models.user import User
    from app.models.employee import Employee, Role
    from app.models.patients import Patient
    from app.models.operation import OperationDiary
    from app.models.prescriptions import Prescription
    from app.models.inpatient import InPatientRecord
    from app.models.outpatient import OutPatientRecord
    from app.models.dispense import DispenseRecord
    from app.models.lab import LabVisit, LabRequest
    from app.models.drugs import Drug

    # Import blueprints AFTER login_manager is initialized
    from app.views.auth import auth_bp
    from app.views.doctor.doctor_views import doctor_bp
    from app.views.nurse.nurse_view import nurse_bp
    from app.views.admin.admin_views import admin_bp
    from app.views.patient.patient_views import patients_bp
    from app.views.chats.patients import patients_chat_bp
    from app.views.pharmacy.pharmacy_views import pharmacy_bp
    from app.views.lab.lab_views import lab_bp
    from app.views.surgery_views import surgery_bp
    from app.views.dispensary_views import dispensary_bp
    from app.views.finance_views import finance_bp
    from app.views.inpatient_views import inpatient_bp
    from app.views.outpatient_views import outpatient_bp
    from app.views.delivery_views import delivery_bp

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(nurse_bp, url_prefix="/nurse")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(patients_chat_bp, url_prefix="/chats/patients")
    app.register_blueprint(pharmacy_bp, url_prefix="/pharmacy")
    app.register_blueprint(lab_bp, url_prefix="/lab")
    app.register_blueprint(surgery_bp, url_prefix="/surgery")
    app.register_blueprint(dispensary_bp, url_prefix="/dispensary")
    app.register_blueprint(finance_bp, url_prefix="/finance")
    app.register_blueprint(inpatient_bp)
    app.register_blueprint(outpatient_bp)
    app.register_blueprint(delivery_bp)

    # Create superadmin automatically if not exists
    import os
    password = os.getenv("SUPERADMIN_PASSWORD")
    with app.app_context():
        try:
            db.create_all()
            # Check if superadmin exists
            if not User.query.filter_by(username="superadmin").first():
                
                # Ensure the role exists, default to string 'super_admin'
                sa_role_name = "super_admin"
                
                # Create the superadmin
                super_admin = User(
                    username="superadmin",
                    role=sa_role_name
                )
                super_admin.set_password("supersecure123")
                
                db.session.add(super_admin)
                db.session.commit()
                print("Super admin created! (username: superadmin / password: supersecure123)")
            else:
                print("Super admin already exists")
        except Exception as e:
            print(f"⚠️ Could not create/check superadmin: {e}")


    # Home route
    @app.route("/")
    def index():
        from app.models.lab import LabVisit
        latest_lab_request = LabRequest.query.order_by(LabRequest.created_at.desc()).first()
        return render_template("index.html", latest_lab_request=latest_lab_request)

    return app
