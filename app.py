from app import create_app, db
import os
# from app.modelsx import User  # import models after db
from flask_login import login_manager

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
