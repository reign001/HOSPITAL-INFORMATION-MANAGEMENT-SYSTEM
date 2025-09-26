from app import create_app, db
from app.models import User  # import models after db
from flask_login import login_manager

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
