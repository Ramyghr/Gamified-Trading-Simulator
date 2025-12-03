"""
Liquidation Engine - Background Worker
Monitors all open leveraged positions and liquidates when necessary.
Save as: app/services/liquidation_engine.py
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config.database import SessionLocal
from app.models.portfolio import Position, Portfolio, PositionSide
from app.services.leverage_trading_service import LeverageTradingService
from app.services.market_data_service import enhanced_market_service
from app.services.margin_service import margin_service

logger = logging.getLogger(__name__)


class LiquidationEngine:
    """
    Background worker that continuously monitors positions
    and liquidates those that reach their liquidation price.
    """
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 2  # Check every 2 seconds
        self.batch_size = 100  # Process positions in batches
        
        # Risk thresholds
        self.margin_call_threshold = Decimal("0.15")  # 15% above maintenance
        self.emergency_liquidation_threshold = Decimal("0.05")  # 5% buffer
    
    async def start(self):
        """Start the liquidation engine"""
        self.is_running = True
        logger.info("🚨 Liquidation Engine started")
        
        while self.is_running:
            try:
                await self.monitor_positions()
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in liquidation engine loop: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the liquidation engine"""
        self.is_running = False
        logger.info("Liquidation Engine stopped")
    
    async def monitor_positions(self):
        """Monitor all open positions for liquidation conditions"""
        db = SessionLocal()
        try:
            # Get all open positions
            positions = db.query(Position).filter(
                and_(
                    Position.is_open == True,
                    Position.is_liquidated == False
                )
            ).limit(self.batch_size).all()
            
            if not positions:
                return
            
            logger.debug(f"Monitoring {len(positions)} open positions")
            
            # Group by symbol for efficient price fetching
            positions_by_symbol = {}
            for pos in positions:
                if pos.symbol not in positions_by_symbol:
                    positions_by_symbol[pos.symbol] = []
                positions_by_symbol[pos.symbol].append(pos)
            
            # Check each symbol's positions
            for symbol, symbol_positions in positions_by_symbol.items():
                await self._check_symbol_positions(db, symbol, symbol_positions)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()
    
    async def _check_symbol_positions(
        self,
        db: Session,
        symbol: str,
        positions: List[Position]
    ):
        """Check all positions for a specific symbol"""
        try:
            # Get current market price
            price = await enhanced_market_service.get_price(symbol, "STOCK", force_refresh=True)
            
            if not price or price <= 0:
                logger.warning(f"Invalid price for {symbol}, skipping liquidation check")
                return
            
            current_price = Decimal(str(price))
            
            # Check each position
            for position in positions:
                await self._check_position_liquidation(db, position, current_price)
                
        except Exception as e:
            logger.error(f"Error checking positions for {symbol}: {str(e)}")
    
    async def _check_position_liquidation(
        self,
        db: Session,
        position: Position,
        current_price: Decimal
    ):
        """Check if a single position should be liquidated"""
        try:
            liquidation_price = Decimal(str(position.liquidation_price))
            side = position.side
            
            # Check if liquidation condition is met
            should_liquidate, distance = margin_service.check_liquidation_risk(
                current_price, liquidation_price, side.value
            )
            
            if should_liquidate:
                logger.warning(
                    f"🚨 LIQUIDATION TRIGGERED: Position {position.id}, "
                    f"Symbol={position.symbol}, Side={side.value}, "
                    f"Current={current_price}, Liq={liquidation_price}"
                )
                
                # Execute liquidation
                trading_service = LeverageTradingService(db)
                await trading_service.liquidate_position(
                    position, current_price, reason="Price reached liquidation level"
                )
                
            elif distance < self.margin_call_threshold:
                # Position is close to liquidation - log warning
                logger.warning(
                    f"⚠️  MARGIN CALL WARNING: Position {position.id}, "
                    f"Symbol={position.symbol}, Distance={distance:.2f}%"
                )
                
                # Could send notification to user here
                await self._send_margin_call_notification(position, distance)
                
        except Exception as e:
            logger.error(f"Error checking position {position.id}: {str(e)}")
    
    async def _send_margin_call_notification(
        self,
        position: Position,
        distance_from_liquidation: Decimal
    ):
        """
        Send margin call notification to user.
        Implement your notification logic here (email, push, websocket, etc.)
        """
        try:
            # TODO: Implement notification system
            logger.info(
                f"Margin call notification for user {position.user_id}, "
                f"position {position.id}, distance: {distance_from_liquidation:.2f}%"
            )
            
            # Example: Send via websocket, email, or push notification
            # await websocket_manager.send_to_user(position.user_id, {
            #     "type": "MARGIN_CALL_WARNING",
            #     "position_id": position.id,
            #     "symbol": position.symbol,
            #     "distance_from_liquidation": float(distance_from_liquidation)
            # })
            
        except Exception as e:
            logger.error(f"Error sending margin call notification: {str(e)}")
    
    async def emergency_liquidation_check(self):
        """
        Emergency check for positions that need immediate liquidation.
        Can be called manually or triggered by extreme market conditions.
        """
        db = SessionLocal()
        try:
            logger.warning("🚨 Running emergency liquidation check")
            
            positions = db.query(Position).filter(
                and_(
                    Position.is_open == True,
                    Position.is_liquidated == False
                )
            ).all()
            
            liquidation_count = 0
            
            for position in positions:
                try:
                    # Get current price
                    price = await enhanced_market_service.get_price(
                        position.symbol, "STOCK", force_refresh=True
                    )
                    
                    if not price or price <= 0:
                        continue
                    
                    current_price = Decimal(str(price))
                    liquidation_price = Decimal(str(position.liquidation_price))
                    
                    should_liquidate, _ = margin_service.check_liquidation_risk(
                        current_price, liquidation_price, position.side.value
                    )
                    
                    if should_liquidate:
                        trading_service = LeverageTradingService(db)
                        await trading_service.liquidate_position(
                            position, current_price, reason="Emergency liquidation"
                        )
                        liquidation_count += 1
                        
                except Exception as e:
                    logger.error(f"Error in emergency liquidation for position {position.id}: {str(e)}")
                    continue
            
            db.commit()
            logger.warning(f"Emergency liquidation complete: {liquidation_count} positions liquidated")
            
            return liquidation_count
            
        except Exception as e:
            logger.error(f"Error in emergency liquidation check: {str(e)}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    async def check_portfolio_margin_levels(self):
        """
        Check all portfolios for low margin levels.
        Useful for risk monitoring and reporting.
        """
        db = SessionLocal()
        try:
            portfolios = db.query(Portfolio).filter(
                Portfolio.margin_used > 0
            ).all()
            
            at_risk_portfolios = []
            
            for portfolio in portfolios:
                margin_level = Decimal(str(portfolio.margin_level))
                
                # Margin level below 120% is concerning
                if margin_level < Decimal("120"):
                    at_risk_portfolios.append({
                        "portfolio_id": portfolio.id,
                        "user_id": portfolio.user_id,
                        "margin_level": float(margin_level),
                        "equity": float(portfolio.equity),
                        "margin_used": float(portfolio.margin_used)
                    })
            
            if at_risk_portfolios:
                logger.warning(
                    f"⚠️  {len(at_risk_portfolios)} portfolios at risk of liquidation"
                )
                
                # Could send alerts to admin or users
                for portfolio_data in at_risk_portfolios:
                    logger.warning(f"At-risk portfolio: {portfolio_data}")
            
            return at_risk_portfolios
            
        except Exception as e:
            logger.error(f"Error checking portfolio margin levels: {str(e)}")
            return []
        finally:
            db.close()


# Global instance
liquidation_engine = LiquidationEngine()


async def start_liquidation_engine():
    """Start the liquidation engine background task"""
    await liquidation_engine.start()


async def stop_liquidation_engine():
    """Stop the liquidation engine background task"""
    await liquidation_engine.stop()


async def run_emergency_liquidation():
    """Run emergency liquidation check (manual trigger)"""
    return await liquidation_engine.emergency_liquidation_check()