# Create a test.py file
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("✅ Database connection successful!")
    connection.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")