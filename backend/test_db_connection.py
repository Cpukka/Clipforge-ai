# test_db_connection.py
from sqlalchemy import create_engine, text

# Your database URL
DATABASE_URL = "postgresql://postgres:Ubo%401234@localhost/clipforge"

print(f"Testing connection to: {DATABASE_URL.replace('Ubo%401234', '***')}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Check if clipforge database exists
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        print(f"✅ Connected to database: {db_name}")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")