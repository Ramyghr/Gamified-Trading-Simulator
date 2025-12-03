# scripts/create_tables.py
from app.config.database import Base, engine
from app.models import *  # imports all your models

Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully")
