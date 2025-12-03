#!/usr/bin/env python3
"""
Script to create crisis simulator tables
"""
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine
from app.models.base import Base
from app.models.crisis_simulator import *

def create_crisis_tables():
    """Create all crisis simulator tables"""
    print("Creating crisis simulator tables...")
    
    # Create all tables that don't exist yet
    Base.metadata.create_all(bind=engine, tables=[
        CrisisSimulation.__table__,
        SimulationParticipant.__table__,
        SimulationOrder.__table__,
        SimulationPosition.__table__,
        SimulationLeaderboard.__table__,
        SimulationSnapshot.__table__
    ])
    
    print("Crisis simulator tables created successfully!")

if __name__ == "__main__":
    create_crisis_tables()