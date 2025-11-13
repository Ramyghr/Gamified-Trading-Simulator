"""
Comprehensive test script for leverage trading engine.
Save as: scripts/test_leverage_system.py

Run with: python -m scripts.test_leverage_system
"""

import asyncio
import sys
from decimal import Decimal
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import SessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio, Position
from app.services.leverage_trading_service import LeverageTradingService
from app.services.margin_service import margin_service
from app.services.liquidation_engine import liquidation_engine

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeverageTradingTests:
    """Test suite for leverage trading system"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.trading_service = LeverageTradingService(self.db)
        self.test_user_id = None
        self.test_position_id = None
    
    def setup_test_user(self):
        """Create or get test user"""
        logger.info("Setting up test user...")
        
        user = self.db.query(User).filter(User.email == "test_leverage@example.com").first()
        
        if not user:
            user = User(
                first_name="Test",
                last_name="Trader",
                email="test_leverage@example.com",
                password_hash="test_hash",
                level=10
            )
            self.db.add(user)
            self.db.flush()
        
        self.test_user_id = user.id
        
        # Ensure portfolio exists
        portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        
        if not portfolio:
            portfolio = Portfolio(
                user_id=user.id,
                cash_balance=10000.00,
                initial_balance=10000.00,
                equity=10000.00,
                max_leverage=10.00
            )
            self.db.add(portfolio)
        else:
            # Reset portfolio for testing
            portfolio.cash_balance = 10000.00
            portfolio.equity = 10000.00
            portfolio.margin_used = 0.00
            portfolio.unrealized_pnl = 0.00
        
        self.db.commit()
        logger.info(f"✅ Test user ready: ID={self.test_user_id}")
    
    def test_margin_calculations(self):
        """Test 1: Margin calculation formulas"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Margin Calculations")
        logger.info("="*60)
        
        # Test parameters
        quantity = Decimal("10")
        entry_price = Decimal("150.00")
        leverage = Decimal("10")
        
        # Calculate margin
        margin = margin_service.calculate_margin_required(quantity, entry_price, leverage)
        logger.info(f"Margin required: ${margin}")
        assert margin == Decimal("150.00"), "Incorrect margin calculation"
        
        # Calculate liquidation prices
        liq_long = margin_service.calculate_liquidation_price_long(entry_price, leverage)
        liq_short = margin_service.calculate_liquidation_price_short(entry_price, leverage)
        
        logger.info(f"Liquidation price (LONG): ${liq_long}")
        logger.info(f"Liquidation price (SHORT): ${liq_short}")
        
        assert liq_long < entry_price, "LONG liquidation should be below entry"
        assert liq_short > entry_price, "SHORT liquidation should be above entry"
        
        # Test PnL calculations
        current_price = Decimal("155.00")
        pnl_long = margin_service.calculate_unrealized_pnl_long(quantity, entry_price, current_price)
        pnl_short = margin_service.calculate_unrealized_pnl_short(quantity, entry_price, current_price)
        
        logger.info(f"PnL LONG at $155: ${pnl_long}")
        logger.info(f"PnL SHORT at $155: ${pnl_short}")
        
        assert pnl_long == Decimal("50.00"), "LONG PnL incorrect"
        assert pnl_short == Decimal("-50.00"), "SHORT PnL incorrect"
        
        logger.info("✅ All margin calculations passed")
    
    async def test_open_long_position(self):
        """Test 2: Open a leveraged LONG position"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Open LONG Position")
        logger.info("="*60)
        
        try:
            position = await self.trading_service.open_leveraged_position(
                user_id=self.test_user_id,
                symbol="AAPL",
                side="LONG",
                quantity=Decimal("10"),
                leverage=Decimal("10"),
                stop_loss=Decimal("145.00"),
                take_profit=Decimal("165.00")
            )
            
            self.test_position_id = position.id
            
            logger.info(f"Position ID: {position.id}")
            logger.info(f"Symbol: {position.symbol}")
            logger.info(f"Side: {position.side}")
            logger.info(f"Quantity: {position.quantity}")
            logger.info(f"Entry Price: ${position.entry_price}")
            logger.info(f"Leverage: {position.leverage}x")
            logger.info(f"Margin Used: ${position.margin_used}")
            logger.info(f"Position Value: ${position.position_value}")
            logger.info(f"Liquidation Price: ${position.liquidation_price}")
            logger.info(f"Stop Loss: ${position.stop_loss_price}")
            logger.info(f"Take Profit: ${position.take_profit_price}")
            
            # Verify position
            assert position.is_open == True, "Position should be open"
            assert position.side.value == "LONG", "Should be LONG position"
            assert position.leverage == 10.0, "Leverage should be 10x"
            assert position.liquidation_price < position.entry_price, "Liquidation should be below entry"
            
            # Verify portfolio
            portfolio = self.db.query(Portfolio).filter(Portfolio.user_id == self.test_user_id).first()
            logger.info(f"\nPortfolio after opening:")
            logger.info(f"Cash Balance: ${portfolio.cash_balance}")
            logger.info(f"Margin Used: ${portfolio.margin_used}")
            logger.info(f"Equity: ${portfolio.equity}")
            
            assert float(portfolio.margin_used) > 0, "Margin should be reserved"
            
            logger.info("✅ LONG position opened successfully")
            return position
            
        except Exception as e:
            logger.error(f"❌ Failed to open LONG position: {str(e)}")
            raise
    
    async def test_open_short_position(self):
        """Test 3: Open a leveraged SHORT position"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Open SHORT Position")
        logger.info("="*60)
        
        try:
            position = await self.trading_service.open_leveraged_position(
                user_id=self.test_user_id,
                symbol="TSLA",
                side="SHORT",
                quantity=Decimal("5"),
                leverage=Decimal("5")
            )
            
            logger.info(f"Position ID: {position.id}")
            logger.info(f"Symbol: {position.symbol}")
            logger.info(f"Side: {position.side}")
            logger.info(f"Entry Price: ${position.entry_price}")
            logger.info(f"Liquidation Price: ${position.liquidation_price}")
            
            assert position.side.value == "SHORT", "Should be SHORT position"
            assert position.liquidation_price > position.entry_price, "Liquidation should be above entry"
            
            logger.info("✅ SHORT position opened successfully")
            return position
            
        except Exception as e:
            logger.error(f"❌ Failed to open SHORT position: {str(e)}")
            raise
    
    async def test_update_position_prices(self):
        """Test 4: Update position prices and PnL"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Update Position Prices")
        logger.info("="*60)
        
        position = self.trading_service.get_position_by_id(self.test_user_id, self.test_position_id)
        
        if not position:
            logger.warning("⚠️  No position to update")
            return
        
        logger.info(f"Position before update:")
        logger.info(f"Current Price: ${position.current_price}")
        logger.info(f"Unrealized PnL: ${position.unrealized_pnl}")
        
        # Update prices
        await self.trading_service.update_position_prices(position)
        self.db.commit()
        
        logger.info(f"\nPosition after update:")
        logger.info(f"Current Price: ${position.current_price}")
        logger.info(f"Unrealized PnL: ${position.unrealized_pnl}")
        logger.info(f"Last Update: {position.last_price_update}")
        
        logger.info("✅ Position prices updated")
    
    async def test_close_position(self):
        """Test 5: Close a position"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Close Position")
        logger.info("="*60)
        
        if not self.test_position_id:
            logger.warning("⚠️  No position to close")
            return
        
        # Get portfolio before
        portfolio_before = self.db.query(Portfolio).filter(
            Portfolio.user_id == self.test_user_id
        ).first()
        
        logger.info(f"Portfolio before closing:")
        logger.info(f"Cash: ${portfolio_before.cash_balance}")
        logger.info(f"Margin Used: ${portfolio_before.margin_used}")
        
        # Close position
        result = await self.trading_service.close_leveraged_position(
            user_id=self.test_user_id,
            position_id=self.test_position_id
        )
        
        logger.info(f"\nClosure result:")
        logger.info(f"Closed Quantity: {result['closed_quantity']}")
        logger.info(f"Exit Price: ${result['exit_price']}")
        logger.info(f"PnL: ${result['pnl']}")
        logger.info(f"Fee: ${result['fee']}")
        logger.info(f"Net PnL: ${result['net_pnl']}")
        logger.info(f"Margin Released: ${result['margin_released']}")
        
        # Get portfolio after
        portfolio_after = self.db.query(Portfolio).filter(
            Portfolio.user_id == self.test_user_id
        ).first()
        
        logger.info(f"\nPortfolio after closing:")
        logger.info(f"Cash: ${portfolio_after.cash_balance}")
        logger.info(f"Margin Used: ${portfolio_after.margin_used}")
        
        # Verify position is closed
        position = self.trading_service.get_position_by_id(self.test_user_id, self.test_position_id)
        assert position.is_open == False, "Position should be closed"
        
        logger.info("✅ Position closed successfully")
    
    async def test_liquidation_check(self):
        """Test 6: Liquidation engine check"""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Liquidation Engine")
        logger.info("="*60)
        
        # Run liquidation check
        logger.info("Running liquidation check...")
        await liquidation_engine.monitor_positions()
        
        logger.info("✅ Liquidation check completed")
    
    async def test_position_metrics(self):
        """Test 7: Calculate position metrics"""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: Position Metrics")
        logger.info("="*60)
        
        metrics = margin_service.calculate_position_metrics(
            side="LONG",
            quantity=Decimal("10"),
            entry_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            leverage=Decimal("10"),
            margin_used=Decimal("150.00")
        )
        
        logger.info(f"Unrealized PnL: ${metrics['unrealized_pnl']}")
        logger.info(f"PnL Percentage: {metrics['pnl_percentage']:.2f}%")
        logger.info(f"ROI: {metrics['roi']:.2f}%")
        logger.info(f"Liquidation Price: ${metrics['liquidation_price']}")
        logger.info(f"Distance from Liquidation: {metrics['distance_from_liquidation']:.2f}%")
        logger.info(f"Should Liquidate: {metrics['should_liquidate']}")
        
        logger.info("✅ Metrics calculated successfully")
    
    async def test_insufficient_margin(self):
        """Test 8: Handle insufficient margin"""
        logger.info("\n" + "="*60)
        logger.info("TEST 8: Insufficient Margin Error")
        logger.info("="*60)
        
        try:
            # Try to open position larger than available margin
            await self.trading_service.open_leveraged_position(
                user_id=self.test_user_id,
                symbol="AAPL",
                side="LONG",
                quantity=Decimal("1000"),  # Very large position
                leverage=Decimal("10")
            )
            
            logger.error("❌ Should have raised InsufficientMarginError")
            
        except Exception as e:
            if "Insufficient margin" in str(e):
                logger.info(f"✅ Correctly raised error: {str(e)}")
            else:
                logger.error(f"❌ Unexpected error: {str(e)}")
                raise
    
    def cleanup(self):
        """Clean up test data"""
        logger.info("\n" + "="*60)
        logger.info("Cleaning up test data...")
        logger.info("="*60)
        
        # Close all test positions
        positions = self.db.query(Position).filter(
            Position.user_id == self.test_user_id,
            Position.is_open == True
        ).all()
        
        for pos in positions:
            pos.is_open = False
            pos.closed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.close()
        
        logger.info("✅ Cleanup complete")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "🚀" * 30)
        logger.info("LEVERAGE TRADING SYSTEM - COMPREHENSIVE TESTS")
        logger.info("🚀" * 30)
        
        try:
            # Setup
            self.setup_test_user()
            
            # Run tests
            self.test_margin_calculations()
            await self.test_open_long_position()
            await self.test_open_short_position()
            await self.test_update_position_prices()
            await self.test_position_metrics()
            await self.test_close_position()
            await self.test_liquidation_check()
            await self.test_insufficient_margin()
            
            logger.info("\n" + "✅" * 30)
            logger.info("ALL TESTS PASSED SUCCESSFULLY!")
            logger.info("✅" * 30)
            
        except Exception as e:
            logger.error("\n" + "❌" * 30)
            logger.error(f"TEST FAILED: {str(e)}")
            logger.error("❌" * 30)
            import traceback
            traceback.print_exc()
            
        finally:
            self.cleanup()


async def main():
    """Main test runner"""
    tests = LeverageTradingTests()
    await tests.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())