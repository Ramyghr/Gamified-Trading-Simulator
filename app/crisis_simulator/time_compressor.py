"""
Time Compression Engine
Manages mapping between real-world time and historical time during simulations
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class PhaseConfig:
    """Configuration for a single phase of a crisis"""
    name: str
    historical_start: datetime
    historical_end: datetime
    real_duration_minutes: float  # How long this phase takes in real time
    compression_ratio: float  # Calculated: historical_days / real_seconds


class TimeCompressor:
    """
    Handles time compression for crisis simulations
    Maps real-world seconds to historical timestamps with phase-aware acceleration
    """
    
    # Crisis Phase Configurations
    CRISIS_PHASES = {
        "great_depression": [
            {"name": "bubble", "start": "1928-01-01", "end": "1929-09-03", "real_minutes": 5},
            {"name": "crash", "start": "1929-09-04", "end": "1929-11-13", "real_minutes": 10},
            {"name": "decline", "start": "1929-11-14", "end": "1932-07-08", "real_minutes": 20},
            {"name": "recovery", "start": "1932-07-09", "end": "1939-12-31", "real_minutes": 25},
        ],
        "black_monday": [
            {"name": "pre_crash", "start": "1987-08-01", "end": "1987-10-16", "real_minutes": 15},
            {"name": "crash_week", "start": "1987-10-19", "end": "1987-10-23", "real_minutes": 20},
            {"name": "aftermath", "start": "1987-10-26", "end": "1987-12-31", "real_minutes": 10},
        ],
        "dotcom_bubble": [
            {"name": "bubble_formation", "start": "1998-01-01", "end": "1999-12-31", "real_minutes": 15},
            {"name": "bubble_peak", "start": "2000-01-01", "end": "2000-03-31", "real_minutes": 10},
            {"name": "crash_phase", "start": "2000-04-01", "end": "2002-10-31", "real_minutes": 25},
            {"name": "recovery_start", "start": "2002-11-01", "end": "2003-12-31", "real_minutes": 10},
        ],
        "financial_crisis_2008": [
            {"name": "buildup", "start": "2007-01-01", "end": "2008-07-31", "real_minutes": 15},
            {"name": "peak_crisis", "start": "2008-08-01", "end": "2009-03-31", "real_minutes": 25},
            {"name": "recovery", "start": "2009-04-01", "end": "2009-12-31", "real_minutes": 20},
        ],
        "covid_crash": [
            {"name": "pre_covid", "start": "2020-01-01", "end": "2020-01-31", "real_minutes": 5},
            {"name": "initial_decline", "start": "2020-02-01", "end": "2020-02-29", "real_minutes": 10},
            {"name": "crash_phase", "start": "2020-03-01", "end": "2020-03-31", "real_minutes": 15},
            {"name": "recovery", "start": "2020-04-01", "end": "2020-06-30", "real_minutes": 15},
            {"name": "tech_surge", "start": "2020-07-01", "end": "2020-09-30", "real_minutes": 10},
            {"name": "normalization", "start": "2020-10-01", "end": "2020-12-31", "real_minutes": 5},
        ],
    }
    
    def __init__(self, crisis_type: str):
        """
        Initialize time compressor for a specific crisis
        
        Args:
            crisis_type: One of the crisis types (great_depression, black_monday, etc.)
        """
        self.crisis_type = crisis_type
        self.phases = self._build_phase_configs()
        self.simulation_start_real_time: Optional[datetime] = None
        self.simulation_start_historical_time: Optional[datetime] = None
        
    def _build_phase_configs(self) -> list[PhaseConfig]:
        """Build phase configuration objects with calculated compression ratios"""
        phase_defs = self.CRISIS_PHASES.get(self.crisis_type, [])
        configs = []
        
        for phase_def in phase_defs:
            hist_start = datetime.strptime(phase_def["start"], "%Y-%m-%d")
            hist_end = datetime.strptime(phase_def["end"], "%Y-%m-%d")
            real_minutes = phase_def["real_minutes"]
            
            # Calculate compression ratio
            historical_days = (hist_end - hist_start).days
            real_seconds = real_minutes * 60
            compression_ratio = historical_days / real_seconds if real_seconds > 0 else 0
            
            configs.append(PhaseConfig(
                name=phase_def["name"],
                historical_start=hist_start,
                historical_end=hist_end,
                real_duration_minutes=real_minutes,
                compression_ratio=compression_ratio
            ))
        
        return configs
    
    def start_simulation(self, real_start_time: datetime) -> datetime:
        """
        Initialize simulation timing
        
        Args:
            real_start_time: When the simulation starts in real world
            
        Returns:
            Historical start time
        """
        self.simulation_start_real_time = real_start_time
        self.simulation_start_historical_time = self.phases[0].historical_start
        return self.simulation_start_historical_time
    
    def real_to_historical(self, real_time: datetime) -> Tuple[datetime, str, float]:
        """
        Convert real-world time to historical time
        
        Args:
            real_time: Current real-world timestamp
            
        Returns:
            Tuple of (historical_time, current_phase_name, progress_percentage)
        """
        if not self.simulation_start_real_time:
            raise ValueError("Simulation not started. Call start_simulation() first.")
        
        # Calculate elapsed real time
        elapsed_real_seconds = (real_time - self.simulation_start_real_time).total_seconds()
        
        # Find current phase and calculate historical time
        cumulative_real_seconds = 0
        
        for phase in self.phases:
            phase_duration_seconds = phase.real_duration_minutes * 60
            
            if elapsed_real_seconds < cumulative_real_seconds + phase_duration_seconds:
                # We're in this phase
                phase_elapsed_seconds = elapsed_real_seconds - cumulative_real_seconds
                
                # Calculate historical time within this phase
                historical_days_elapsed = phase_elapsed_seconds * phase.compression_ratio
                historical_time = phase.historical_start + timedelta(days=historical_days_elapsed)
                
                # Calculate progress through simulation
                total_duration = sum(p.real_duration_minutes * 60 for p in self.phases)
                progress_pct = (elapsed_real_seconds / total_duration) * 100
                
                return historical_time, phase.name, progress_pct
            
            cumulative_real_seconds += phase_duration_seconds
        
        # Simulation has ended
        final_phase = self.phases[-1]
        return final_phase.historical_end, final_phase.name, 100.0
    
    def historical_to_real(self, historical_time: datetime) -> datetime:
        """
        Convert historical time back to real-world time (for scheduling)
        
        Args:
            historical_time: A point in historical time
            
        Returns:
            Corresponding real-world time
        """
        if not self.simulation_start_real_time:
            raise ValueError("Simulation not started.")
        
        cumulative_real_seconds = 0
        
        for phase in self.phases:
            if phase.historical_start <= historical_time <= phase.historical_end:
                # Calculate how far into this phase historically
                historical_days_into_phase = (historical_time - phase.historical_start).days
                
                # Convert to real seconds
                real_seconds_into_phase = historical_days_into_phase / phase.compression_ratio
                
                return self.simulation_start_real_time + timedelta(
                    seconds=cumulative_real_seconds + real_seconds_into_phase
                )
            
            cumulative_real_seconds += phase.real_duration_minutes * 60
        
        # If not found, return end time
        total_duration = sum(p.real_duration_minutes * 60 for p in self.phases)
        return self.simulation_start_real_time + timedelta(seconds=total_duration)
    
    def get_total_duration_minutes(self) -> float:
        """Get total real-world duration of simulation in minutes"""
        return sum(phase.real_duration_minutes for phase in self.phases)
    
    def get_phase_info(self, phase_name: str) -> Optional[PhaseConfig]:
        """Get configuration for a specific phase"""
        for phase in self.phases:
            if phase.name == phase_name:
                return phase
        return None
    
    def get_current_phase(self, real_time: datetime) -> Optional[PhaseConfig]:
        """Get the current phase configuration"""
        _, phase_name, _ = self.real_to_historical(real_time)
        return self.get_phase_info(phase_name)
    
    def is_simulation_complete(self, real_time: datetime) -> bool:
        """Check if simulation has reached its end"""
        elapsed_seconds = (real_time - self.simulation_start_real_time).total_seconds()
        total_duration_seconds = self.get_total_duration_minutes() * 60
        return elapsed_seconds >= total_duration_seconds
    
    def get_phase_config_dict(self) -> Dict:
        """
        Export phase configuration as dictionary for database storage
        
        Returns:
            Dictionary with phase configurations
        """
        return {
            phase.name: {
                "historical_start": phase.historical_start.isoformat(),
                "historical_end": phase.historical_end.isoformat(),
                "real_duration_minutes": phase.real_duration_minutes,
                "compression_ratio": phase.compression_ratio
            }
            for phase in self.phases
        }