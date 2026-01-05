# flush_db.py
from app import create_app, db
from sqlalchemy import text

def flush_database():
    """Completely clears all data from the database (preserving tables)."""
    try:
        print("⚙️ Flushing database...")

        # Disable foreign key constraints (for PostgreSQL)
        db.session.execute(text("SET session_replication_role = 'replica';"))

        # Truncate all tables in reverse order to handle dependencies
        for table in reversed(db.metadata.sorted_tables):
            print(f"🧹 Clearing table: {table.name}")
            db.session.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))

        # Re-enable foreign key constraints
        db.session.execute(text("SET session_replication_role = 'origin';"))

        db.session.commit()
        print("✅ Database flush completed successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error while flushing database: {e}")


if __name__ == "__main__":
    # ✅ Create the Flask app context before using db
    app = create_app()   # or: from app import app  (if you have app = Flask(__name__) globally)
    with app.app_context():
        flush_database()
