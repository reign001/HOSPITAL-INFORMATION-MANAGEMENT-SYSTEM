from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres:John4u.com@localhost:5432/hospital_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "supersecret"

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # redirect unauthorized users to login page

    # Import models after db is initialized
    from app import models
    from app.models import User

    # Create superadmin automatically if not exists
    with app.app_context():
        try:
            if not User.query.filter_by(username="superadmin").first():
                super_admin = User(username="superadmin", role="super_admin")
                super_admin.set_password("supersecure123")
                db.session.add(super_admin)
                db.session.commit()
                print("✅ Super admin created! (username: superadmin / password: supersecure123)")
            else:
                print("ℹ️ Super admin already exists")
        except Exception as e:
            print(f"⚠️ Could not create/check superadmin: {e}")

    # Register blueprints
    from app.views.patient_views import patient_bp
    from app.views.pharmacy_views import pharmacy_bp
    from app.views.lab_views import lab_bp
    from app.views.auth import auth_bp
    from app.views.surgery_views import surgery_bp
    from app.views.dispensary_views import dispensary_bp
    from app.views.staff_views import staff_bp
    from app.views.finance_views import finance_bp
    from app.views.inpatient_views import inpatient_bp
    from app.views.outpatient_views import outpatient_bp
    from app.views.delivery_views import delivery_bp
    from app.views.doctor_views import doctor_bp
    from app.views.nurse_views import nurse_bp


    
    app.register_blueprint(nurse_bp)
    app.register_blueprint(doctor_bp, url_prefix="/doctor")
    app.register_blueprint(patient_bp, url_prefix="/patients")
    app.register_blueprint(pharmacy_bp, url_prefix="/pharmacy")
    app.register_blueprint(lab_bp, url_prefix="/lab")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(surgery_bp, url_prefix="/surgery")
    app.register_blueprint(dispensary_bp, url_prefix="/dispensary")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(finance_bp, url_prefix="/finance")
    app.register_blueprint(inpatient_bp)
    app.register_blueprint(outpatient_bp)
    app.register_blueprint(delivery_bp)

    # -------------------
    # Homepage / Dashboard
    # -------------------
    @app.route("/")
    @login_required
    def index():
        # Example: show latest lab visit
        from app.models import LabVisit
        latest_visit = LabVisit.query.order_by(LabVisit.id.desc()).first()
        return render_template("index.html", latest_visit=latest_visit)

    return app
