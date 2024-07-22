import os, sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# POSTGRES_USER = os.getenv("POSTGRES_USER")
# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
# POSTGRES_HOST = os.getenv("POSTGRES_HOST")
# POSTGRES_DB = os.getenv("POSTGRES_DB")
# POSTGRES_PORT = os.getenv("POSTGRES_PORT", default=5432)

POSTGRES_URI = os.getenv("POSTGRES_URL")
#postgresql://unbtv:z66y7sfFA8uEGf5t7LQc2fP2UUTxzMhe@dpg-cqf64o0gph6c73b7iasg-a/unbtv

engine = create_engine(POSTGRES_URI)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
  db = SessionLocal()
  try:
      yield db
  finally:
      db.close()