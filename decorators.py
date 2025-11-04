from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user, login_required

def role_required(*roles):
    """Restrict access to users with specific roles"""
    def wrapper(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash("🚫 You don’t have permission to access this page.", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper
