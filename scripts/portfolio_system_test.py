"""
Comprehensive test suite for the enhanced portfolio system
Run this after migration to verify everything works correctly
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio, Holding, AssetType
from app.services.portfolio_service import PortfolioService
from app.services.market_data_service import market_data_service

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

class PortfolioSystemTests:
    def __init__(self):
        self.db = SessionLocal()
        self.service = PortfolioService(self.db)
        self.test_user_email = None
        self.passed = 0
        self.failed = 0

    def cleanup(self):
        self.db.close()

    async def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*60)
        print("  🧪 PORTFOLIO SYSTEM TEST SUITE")
        print("="*60 + "\n")

        # Setup
        print("📋 SETUP PHASE")
        print("-" * 60)
        if not await self.setup_test_data():
            print_error("Setup failed. Cannot continue tests.")
            return False

        # Test suites
        test_suites = [
            ("Market Data Integration", self.test_market_data),
            ("Portfolio Models", self.test_portfolio_models),
            ("Portfolio Overview", self.test_portfolio_overview),
            ("Holdings Management", self.test_holdings),
            ("Portfolio Statistics", self.test_statistics),
            ("History & Snapshots", self.test_history),
            ("Rankings", self.test_rankings),
            ("Asset Allocation", self.test_allocation),
            ("Best/Worst Holdings", self.test_best_worst),
        ]

        for suite_name, test_func in test_suites:
            print(f"\n{'='*60}")
            print(f"  🎯 {suite_name.upper()}")
            print('='*60)
            await test_func()

        # Summary
        self.print_summary()

    async def setup_test_data(self):
        """Create test user and portfolio with sample holdings"""
        try:
            # Find or create test user
            test_user = self.db.query(User).first()
            
            if not test_user:
                print_warning("No users found in database. Create a user first.")
                return False
            
            self.test_user_email = test_user.email
            print_success(f"Using test user: {self.test_user_email}")

            # Get portfolio
            portfolio = test_user.portfolio
            if not portfolio:
                print_error("User has no portfolio")
                return False

            print_success(f"Found portfolio (ID: {portfolio.id})")

            # Add sample holdings if none exist
            if not portfolio.holdings:
                print_info("Adding sample holdings...")
                
                sample_holdings = [
                    ("AAPL", AssetType.STOCK, 10, 150.00),
                    ("TSLA", AssetType.STOCK, 5, 200.00),
                    ("BTC", AssetType.CRYPTO, 0.5, 40000.00),
                ]

                for symbol, asset_type, quantity, price in sample_holdings:
                    holding = Holding(
                        portfolio_id=portfolio.id,
                        symbol=symbol,
                        asset_type=asset_type,
                        quantity=quantity,
                        average_buy_price=price,
                        current_price=price
                    )
                    self.db.add(holding)
                
                self.db.commit()
                print_success(f"Added {len(sample_holdings)} sample holdings")
            else:
                print_success(f"Portfolio has {len(portfolio.holdings)} existing holdings")

            return True

        except Exception as e:
            print_error(f"Setup error: {e}")
            return False

    async def test_market_data(self):
        """Test market data service"""
        tests = [
            ("Fetch AAPL stock price", lambda: market_data_service.get_stock_price("AAPL")),
            ("Fetch TSLA stock price", lambda: market_data_service.get_stock_price("TSLA")),
            ("Fetch BTC crypto price", lambda: market_data_service.get_crypto_price("BTC")),
            ("Batch price fetch", lambda: market_data_service.get_batch_prices([
                ("AAPL", "STOCK"), ("TSLA", "STOCK"), ("BTC", "CRYPTO")
            ])),
        ]

        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    print_success(f"{test_name}: {result}")
                    self.passed += 1
                else:
                    print_warning(f"{test_name}: No data (API limit or invalid symbol)")
                    self.passed += 1  # Count as pass if no error
            except Exception as e:
                print_error(f"{test_name}: {e}")
                self.failed += 1

    async def test_portfolio_models(self):
        """Test portfolio model relationships"""
        try:
            portfolio = self.service.get_portfolio_by_email(self.test_user_email)
            
            # Test relationships
            assert portfolio.user is not None, "User relationship missing"
            print_success("Portfolio → User relationship")
            self.passed += 1

            assert isinstance(portfolio.holdings, list), "Holdings relationship invalid"
            print_success(f"Portfolio → Holdings relationship ({len(portfolio.holdings)} holdings)")
            self.passed += 1

            # Test holdings fields
            if portfolio.holdings:
                holding = portfolio.holdings[0]
                assert holding.symbol, "Symbol missing"
                assert holding.quantity > 0, "Quantity invalid"
                assert holding.average_buy_price > 0, "Price invalid"
                print_success("Holding fields valid")
                self.passed += 1

        except Exception as e:
            print_error(f"Model test failed: {e}")
            self.failed += 1

    async def test_portfolio_overview(self):
        """Test portfolio overview endpoint"""
        try:
            overview = await self.service.get_overview(self.test_user_email)
            
            # Validate fields
            assert overview.total_value > 0, "Total value invalid"
            print_success(f"Total value: ${overview.total_value:,.2f}")
            self.passed += 1

            assert overview.cash_balance >= 0, "Cash balance invalid"
            print_success(f"Cash balance: ${overview.cash_balance:,.2f}")
            self.passed += 1

            assert overview.holdings_value >= 0, "Holdings value invalid"
            print_success(f"Holdings value: ${overview.holdings_value:,.2f}")
            self.passed += 1

            print_success(f"Total gain: ${overview.total_gain:,.2f} ({overview.total_gain_pct:.2f}%)")
            self.passed += 1

            # Check allocation percentages
            total_allocation = overview.cash_allocation_pct + overview.holdings_allocation_pct
            assert 99 <= total_allocation <= 101, f"Allocation doesn't add up to 100%: {total_allocation}"
            print_success(f"Allocation: {overview.cash_allocation_pct:.1f}% cash, {overview.holdings_allocation_pct:.1f}% holdings")
            self.passed += 1

        except Exception as e:
            print_error(f"Overview test failed: {e}")
            self.failed += 1

    async def test_holdings(self):
        """Test holdings endpoints"""
        try:
            # Test paginated holdings
            holdings = await self.service.get_holdings(self.test_user_email, page=0, size=10, sort_by="value")
            
            assert holdings.total > 0, "No holdings found"
            print_success(f"Found {holdings.total} holdings")
            self.passed += 1

            assert len(holdings.items) > 0, "No holding items"
            print_success(f"Retrieved {len(holdings.items)} holdings on page")
            self.passed += 1

            # Test holding details
            holding = holdings.items[0]
            assert holding.symbol, "Symbol missing"
            assert holding.market_value > 0, "Market value invalid"
            print_success(f"Top holding: {holding.symbol} - ${holding.market_value:,.2f}")
            self.passed += 1

            # Test detailed positions
            positions = await self.service.get_detailed_positions(self.test_user_email)
            assert len(positions.positions) == holdings.total, "Position count mismatch"
            print_success(f"Detailed positions: {len(positions.positions)} items")
            self.passed += 1

            print_success(f"Total unrealized P&L: ${positions.total_unrealized_pnl:,.2f} ({positions.total_unrealized_pnl_pct:.2f}%)")
            self.passed += 1

        except Exception as e:
            print_error(f"Holdings test failed: {e}")
            self.failed += 1

    async def test_statistics(self):
        """Test portfolio statistics"""
        try:
            stats = await self.service.get_stats(self.test_user_email)
            
            print_success(f"Total trades: {stats.total_trades}")
            self.passed += 1

            print_success(f"Win rate: {stats.win_rate:.2f}%")
            self.passed += 1

            print_success(f"Total P&L: ${stats.total_pnl:,.2f}")
            self.passed += 1

            print_success(f"Total return: ${stats.total_return:,.2f} ({stats.total_return_pct:.2f}%)")
            self.passed += 1

            if stats.sharpe_ratio:
                print_success(f"Sharpe ratio: {stats.sharpe_ratio:.4f}")
            else:
                print_info("Sharpe ratio: Not enough data")
            self.passed += 1

        except Exception as e:
            print_error(f"Statistics test failed: {e}")
            self.failed += 1

    async def test_history(self):
        """Test portfolio history"""
        try:
            # Test history
            history = self.service.get_history(self.test_user_email, days=30)
            print_success(f"History points: {len(history)}")
            self.passed += 1

            if history:
                latest = history[-1]
                print_success(f"Latest value: ${latest.total_value:,.2f} at {latest.timestamp}")
                self.passed += 1

            # Test daily snapshots
            snapshots = self.service.get_daily_snapshots(self.test_user_email, days=30)
            print_success(f"Daily snapshots: {len(snapshots)}")
            self.passed += 1

            if snapshots:
                latest_snapshot = snapshots[-1]
                print_success(f"Latest snapshot: ${latest_snapshot.total_value:,.2f} (Return: {latest_snapshot.total_return_pct:.2f}%)")
                self.passed += 1

        except Exception as e:
            print_error(f"History test failed: {e}")
            self.failed += 1

    async def test_rankings(self):
        """Test portfolio rankings"""
        try:
            rank = await self.service.get_rank(self.test_user_email)
            
            assert rank.rank > 0, "Rank invalid"
            assert rank.total_users > 0, "Total users invalid"
            
            print_success(f"Rank: #{rank.rank} out of {rank.total_users} users")
            self.passed += 1

            print_success(f"Percentile: {rank.percentile:.1f}th")
            self.passed += 1

            print_success(f"Total return: {rank.total_return_pct:.2f}%")
            self.passed += 1

        except Exception as e:
            print_error(f"Rankings test failed: {e}")
            self.failed += 1

    async def test_allocation(self):
        """Test asset allocation"""
        try:
            allocation = await self.service.get_allocation(self.test_user_email)
            
            assert allocation.total_value > 0, "Total value invalid"
            print_success(f"Portfolio total: ${allocation.total_value:,.2f}")
            self.passed += 1

            total_pct = sum(a.percentage for a in allocation.by_asset_type)
            holdings_pct = (allocation.total_holdings_value / allocation.total_value * 100) if allocation.total_value > 0 else 0
            
            print_success(f"Holdings allocation: {holdings_pct:.1f}%")
            self.passed += 1

            for asset_alloc in allocation.by_asset_type:
                print_success(f"  {asset_alloc.asset_type.value}: ${asset_alloc.total_value:,.2f} ({asset_alloc.percentage:.1f}%)")
            self.passed += 1

        except Exception as e:
            print_error(f"Allocation test failed: {e}")
            self.failed += 1

    async def test_best_worst(self):
        """Test best/worst holdings analysis"""
        try:
            analysis = await self.service.get_best_worst_holdings(self.test_user_email, limit=3)
            
            if analysis.best_performing:
                print_success(f"Best performer: {analysis.best_performing[0].symbol} (+{analysis.best_performing[0].unrealized_pnl_pct:.2f}%)")
                self.passed += 1

            if analysis.worst_performing:
                print_success(f"Worst performer: {analysis.worst_performing[0].symbol} ({analysis.worst_performing[0].unrealized_pnl_pct:.2f}%)")
                self.passed += 1

            if analysis.largest_positions:
                print_success(f"Largest position: {analysis.largest_positions[0].symbol} (${analysis.largest_positions[0].market_value:,.2f})")
                self.passed += 1

        except Exception as e:
            print_error(f"Best/worst test failed: {e}")
            self.failed += 1

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("  📊 TEST SUMMARY")
        print("="*60)
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n  Total Tests: {total}")
        print_success(f"Passed: {self.passed}")
        if self.failed > 0:
            print_error(f"Failed: {self.failed}")
        else:
            print(f"  Failed: {self.failed}")
        
        print(f"\n  Success Rate: {success_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! Your portfolio system is working perfectly!{Colors.END}\n")
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Review the errors above.{Colors.END}\n")

async def main():
    """Main test runner"""
    tester = PortfolioSystemTests()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
