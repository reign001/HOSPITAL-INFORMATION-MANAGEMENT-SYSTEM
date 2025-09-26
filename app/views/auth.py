from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User

from flask import Blueprint



auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# User logout
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

# Create initial super admin (for setup only!)
@auth_bp.route("/create_super_admin")
def create_super_admin():
    if User.query.filter_by(username="superadmin").first():
        flash("Super admin already exists!", "warning")
        return redirect(url_for("auth.login"))

    super_admin = User(username="superadmin", role="super_admin")
    super_admin.set_password("supersecure123")
    db.session.add(super_admin)
    db.session.commit()
    flash("Super admin account created! Username: superadmin", "success")
    return redirect(url_for("auth.login"))


# User login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("✅ Login successful!", "success")
            # Redirect to the dashboard / index page
            return redirect(url_for("index"))
        else:
            flash("❌ Invalid username or password", "danger")

    # GET request renders login page
    return render_template("auth/login.html")

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import User
from app.views.auth import auth_bp


# List all admins/superadmins
@auth_bp.route("/manage_admins")
def manage_admins():
    admins = User.query.filter(User.role.in_(["admin", "super_admin"])).all()
    return render_template("auth/manage_admins.html", admins=admins)


# Add a new admin or superadmin
@auth_bp.route("/add_admin", methods=["GET", "POST"])
def add_admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if User.query.filter_by(username=username).first():
            flash("⚠️ Username already exists!", "danger")
            return redirect(url_for("auth.add_admin"))

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"✅ {role.capitalize()} '{username}' created successfully!", "success")
        return redirect(url_for("auth.manage_admins"))

    return render_template("auth/add_admin.html")


# Reset admin/superadmin password
@auth_bp.route("/reset_superadmin", methods=["GET", "POST"])
def reset_superadmin():
    user = User.query.filter_by(username="superadmin").first()
    if not user:
        flash("⚠️ Superadmin not found in the system.", "danger")
        return redirect(url_for("auth.login"))

    # Reset password
    user.set_password("supersecure123")
    db.session.commit()

    flash("✅ Superadmin password has been reset to 'supersecure123'. Please change it after login.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route('/list_users')
@login_required
def list_users():
    users = User.query.all()
    return render_template("auth/list_users.html", users=users)