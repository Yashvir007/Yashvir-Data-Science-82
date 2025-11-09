"""Small migration helper to add missing pdf_url column to Book table.

This script runs inside the Flask app context and uses SQLAlchemy engine to check
if the column exists and, if missing, runs an ALTER TABLE statement.

Usage:
    python db_migrate.py
"""
import os
from sqlalchemy import inspect, text
from customer.models import db
from app import app

ALIAS_DB_TABLE = 'book'
COLUMN_NAME = 'pdf_url'

with app.app_context():
    engine = db.get_engine()
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns(ALIAS_DB_TABLE)]
    if COLUMN_NAME in cols:
        print(f"Column '{COLUMN_NAME}' already exists in table '{ALIAS_DB_TABLE}'.")
    else:
        print(f"Adding column '{COLUMN_NAME}' to table '{ALIAS_DB_TABLE}'...")
        try:
            # Execute ALTER TABLE using a connection
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {ALIAS_DB_TABLE} ADD COLUMN {COLUMN_NAME} VARCHAR(300) NULL;"))
                conn.commit()
            print("Column added successfully.")
        except Exception as e:
            print("Failed to add column:", e)
            raise
