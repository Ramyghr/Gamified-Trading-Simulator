"""
Comprehensive test script for the trading engine.
Run this to validate order placement, execution, and edge cases.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio, StockHolding
from app.models.order import Order, OrderType, OrderSide, OrderStatus
from app.schemas.order import OrderCreate
from app.services.trading_service import TradingService, InsufficientFundsError, InsufficientSharesError
from app.services.order_processor import process_orders_once


def setup_test_user(db: Session) -> User:
    """Create or get test user with portfolio"""
    user = db.query(User).filter(User.email == "test_trader@example.com").first()
    
    if not user:
        from app.utils.password_util import hash_password
        user = User(
            email="test_trader@example.com",
            username="test_trader",
            hashed_password=hash_password("testpass123"),
            first_name="Test",
            last_name="Trader",
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.flush()
    
    # Create or update portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user.id,
            cash_balance=Decimal("100000.00"),  # $100k starting cash
            reserved_cash=Decimal("0.00")
        )
        db.add(portfolio)
    else:
        portfolio.cash_balance = Decimal("100000.00")
        portfolio.reserved_cash = Decimal("0.00")
    
    # Clear existing holdings
    db.query(StockHolding).filter(StockHolding.portfolio_id == portfolio.id).delete()
    
    db.commit()
    db.refresh(user)
    return user


def test_market_order_buy(db: Session, user: User):
    """Test 1: Market order BUY"""
    print("\n" + "="*60)
    print("TEST 1: Market Order BUY")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=Decimal("10"),
            idempotency_key="test_market_buy_1"
        )
        
        order = trading_service.create_order(user.id, order_data)
        
        print(f"✓ Order created: ID={order.id}")
        print(f"  Status: {order.status}")
        print(f"  Filled: {order.filled_quantity}/{order.quantity}")
        print(f"  Avg Price: ${order.average_fill_price}")
        print(f"  Total Fees: ${order.total_fees}")
        
        # Check portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        holding = db.query(StockHolding).filter(
            StockHolding.portfolio_id == portfolio.id,
            StockHolding.symbol == "AAPL"
        ).first()
        
        print(f"  Cash Balance: ${portfolio.cash_balance}")
        print(f"  Shares Owned: {holding.quantity if holding else 0}")
        
        assert order.status == OrderStatus.FILLED, "Order should be filled"
        assert holding is not None, "Holding should exist"
        assert holding.quantity == Decimal("10"), "Should own 10 shares"
        
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


def test_market_order_sell(db: Session, user: User):
    """Test 2: Market order SELL"""
    print("\n" + "="*60)
    print("TEST 2: Market Order SELL")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        # First, ensure user has shares to sell
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        holding = db.query(StockHolding).filter(
            StockHolding.portfolio_id == portfolio.id,
            StockHolding.symbol == "AAPL"
        ).first()
        
        if not holding or holding.quantity < 5:
            print("✗ TEST SKIPPED: Insufficient shares")
            return False
        
        cash_before = portfolio.cash_balance
        
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            quantity=Decimal("5"),
            idempotency_key="test_market_sell_1"
        )
        
        order = trading_service.create_order(user.id, order_data)
        
        print(f"✓ Order created: ID={order.id}")
        print(f"  Status: {order.status}")
        print(f"  Filled: {order.filled_quantity}/{order.quantity}")
        print(f"  Avg Price: ${order.average_fill_price}")
        
        # Check portfolio
        db.refresh(portfolio)
        db.refresh(holding)
        
        print(f"  Cash Before: ${cash_before}")
        print(f"  Cash After: ${portfolio.cash_balance}")
        print(f"  Shares Left: {holding.quantity}")
        
        assert order.status == OrderStatus.FILLED, "Order should be filled"
        assert portfolio.cash_balance > cash_before, "Cash should increase"
        
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


def test_limit_order_buy(db: Session, user: User):
    """Test 3: Limit order BUY (pending)"""
    print("\n" + "="*60)
    print("TEST 3: Limit Order BUY (Pending)")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        # Place limit order at price below market
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=Decimal("5"),
            price=Decimal("100.00"),  # Below market price
            idempotency_key="test_limit_buy_1"
        )
        
        order = trading_service.create_order(user.id, order_data)
        
        print(f"✓ Order created: ID={order.id}")
        print(f"  Status: {order.status}")
        print(f"  Limit Price: ${order.price}")
        
        # Check portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        print(f"  Reserved Cash: ${portfolio.reserved_cash}")
        
        assert order.status == OrderStatus.PENDING, "Order should be pending"
        assert portfolio.reserved_cash > 0, "Cash should be reserved"
        
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


def test_insufficient_funds(db: Session, user: User):
    """Test 4: Insufficient funds error"""
    print("\n" + "="*60)
    print("TEST 4: Insufficient Funds Error")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        # Try to buy more than we can afford
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=Decimal("10000"),  # Way too many shares
            idempotency_key="test_insufficient_funds_1"
        )
        
        try:
            order = trading_service.create_order(user.id, order_data)
            print("✗ TEST FAILED: Should have raised InsufficientFundsError")
            return False
        except InsufficientFundsError as e:
            print(f"✓ Correctly raised error: {str(e)}")
            print("✓ TEST PASSED")
            return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: Unexpected error: {str(e)}")
        return False


def test_insufficient_shares(db: Session, user: User):
    """Test 5: Insufficient shares error"""
    print("\n" + "="*60)
    print("TEST 5: Insufficient Shares Error")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        # Try to sell more shares than we own
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            quantity=Decimal("10000"),  # Don't own this many
            idempotency_key="test_insufficient_shares_1"
        )
        
        try:
            order = trading_service.create_order(user.id, order_data)
            print("✗ TEST FAILED: Should have raised InsufficientSharesError")
            return False
        except InsufficientSharesError as e:
            print(f"✓ Correctly raised error: {str(e)}")
            print("✓ TEST PASSED")
            return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: Unexpected error: {str(e)}")
        return False


def test_order_cancellation(db: Session, user: User):
    """Test 6: Order cancellation"""
    print("\n" + "="*60)
    print("TEST 6: Order Cancellation")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        # Create a pending limit order
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=Decimal("10"),
            price=Decimal("50.00"),  # Very low price
            idempotency_key="test_cancel_1"
        )
        
        order = trading_service.create_order(user.id, order_data)
        print(f"✓ Order created: ID={order.id}")
        
        # Get reserved cash before
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        reserved_before = portfolio.reserved_cash
        print(f"  Reserved before: ${reserved_before}")
        
        # Cancel the order
        canceled_order = trading_service.cancel_order(user.id, order.id)
        
        print(f"✓ Order canceled: ID={canceled_order.id}")
        print(f"  Status: {canceled_order.status}")
        
        # Check reserved cash is released
        db.refresh(portfolio)
        print(f"  Reserved after: ${portfolio.reserved_cash}")
        
        assert canceled_order.status == OrderStatus.CANCELED, "Order should be canceled"
        assert portfolio.reserved_cash < reserved_before, "Reserved cash should decrease"
        
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


def test_idempotency(db: Session, user: User):
    """Test 7: Idempotency key"""
    print("\n" + "="*60)
    print("TEST 7: Idempotency Key")
    print("="*60)
    
    try:
        trading_service = TradingService(db)
        
        idempotency_key = f"test_idempotency_{datetime.utcnow().timestamp()}"
        
        order_data = OrderCreate(
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("150.00"),
            idempotency_key=idempotency_key
        )
        
        # Create first order
        order1 = trading_service.create_order(user.id, order_data)
        print(f"✓ First order created: ID={order1.id}")
        
        # Try to create duplicate
        order2 = trading_service.create_order(user.id, order_data)
        print(f"✓ Second order returned: ID={order2.id}")
        
        assert order1.id == order2.id, "Should return same order for duplicate idempotency key"
        
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


async def test_order_processor(db: Session, user: User):
    """Test 8: Background order processor"""
    print("\n" + "="*60)
    print("TEST 8: Order Processor")
    print("="*60)
    
    try:
        # This test would require actual price data
        # For now, just verify the processor runs without errors
        print("  Running order processor...")
        await process_orders_once()
        print("✓ Order processor executed successfully")
        print("✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TRADING ENGINE TEST SUITE")
    print("="*60)
    
    db = SessionLocal()
    results = []
    
    try:
        # Setup
        print("\nSetting up test environment...")
        user = setup_test_user(db)
        print(f"✓ Test user created: {user.email}")
        
        # Run tests
        results.append(("Market Order BUY", test_market_order_buy(db, user)))
        results.append(("Market Order SELL", test_market_order_sell(db, user)))
        results.append(("Limit Order BUY", test_limit_order_buy(db, user)))
        results.append(("Insufficient Funds", test_insufficient_funds(db, user)))
        results.append(("Insufficient Shares", test_insufficient_shares(db, user)))
        results.append(("Order Cancellation", test_order_cancellation(db, user)))
        results.append(("Idempotency Key", test_idempotency(db, user)))
        results.append(("Order Processor", asyncio.run(test_order_processor(db, user))))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
        
        print(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()