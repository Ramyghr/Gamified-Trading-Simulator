"""
Real-Time Portfolio Service with automatic valuation updates
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.user import User
from app.models.portfolio import Portfolio, Holding, PortfolioHistory, PortfolioDailySnapshot
from decimal import Decimal
from app.services.market_data_refresher import market_refresher
from app.schemas.portfolio import *
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math
import logging
from app.models.stock_transaction import StockTransaction

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db
        self.market_refresher = market_refresher

    def get_portfolio_by_email(self, email: str) -> Portfolio:
        """Get portfolio with user validation"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        return user.portfolio

    async def update_portfolio_valuation(
        self, 
        portfolio: Portfolio, 
        force_refresh: bool = False
    ) -> Portfolio:
        """
        Update portfolio with real-time prices
        Uses background refresher cache for speed, can force refresh
        """
        holdings = portfolio.holdings
        
        if not holdings:
            portfolio.total_value = Decimal(str(portfolio.cash_balance))
            portfolio.last_valuation_update = datetime.utcnow()
            self.db.commit()
            return portfolio
        
        # Get prices (from cache or live)
        total_holdings_value = Decimal('0.0')
        prices_updated = 0
        
        for holding in holdings:
            # Try to get from refresher cache first (fastest)
            price = self.market_refresher.get_cached_price(holding.symbol)
            
            # If not in cache or force refresh, fetch live
            if price is None or force_refresh:
                from app.services.market_data_service import enhanced_market_service  
                price = await enhanced_market_service.get_price(
                    holding.symbol, 
                    holding.asset_type.value,
                    force_refresh=force_refresh
                )
            
            if price and price > 0:
                price_decimal = Decimal(str(price))
                holding.current_price = price_decimal
                holding.last_price_update = datetime.utcnow()
                prices_updated += 1
            else:
                # Use last known price
                price_decimal = holding.current_price or holding.average_buy_price
            
            # Calculate current value
            current_holding_value = Decimal(holding.quantity) * price_decimal
            total_holdings_value += current_holding_value
        
        # Update portfolio total
        cash_balance_decimal = Decimal(str(portfolio.cash_balance))
        portfolio.total_value = cash_balance_decimal + total_holdings_value
        portfolio.last_valuation_update = datetime.utcnow()
        
        # Record in history
        history_entry = PortfolioHistory(
            portfolio_id=portfolio.id,
            total_value=portfolio.total_value,
            cash_balance=cash_balance_decimal,
            holdings_value=total_holdings_value,
            timestamp=datetime.utcnow()
        )
        self.db.add(history_entry)
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        logger.info(
            f"Portfolio {portfolio.id} updated: "
            f"${portfolio.total_value:.2f} ({prices_updated}/{len(holdings)} prices)"
        )
        
        return portfolio

    async def get_overview(self, email: str) -> PortfolioOverview:
        """
        Get real-time portfolio overview
        Always uses latest cached prices from background refresher
        """
        portfolio = self.get_portfolio_by_email(email)
        
        # Update valuation with latest prices (uses cache, very fast)
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        # Convert to Decimal for calculations
        cash_balance_decimal = Decimal(str(portfolio.cash_balance))
        initial_balance_decimal = Decimal(str(portfolio.initial_balance))
        
        # Calculate holdings value
        holdings_value = Decimal('0.0')
        for h in portfolio.holdings:
            # Use refresher cache first
            price = self.market_refresher.get_cached_price(h.symbol)
            if price is None:
                price = float(h.current_price or h.average_buy_price)
            holdings_value += Decimal(str(price)) * Decimal(h.quantity)
        
        # Calculate totals
        total_value = cash_balance_decimal + holdings_value
        total_gain = total_value - initial_balance_decimal
        gain_percentage = (
            (total_gain / initial_balance_decimal * 100) 
            if initial_balance_decimal > 0 
            else 0
        )
        
        # Calculate daily gain from last snapshot
        from app.models.portfolio import PortfolioDailySnapshot
        yesterday_snapshot = self.db.query(PortfolioDailySnapshot).filter(
            PortfolioDailySnapshot.portfolio_id == portfolio.id
        ).order_by(desc(PortfolioDailySnapshot.date)).first()
        
        if yesterday_snapshot:
            daily_gain = total_value - yesterday_snapshot.total_value
            daily_gain_pct = (
                (daily_gain / yesterday_snapshot.total_value * 100) 
                if yesterday_snapshot.total_value > 0 
                else 0
            )
        else:
            daily_gain = total_gain
            daily_gain_pct = gain_percentage
        
        # Update portfolio total_value if different
        if abs(Decimal(portfolio.total_value) - total_value) > Decimal('0.01'):
            portfolio.total_value = float(total_value)
            self.db.commit()
        
        return PortfolioOverview(
            total_value=float(total_value),
            cash_balance=float(cash_balance_decimal),
            holdings_value=float(holdings_value),
            initial_balance=float(initial_balance_decimal),
            total_gain=float(total_gain),
            total_gain_pct=float(gain_percentage),
            daily_gain=float(daily_gain),
            daily_gain_pct=float(daily_gain_pct),
            cash_allocation_pct=float(
                cash_balance_decimal / total_value * 100 
                if total_value > 0 
                else 100
            ),
            holdings_allocation_pct=float(
                holdings_value / total_value * 100 
                if total_value > 0 
                else 0
            ),
            last_updated=portfolio.last_valuation_update
        )

    def get_history(self, portfolio_id: int, days: int = 30) -> List[PortfolioHistoryPoint]:
        """Get portfolio history for the last N days - synchronous"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.db.query(PortfolioHistory).filter(
            PortfolioHistory.portfolio_id == portfolio_id,
            PortfolioHistory.timestamp >= start_date
        ).order_by(PortfolioHistory.timestamp.asc()).all()
        
        # Convert to list of history points
        history_points = []
        for snapshot in snapshots:
            history_points.append(PortfolioHistoryPoint(
                timestamp=snapshot.timestamp,
                total_value=float(snapshot.total_value),
                cash_balance=float(snapshot.cash_balance),
                holdings_value=float(snapshot.holdings_value)
            ))
        
        return history_points



    async def get_holdings(
        self, 
        email: str, 
        page: int = 0, 
        size: int = 10, 
        sort_by: str = "value"
    ) -> HoldingsPaginated:
        """Get holdings with real-time prices"""
        portfolio = self.get_portfolio_by_email(email)
        
        # Quick update from cache
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        offset = page * size
        query = self.db.query(Holding).filter(Holding.portfolio_id == portfolio.id)
        
        # Sorting
        if sort_by == "symbol":
            query = query.order_by(Holding.symbol)
        elif sort_by == "quantity":
            query = query.order_by(desc(Holding.quantity))
        elif sort_by == "pnl":
            query = query.order_by(
                desc((Holding.current_price - Holding.average_buy_price) * Holding.quantity)
            )
        else:
            query = query.order_by(desc(Holding.current_price * Holding.quantity))
        
        total = query.count()
        holdings = query.offset(offset).limit(size).all()
        
        items = []
        for holding in holdings:
            # Get latest price
            price = self.market_refresher.get_cached_price(holding.symbol)
            if price is None:
                price = float(holding.current_price or holding.average_buy_price)
            
            price_decimal = Decimal(str(price))
            market_value = Decimal(holding.quantity) * price_decimal
            cost_basis = Decimal(holding.quantity) * holding.average_buy_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (
                (unrealized_pnl / cost_basis * 100) 
                if cost_basis > 0 
                else 0
            )
            
            items.append(HoldingResponse(
                id=holding.id,
                portfolio_id=holding.portfolio_id,
                symbol=holding.symbol,
                asset_type=holding.asset_type,
                quantity=float(holding.quantity),
                average_buy_price=float(holding.average_buy_price),
                current_price=float(price_decimal),
                last_price_update=holding.last_price_update,
                market_value=float(market_value),
                cost_basis=float(cost_basis),
                unrealized_pnl=float(unrealized_pnl),
                unrealized_pnl_pct=float(unrealized_pnl_pct)
            ))
        
        return HoldingsPaginated(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if size > 0 else 0
        )
    
    def get_stats(self, email: str) -> PortfolioStats:
        """Get portfolio statistics that match PortfolioStats schema"""
        portfolio = self.get_portfolio_by_email(email)

        # Calculate basic stats
        total_trades = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id
        ).count()

        winning_trades = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id,
            StockTransaction.net_amount > 0
        ).count()

        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate P&L from transactions
        realized_pnl = 0.0
        transactions = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id
        ).all()

        for tx in transactions:
            if tx.transaction_type.value == "SELL":
                realized_pnl += float(tx.net_amount or 0)

        # Calculate unrealized P&L from holdings
        unrealized_pnl = 0.0
        for holding in portfolio.holdings:
            current_price = float(holding.current_price or holding.average_buy_price)
            cost_basis = float(holding.average_buy_price)
            quantity = float(holding.quantity)
            unrealized_pnl += (current_price - cost_basis) * quantity

        total_pnl = realized_pnl + unrealized_pnl
        
        # Calculate total return percentages
        initial_balance = float(portfolio.initial_balance)
        total_return = total_pnl
        total_return_pct = (total_return / initial_balance * 100) if initial_balance > 0 else 0

        # Find best and worst trades
        best_trade = 0.0
        worst_trade = 0.0
        if transactions:
            net_amounts = [float(tx.net_amount or 0) for tx in transactions if tx.net_amount]
            best_trade = max(net_amounts) if net_amounts else 0.0
            worst_trade = min(net_amounts) if net_amounts else 0.0

        # Calculate averages
        winning_transactions = [tx for tx in transactions if tx.net_amount and float(tx.net_amount) > 0]
        losing_transactions = [tx for tx in transactions if tx.net_amount and float(tx.net_amount) < 0]

        avg_win = sum(float(tx.net_amount) for tx in winning_transactions) / len(winning_transactions) if winning_transactions else 0.0
        avg_loss = sum(float(tx.net_amount) for tx in losing_transactions) / len(losing_transactions) if losing_transactions else 0.0

        # Calculate profit factor
        total_wins = sum(float(tx.net_amount) for tx in winning_transactions) if winning_transactions else 0.0
        total_losses = abs(sum(float(tx.net_amount) for tx in losing_transactions)) if losing_transactions else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        # Simplified calculations for now
        daily_return = 0.0
        max_drawdown = 0.0
        current_drawdown = 0.0

        return PortfolioStats(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=float(win_rate),
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            total_return=total_return,  # Added this field
            total_return_pct=total_return_pct,  # Added this field
            daily_return=daily_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            last_updated=datetime.utcnow()
        )


    def get_daily_snapshots(self, email: str, days: int = 30) -> List[PortfolioDailySnapshotResponse]:
        """Get daily snapshots"""
        portfolio = self.get_portfolio_by_email(email)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.db.query(PortfolioDailySnapshot).filter(
            PortfolioDailySnapshot.portfolio_id == portfolio.id,
            PortfolioDailySnapshot.date >= start_date
        ).order_by(PortfolioDailySnapshot.date.asc()).all()
        
        snapshot_responses = []
        for snapshot in snapshots:
            snapshot_responses.append(PortfolioDailySnapshotResponse(
                date=snapshot.date,
                total_value=float(snapshot.total_value),
                cash_balance=float(snapshot.cash_balance),
                holdings_value=float(snapshot.total_value - snapshot.cash_balance),  # Calculate holdings value
                daily_return=float(snapshot.daily_return),
                total_return=float(snapshot.total_return),
                total_return_pct=float(snapshot.total_return_pct),
                portfolio_rank=snapshot.portfolio_rank
            ))
        
        return snapshot_responses

    
    # In app/services/portfolio_service.py - get_best_worst_holdings method

    def get_best_worst_holdings(self, email: str, limit: int = 3) -> BestWorstHoldings:
        """Get best/worst holdings that match BestWorstHoldings schema"""
        portfolio = self.get_portfolio_by_email(email)
        
        holdings_with_performance = []
        for holding in portfolio.holdings:
            current_price = float(holding.current_price or holding.average_buy_price)
            cost_basis = float(holding.average_buy_price)
            quantity = float(holding.quantity)
            
            # Calculate P&L metrics
            unrealized_pnl = (current_price - cost_basis) * quantity
            unrealized_pnl_pct = ((current_price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
            market_value = current_price * quantity
            
            holdings_with_performance.append({
                "symbol": holding.symbol,
                "asset_type": holding.asset_type,
                "quantity": quantity,
                "average_buy_price": cost_basis,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,  # Added this
                "unrealized_pnl_pct": unrealized_pnl_pct  # Added this
            })
        
        # Sort by performance
        best_performing = sorted(holdings_with_performance, key=lambda x: x["unrealized_pnl_pct"], reverse=True)[:limit]
        worst_performing = sorted(holdings_with_performance, key=lambda x: x["unrealized_pnl_pct"])[:limit]
        largest_positions = sorted(holdings_with_performance, key=lambda x: x["market_value"], reverse=True)[:limit]
        
        # Convert to TopHolding objects
        def create_top_holding(data):
            return TopHolding(
                symbol=data["symbol"],
                asset_type=data["asset_type"],
                quantity=data["quantity"],
                average_buy_price=data["average_buy_price"],
                current_price=data["current_price"],
                market_value=data["market_value"],
                unrealized_pnl=data["unrealized_pnl"],  # Added this
                unrealized_pnl_pct=data["unrealized_pnl_pct"]  # Added this
            )
        
        return BestWorstHoldings(
            best_performing=[create_top_holding(h) for h in best_performing],
            worst_performing=[create_top_holding(h) for h in worst_performing],
            largest_positions=[create_top_holding(h) for h in largest_positions]
        )
            
        
        # Convert to TopHolding objects
        def create_top_holding(data):
            return TopHolding(
                symbol=data["symbol"],
                asset_type=data["asset_type"],
                quantity=data["quantity"],
                average_buy_price=data["average_buy_price"],
                current_price=data["current_price"],
                market_value=data["market_value"],
                unrealized_pnl=data["unrealized_pnl"],
                unrealized_pnl_pct=data["unrealized_pnl_pct"]
            )
        
        return BestWorstHoldings(
            best_performing=[create_top_holding(h) for h in best_performing],
            worst_performing=[create_top_holding(h) for h in worst_performing],
            largest_positions=[create_top_holding(h) for h in largest_positions]
        )

    # In app/services/portfolio_service.py - get_rank method

    def get_rank(self, email: str) -> PortfolioRank:
        """Get portfolio rank that matches PortfolioRank schema"""
        portfolio = self.get_portfolio_by_email(email)

        # Get all portfolios sorted by total value
        all_portfolios = self.db.query(Portfolio).order_by(Portfolio.total_value.desc()).all()

        # Find current portfolio rank
        rank = 1
        for p in all_portfolios:
            if p.id == portfolio.id:
                break
            rank += 1

        total_users = len(all_portfolios)
        percentile = ((total_users - rank) / total_users * 100) if total_users > 0 else 0

        # Calculate total return percentage
        total_return_pct = ((portfolio.total_value - portfolio.initial_balance) / portfolio.initial_balance * 100) if portfolio.initial_balance > 0 else 0

        # Calculate thresholds for top 10% and top 25%
        if total_users > 0:
            top_10_index = max(0, int(total_users * 0.1) - 1)
            top_25_index = max(0, int(total_users * 0.25) - 1)
            top_10_threshold = all_portfolios[top_10_index].total_value if top_10_index < len(all_portfolios) else 0
            top_25_threshold = all_portfolios[top_25_index].total_value if top_25_index < len(all_portfolios) else 0
        else:
            top_10_threshold = 0
            top_25_threshold = 0

        return PortfolioRank(
            rank=rank,
            total_users=total_users,
            percentile=float(percentile),
            total_value=float(portfolio.total_value),
            total_return_pct=float(total_return_pct),
            top_10_threshold=float(top_10_threshold),  # Added this field
            top_25_threshold=float(top_25_threshold)   # Added this field
        )

    def calculate_portfolio_metrics(self, portfolio_id: int) -> bool:
        """Calculate portfolio metrics"""
        logger.info(f"Calculating metrics for portfolio {portfolio_id}")
        return True
    # In app/services/portfolio_service.py - get_allocation method

    def get_allocation(self, email: str) -> AllocationBreakdown:
        """Get asset allocation breakdown"""
        portfolio = self.get_portfolio_by_email(email)
        
        # Calculate holdings value by asset type
        allocation_by_type = {}
        total_holdings_value = 0.0
        
        for holding in portfolio.holdings:
            current_price = float(holding.current_price or holding.average_buy_price)
            market_value = current_price * float(holding.quantity)
            total_holdings_value += market_value
            
            asset_type = holding.asset_type.value
            if asset_type not in allocation_by_type:
                allocation_by_type[asset_type] = {
                    "holdings_count": 0,
                    "total_value": 0.0
                }
            
            allocation_by_type[asset_type]["holdings_count"] += 1
            allocation_by_type[asset_type]["total_value"] += market_value
        
        # Calculate total portfolio value
        cash_balance = float(portfolio.cash_balance)
        total_value = total_holdings_value + cash_balance
        
        # Convert to AssetAllocation objects
        by_asset_type = []
        for asset_type, data in allocation_by_type.items():
            percentage = (data["total_value"] / total_value * 100) if total_value > 0 else 0
            by_asset_type.append(AssetAllocation(
                asset_type=AssetType(asset_type),
                total_value=data["total_value"],
                percentage=percentage,
                holdings_count=data["holdings_count"]
            ))
        
        # Add cash as an allocation type
        cash_percentage = (cash_balance / total_value * 100) if total_value > 0 else 0
        by_asset_type.append(AssetAllocation(
            asset_type=AssetType.CASH,  # You might need to add CASH to your AssetType enum
            total_value=cash_balance,
            percentage=cash_percentage,
            holdings_count=1
        ))
        
        return AllocationBreakdown(
            by_asset_type=by_asset_type,
            total_holdings_value=total_holdings_value,
            cash_balance=cash_balance,
            total_value=total_value
        )
    async def get_detailed_positions(self, email: str) -> PortfolioPositionsDetailed:
        """Get all positions with real-time metrics"""
        portfolio = self.get_portfolio_by_email(email)
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        positions = []
        total_market_value = Decimal('0.0')
        total_cost_basis = Decimal('0.0')
        
        for holding in portfolio.holdings:
            # Get latest price from cache
            price = self.market_refresher.get_cached_price(holding.symbol)
            if price is None:
                price = float(holding.current_price or holding.average_buy_price)
            
            price_decimal = Decimal(str(price))
            market_value = Decimal(holding.quantity) * price_decimal
            cost_basis = Decimal(holding.quantity) * holding.average_buy_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (
                (unrealized_pnl / cost_basis * 100) 
                if cost_basis > 0 
                else 0
            )
            
            total_market_value += market_value
            total_cost_basis += cost_basis
            
            positions.append(DetailedPosition(
                symbol=holding.symbol,
                asset_type=holding.asset_type,
                quantity=float(holding.quantity),
                average_buy_price=float(holding.average_buy_price),
                current_price=float(price_decimal),
                market_value=float(market_value),
                cost_basis=float(cost_basis),
                unrealized_pnl=float(unrealized_pnl),
                unrealized_pnl_pct=float(unrealized_pnl_pct),
                allocation_pct=float(
                    market_value / Decimal(portfolio.total_value) * Decimal("100") 
                    if portfolio.total_value > 0 
                    else Decimal("0")
                ),
                last_price_update=holding.last_price_update
            ))
        
        total_unrealized_pnl = total_market_value - total_cost_basis
        total_unrealized_pnl_pct = (
            (total_unrealized_pnl / total_cost_basis * 100) 
            if total_cost_basis > 0 
            else 0
        )
        
        return PortfolioPositionsDetailed(
            positions=positions,
            total_market_value=float(total_market_value),
            total_cost_basis=float(total_cost_basis),
            total_unrealized_pnl=float(total_unrealized_pnl),
            total_unrealized_pnl_pct=float(total_unrealized_pnl_pct)
        )

    def get_available_cash(self, email: str) -> Decimal:
        """Get available cash balance"""
        portfolio = self.get_portfolio_by_email(email)
        return Decimal(str(portfolio.cash_balance))

    def get_holding_quantity(self, email: str, symbol: str) -> Decimal:
        """Get quantity of specific holding"""
        portfolio = self.get_portfolio_by_email(email)
        
        holding = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.symbol == symbol.upper()
        ).first()
        
        return Decimal(holding.quantity) if holding else Decimal('0.0')