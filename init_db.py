from sqlalchemy import create_engine
from models import Base
import os

DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_RT0BUKS9nlAf@ep-muddy-sound-a1pac0ue-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)

# Drop all tables (if they exist)
Base.metadata.drop_all(engine)

# Create all tables in correct order
Base.metadata.create_all(engine)
print("✅ Database tables recreated!")