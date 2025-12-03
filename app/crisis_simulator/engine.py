"""
Crisis Simulation Engine - FIXED VERSION
Auto-cancels pending orders on simulation end
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import asyncio
import logging

from app.models.crisis_simulator import (
    CrisisSimulation, SimulationParticipant, SimulationOrder, 
    SimulationLeaderboard, SimulationStatus, CrisisType
)
from app.crisis_simulator.time_compressor import TimeCompressor
from app.crisis_simulator.data_loader import HistoricalDataLoader
from app.crisis_simulator.historical_order_processor import HistoricalOrderProcessor

logger = logging.getLogger(__name__)


class SimulationEngine:
    """
    Main simulation engine - manages entire simulation lifecycle
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.data_loader = HistoricalDataLoader()
        self.active_simulations: Dict[int, Dict] = {}
        
    async def create_simulation(
        self,
        crisis_type: CrisisType,
        created_by: int,
        max_participants: int = 100,
        is_competitive: bool = True
    ) -> CrisisSimulation:
        """Create a new simulation instance"""
        try:
            time_compressor = TimeCompressor(crisis_type.value)
            start_date, end_date = self.data_loader.get_date_range(crisis_type.value)
            duration_minutes = time_compressor.get_total_duration_minutes()
            
            simulation = CrisisSimulation(
                crisis_type=crisis_type,
                status=SimulationStatus.PENDING,
                historical_start_date=start_date,
                historical_end_date=end_date,
                duration_minutes=duration_minutes,
                time_compression_ratio=0,
                phase_config=time_compressor.get_phase_config_dict(),
                created_by=created_by,
                max_participants=max_participants,
                is_competitive=is_competitive
            )
            
            self.db.add(simulation)
            self.db.commit()
            self.db.refresh(simulation)
            
            logger.info(f"Created simulation {simulation.id} for {crisis_type.value}")
            return simulation
            
        except Exception as e:
            logger.error(f"Error creating simulation: {e}")
            self.db.rollback()
            raise
    
    async def start_simulation(self, simulation_id: int) -> bool:
        """Start a pending simulation"""
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            if not simulation:
                raise ValueError(f"Simulation {simulation_id} not found")
            
            if simulation.status != SimulationStatus.PENDING:
                raise ValueError(f"Cannot start simulation in {simulation.status.value} state")
            
            time_compressor = TimeCompressor(simulation.crisis_type.value)
            real_start_time = datetime.utcnow()
            historical_start_time = time_compressor.start_simulation(real_start_time)
            
            simulation.status = SimulationStatus.ACTIVE
            simulation.real_start_time = real_start_time
            simulation.started_at = real_start_time
            simulation.current_historical_time = historical_start_time
            simulation.current_phase = time_compressor.phases[0].name
            
            self.db.commit()
            
            self.active_simulations[simulation_id] = {
                "time_compressor": time_compressor,
                "order_processor": HistoricalOrderProcessor(
                    self.data_loader, 
                    simulation.crisis_type.value
                ),
                "last_update": datetime.utcnow()
            }
            
            logger.info(f"Started simulation {simulation_id}")
            
            asyncio.create_task(self._simulation_update_loop(simulation_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting simulation: {e}")
            self.db.rollback()
            raise
    
    async def _simulation_update_loop(self, simulation_id: int):
        """Background loop for simulation updates"""
        logger.info(f"Starting update loop for simulation {simulation_id}")
        
        try:
            while True:
                await asyncio.sleep(1)
                
                simulation = self.db.query(CrisisSimulation).filter(
                    CrisisSimulation.id == simulation_id
                ).first()
                
                if not simulation or simulation.status not in [SimulationStatus.ACTIVE]:
                    logger.info(f"Stopping update loop for simulation {simulation_id}")
                    break
                
                await self._update_simulation_time(simulation_id)
                await self._process_pending_orders(simulation_id)
                await self._update_participant_portfolios(simulation_id)
                
                # Update leaderboard every 10 seconds
                if int(datetime.utcnow().timestamp()) % 10 == 0:
                    await self._update_leaderboard(simulation_id)
                
                # Check if simulation should end
                runtime_state = self.active_simulations.get(simulation_id)
                if runtime_state:
                    time_compressor = runtime_state["time_compressor"]
                    if time_compressor.is_simulation_complete(datetime.utcnow()):
                        await self._complete_simulation(simulation_id)
                        break
                        
        except Exception as e:
            logger.error(f"Error in simulation update loop: {e}")
    
    async def _update_simulation_time(self, simulation_id: int):
        """Update current historical time"""
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            runtime_state = self.active_simulations.get(simulation_id)
            if not runtime_state:
                return
            
            time_compressor = runtime_state["time_compressor"]
            current_real_time = datetime.utcnow()
            historical_time, phase_name, progress = time_compressor.real_to_historical(current_real_time)
            
            simulation.current_historical_time = historical_time
            simulation.current_phase = phase_name
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating simulation time: {e}")
            self.db.rollback()
    
    async def _process_pending_orders(self, simulation_id: int):
        """Process all pending orders - FIXED"""
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            runtime_state = self.active_simulations.get(simulation_id)
            if not runtime_state:
                return
            
            order_processor = runtime_state["order_processor"]
            
            pending_orders = self.db.query(SimulationOrder).join(
                SimulationParticipant
            ).filter(
                SimulationParticipant.simulation_id == simulation_id,
                SimulationOrder.status == "PENDING"
            ).all()
            
            for order in pending_orders:
                participant = order.participant
                
                if order.order_type == "LIMIT":
                    order_processor.execute_limit_order(
                        order, participant, simulation.current_historical_time, self.db
                    )
                elif order.order_type == "STOP":
                    order_processor.execute_stop_order(
                        order, participant, simulation.current_historical_time, self.db
                    )
                    
        except Exception as e:
            logger.error(f"Error processing pending orders: {e}")
    
    async def _update_participant_portfolios(self, simulation_id: int):
        """Update portfolio values for all participants"""
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            runtime_state = self.active_simulations.get(simulation_id)
            if not runtime_state:
                return
            
            order_processor = runtime_state["order_processor"]
            
            participants = self.db.query(SimulationParticipant).filter(
                SimulationParticipant.simulation_id == simulation_id,
                SimulationParticipant.is_active == True
            ).all()
            
            for participant in participants:
                total_value = order_processor.calculate_portfolio_value(
                    participant, simulation.current_historical_time, self.db
                )
                
                participant.current_portfolio_value = total_value - participant.current_cash
                participant.current_total_value = total_value
                participant.total_return_pct = (
                    (total_value / participant.initial_portfolio_value - 1) * 100
                )
                
                # Update max drawdown
                if participant.total_return_pct < participant.max_drawdown_pct:
                    participant.max_drawdown_pct = participant.total_return_pct
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating participant portfolios: {e}")
            self.db.rollback()
    
    async def _update_leaderboard(self, simulation_id: int):
        """Update competitive leaderboard rankings"""
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            if not simulation.is_competitive:
                return
            
            participants = self.db.query(SimulationParticipant).filter(
                SimulationParticipant.simulation_id == simulation_id,
                SimulationParticipant.is_active == True
            ).order_by(
                SimulationParticipant.total_return_pct.desc()
            ).all()
            
            # Clear existing leaderboard
            self.db.query(SimulationLeaderboard).filter(
                SimulationLeaderboard.simulation_id == simulation_id
            ).delete()
            
            # Create new leaderboard entries
            for rank, participant in enumerate(participants, 1):
                competition_score = (
                    participant.total_return_pct * 0.6 +
                    (participant.sharpe_ratio or 0) * 20 * 0.3 +
                    abs(participant.max_drawdown_pct) * -0.1
                )
                
                leaderboard_entry = SimulationLeaderboard(
                    simulation_id=simulation_id,
                    user_id=participant.user_id,
                    current_rank=rank,
                    total_value=participant.current_total_value,
                    total_return_pct=participant.total_return_pct,
                    sharpe_ratio=participant.sharpe_ratio,
                    competition_score=competition_score,
                    snapshot_at_historical=simulation.current_historical_time
                )
                
                self.db.add(leaderboard_entry)
                participant.final_rank = rank
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")
            self.db.rollback()
    
    async def _complete_simulation(self, simulation_id: int):
        """
        Mark simulation as completed - FIXED
        Auto-cancels all pending orders
        """
        try:
            simulation = self.db.query(CrisisSimulation).filter(
                CrisisSimulation.id == simulation_id
            ).first()
            
            # Cancel all pending orders
            pending_orders = self.db.query(SimulationOrder).join(
                SimulationParticipant
            ).filter(
                SimulationParticipant.simulation_id == simulation_id,
                SimulationOrder.status == "PENDING"
            ).all()
            
            for order in pending_orders:
                order.status = "CANCELLED"
                order.rejection_reason = "Simulation ended"
            
            logger.info(f"Cancelled {len(pending_orders)} pending orders on simulation end")
            
            simulation.status = SimulationStatus.COMPLETED
            simulation.completed_at = datetime.utcnow()
            simulation.real_end_time = datetime.utcnow()
            
            # Final leaderboard update
            await self._update_leaderboard(simulation_id)
            
            # Remove from active simulations
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
            
            self.db.commit()
            
            logger.info(f"Simulation {simulation_id} completed")
            
        except Exception as e:
            logger.error(f"Error completing simulation: {e}")
            self.db.rollback()
    
    async def pause_simulation(self, simulation_id: int) -> bool:
        """Pause an active simulation"""
        simulation = self.db.query(CrisisSimulation).filter(
            CrisisSimulation.id == simulation_id
        ).first()
        
        if simulation and simulation.status == SimulationStatus.ACTIVE:
            simulation.status = SimulationStatus.PAUSED
            self.db.commit()
            return True
        
        return False
    
    async def resume_simulation(self, simulation_id: int) -> bool:
        """Resume a paused simulation"""
        simulation = self.db.query(CrisisSimulation).filter(
            CrisisSimulation.id == simulation_id
        ).first()
        
        if simulation and simulation.status == SimulationStatus.PAUSED:
            simulation.status = SimulationStatus.ACTIVE
            self.db.commit()
            
            asyncio.create_task(self._simulation_update_loop(simulation_id))
            return True
        
        return False