from sqlalchemy import create_engine, inspect
from database import engine  # Import from your existing database.py

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Existing tables:")
    for table in tables:
        print(f"- {table}")
    
    return tables

if __name__ == "__main__":
    check_tables()