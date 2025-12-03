"""
Enhanced Portfolio Service with Leverage Trading Support
Integrates both spot trading and leveraged positions
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.models.user import User
from app.models.portfolio import (
    Portfolio, Holding, PortfolioHistory, PortfolioDailySnapshot,
    Position, PositionSide, LiquidationEvent
)
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from app.services.market_data_refresher import market_refresher
from app.schemas.portfolio import *
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math
import logging
from app.models.stock_transaction import StockTransaction

getcontext().prec = 18
getcontext().rounding = ROUND_HALF_EVEN
logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db
        self.market_refresher = market_refresher

    def _to_decimal(self, value) -> Decimal:
        """Safely convert to Decimal"""
        if value is None:
            return Decimal('0')
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')

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
        Update portfolio with real-time prices for BOTH holdings and leveraged positions
        """
        # Update spot holdings
        holdings = portfolio.holdings
        total_holdings_value = Decimal('0.0')
        
        if holdings:
            for holding in holdings:
                price = self.market_refresher.get_cached_price(holding.symbol)
                
                if price is None or force_refresh:
                    from app.services.market_data_service import enhanced_market_service  
                    price = await enhanced_market_service.get_price(
                        holding.symbol, 
                        holding.asset_type.value,
                        force_refresh=force_refresh
                    )
                
                if price and price > 0:
                    price_decimal = self._to_decimal(price)
                    holding.current_price = price_decimal
                    holding.last_price_update = datetime.utcnow()
                else:
                    price_decimal = holding.current_price or holding.average_buy_price
                
                current_holding_value = Decimal(holding.quantity) * price_decimal
                total_holdings_value += current_holding_value
        
        # Update leveraged positions
        open_positions = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).all()
        
        total_unrealized_pnl = Decimal('0.0')
        total_margin_used = Decimal('0.0')
        total_exposure = Decimal('0.0')
        
        for position in open_positions:
            # Update position price
            price = self.market_refresher.get_cached_price(position.symbol)
            if price is None or force_refresh:
                from app.services.market_data_service import enhanced_market_service
                price = await enhanced_market_service.get_price(
                    position.symbol,
                    "STOCK",
                    force_refresh=force_refresh
                )
            
            if price and price > 0:
                current_price = self._to_decimal(price)
                entry_price = self._to_decimal(position.entry_price)
                quantity = self._to_decimal(position.quantity)
                
                # Calculate unrealized PnL
                if position.side == PositionSide.LONG:
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:  # SHORT
                    unrealized_pnl = (entry_price - current_price) * quantity
                
                # Update position
                position.current_price = float(current_price)
                position.unrealized_pnl = float(unrealized_pnl)
                position.last_price_update = datetime.utcnow()
                
                # Accumulate totals
                total_unrealized_pnl += unrealized_pnl
                total_margin_used += self._to_decimal(position.margin_used)
                position_value = quantity * current_price
                total_exposure += position_value
        
        # Update portfolio metrics
        cash_balance_decimal = self._to_decimal(portfolio.cash_balance)
        
        # Calculate equity (cash + unrealized PnL from leveraged positions)
        equity = cash_balance_decimal + total_unrealized_pnl
        
        # Total portfolio value includes holdings + equity
        portfolio.total_value = float(cash_balance_decimal + total_holdings_value + total_unrealized_pnl)
        portfolio.equity = float(equity)
        portfolio.unrealized_pnl = float(total_unrealized_pnl)
        portfolio.margin_used = float(total_margin_used)
        portfolio.total_exposure = float(total_exposure)
        
        # Calculate margin level
        if total_margin_used > 0:
            margin_level = (equity / total_margin_used) * Decimal('100')
            portfolio.margin_level = float(margin_level)
        else:
            portfolio.margin_level = 999999.0
        
        # Calculate available margin
        available_margin = equity - total_margin_used
        portfolio.margin_available = float(max(available_margin, Decimal('0')))
        
        portfolio.last_valuation_update = datetime.utcnow()
        
        # Record in history
        history_entry = PortfolioHistory(
            portfolio_id=portfolio.id,
            total_value=self._to_decimal(portfolio.total_value),
            cash_balance=cash_balance_decimal,
            holdings_value=total_holdings_value,
            timestamp=datetime.utcnow()
        )
        self.db.add(history_entry)
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        logger.info(
            f"Portfolio {portfolio.id} updated: "
            f"${portfolio.total_value:.2f} | "
            f"Equity: ${equity:.2f} | "
            f"Margin Used: ${total_margin_used:.2f} | "
            f"Open Positions: {len(open_positions)}"
        )
        
        return portfolio

    async def get_overview(self, email: str) -> PortfolioOverview:
        """
        Get comprehensive portfolio overview including leveraged positions
        """
        portfolio = self.get_portfolio_by_email(email)
        
        # Update valuation
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        cash_balance_decimal = self._to_decimal(portfolio.cash_balance)
        initial_balance_decimal = self._to_decimal(portfolio.initial_balance)
        
        # Calculate spot holdings value
        holdings_value = Decimal('0.0')
        for h in portfolio.holdings:
            price = self.market_refresher.get_cached_price(h.symbol)
            if price is None:
                price = float(h.current_price or h.average_buy_price)
            holdings_value += self._to_decimal(price) * Decimal(h.quantity)
        
        # Get leveraged positions metrics
        leveraged_pnl = self._to_decimal(portfolio.unrealized_pnl)
        margin_used = self._to_decimal(portfolio.margin_used)
        equity = self._to_decimal(portfolio.equity)
        
        # Total value includes everything
        total_value = cash_balance_decimal + holdings_value + leveraged_pnl
        total_gain = total_value - initial_balance_decimal
        gain_percentage = (
            (total_gain / initial_balance_decimal * 100) 
            if initial_balance_decimal > 0 
            else 0
        )
        
        # Calculate daily gain from last snapshot
        yesterday_snapshot = self.db.query(PortfolioDailySnapshot).filter(
            PortfolioDailySnapshot.portfolio_id == portfolio.id
        ).order_by(desc(PortfolioDailySnapshot.date)).first()
        
        if yesterday_snapshot:
            daily_gain = total_value - self._to_decimal(yesterday_snapshot.total_value)
            daily_gain_pct = (
                (daily_gain / self._to_decimal(yesterday_snapshot.total_value) * 100) 
                if yesterday_snapshot.total_value > 0 
                else 0
            )
        else:
            daily_gain = total_gain
            daily_gain_pct = gain_percentage
        
        # Update portfolio total_value if different
        if abs(self._to_decimal(portfolio.total_value) - total_value) > Decimal('0.01'):
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
            last_updated=portfolio.last_valuation_update,
            # Leverage-specific metrics
            leveraged_pnl=float(leveraged_pnl),
            margin_used=float(margin_used),
            margin_available=float(portfolio.margin_available),
            margin_level=float(portfolio.margin_level),
            total_exposure=float(portfolio.total_exposure)
        )

    def get_stats(self, email: str) -> PortfolioStats:
        """
        Enhanced portfolio statistics including leveraged trading performance
        """
        portfolio = self.get_portfolio_by_email(email)

        # Calculate spot trading stats
        spot_trades = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id
        ).count()

        # Calculate leveraged positions stats
        closed_positions = self.db.query(Position).filter(
            and_(
                Position.user_id == portfolio.user_id,
                Position.is_open == False
            )
        ).all()
        
        leveraged_trades = len(closed_positions)
        total_trades = spot_trades + leveraged_trades

        # Calculate wins/losses from both spot and leveraged
        winning_spot = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id,
            StockTransaction.net_amount > 0
        ).count()
        
        winning_leveraged = sum(1 for p in closed_positions if p.realized_pnl > 0)
        winning_trades = winning_spot + winning_leveraged
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate realized P&L from both sources
        realized_pnl_spot = 0.0
        transactions = self.db.query(StockTransaction).filter(
            StockTransaction.user_id == portfolio.user_id
        ).all()

        for tx in transactions:
            if tx.transaction_type.value == "SELL":
                realized_pnl_spot += float(tx.net_amount or 0)
        
        realized_pnl_leveraged = sum(float(p.realized_pnl) for p in closed_positions)
        realized_pnl = realized_pnl_spot + realized_pnl_leveraged

        # Calculate unrealized P&L from holdings
        unrealized_pnl_holdings = 0.0
        for holding in portfolio.holdings:
            current_price = float(holding.current_price or holding.average_buy_price)
            cost_basis = float(holding.average_buy_price)
            quantity = float(holding.quantity)
            unrealized_pnl_holdings += (current_price - cost_basis) * quantity
        
        # Add unrealized P&L from open leveraged positions
        unrealized_pnl_leveraged = float(portfolio.unrealized_pnl)
        unrealized_pnl = unrealized_pnl_holdings + unrealized_pnl_leveraged

        total_pnl = realized_pnl + unrealized_pnl
        
        # Calculate total return
        initial_balance = float(portfolio.initial_balance)
        total_return = total_pnl
        total_return_pct = (total_return / initial_balance * 100) if initial_balance > 0 else 0

        # Find best and worst trades (including leveraged)
        all_pnls = []
        all_pnls.extend([float(tx.net_amount or 0) for tx in transactions if tx.net_amount])
        all_pnls.extend([float(p.realized_pnl) for p in closed_positions])
        
        best_trade = max(all_pnls) if all_pnls else 0.0
        worst_trade = min(all_pnls) if all_pnls else 0.0

        # Calculate averages
        winning_pnls = [pnl for pnl in all_pnls if pnl > 0]
        losing_pnls = [pnl for pnl in all_pnls if pnl < 0]

        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0

        # Calculate profit factor
        total_wins = sum(winning_pnls) if winning_pnls else 0.0
        total_losses = abs(sum(losing_pnls)) if losing_pnls else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        # Calculate liquidation stats
        liquidations = self.db.query(LiquidationEvent).filter(
            LiquidationEvent.user_id == portfolio.user_id
        ).count()

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
            total_return=total_return,
            total_return_pct=total_return_pct,
            daily_return=daily_return,
            best_trade=best_trade,
            worst_trade=worst_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            last_updated=datetime.utcnow(),
            # Leverage-specific stats
            leveraged_trades=leveraged_trades,
            liquidations=liquidations,
            avg_leverage_used=self._calculate_avg_leverage(portfolio)
        )

    def _calculate_avg_leverage(self, portfolio: Portfolio) -> float:
        """Calculate average leverage used across all positions"""
        positions = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.id
        ).all()
        
        if not positions:
            return 0.0
        
        total_weighted_leverage = Decimal('0')
        total_margin = Decimal('0')
        
        for pos in positions:
            leverage = self._to_decimal(pos.leverage)
            margin = self._to_decimal(pos.margin_used)
            total_weighted_leverage += leverage * margin
            total_margin += margin
        
        if total_margin > 0:
            return float(total_weighted_leverage / total_margin)
        return 0.0

    async def get_detailed_positions(self, email: str) -> PortfolioPositionsDetailed:
        """
        Get all positions including spot holdings AND leveraged positions
        """
        portfolio = self.get_portfolio_by_email(email)
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        positions = []
        total_market_value = Decimal('0.0')
        total_cost_basis = Decimal('0.0')
        
        # Add spot holdings
        for holding in portfolio.holdings:
            price = self.market_refresher.get_cached_price(holding.symbol)
            if price is None:
                price = float(holding.current_price or holding.average_buy_price)
            
            price_decimal = self._to_decimal(price)
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
                position_type="SPOT",
                quantity=float(holding.quantity),
                average_buy_price=float(holding.average_buy_price),
                current_price=float(price_decimal),
                market_value=float(market_value),
                cost_basis=float(cost_basis),
                unrealized_pnl=float(unrealized_pnl),
                unrealized_pnl_pct=float(unrealized_pnl_pct),
                allocation_pct=float(
                    market_value / self._to_decimal(portfolio.total_value) * Decimal("100") 
                    if portfolio.total_value > 0 
                    else Decimal("0")
                ),
                last_price_update=holding.last_price_update
            ))
        
        # Add leveraged positions
        leveraged_positions = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).all()
        
        for lev_pos in leveraged_positions:
            current_price = self._to_decimal(lev_pos.current_price)
            entry_price = self._to_decimal(lev_pos.entry_price)
            quantity = self._to_decimal(lev_pos.quantity)
            
            position_value = current_price * quantity
            margin_used = self._to_decimal(lev_pos.margin_used)
            unrealized_pnl = self._to_decimal(lev_pos.unrealized_pnl)
            
            unrealized_pnl_pct = (
                (unrealized_pnl / margin_used * 100)
                if margin_used > 0
                else 0
            )
            
            positions.append(DetailedPosition(
                symbol=lev_pos.symbol,
                asset_type=lev_pos.asset_type,
                position_type=f"LEVERAGE_{lev_pos.side.value}",
                quantity=float(quantity),
                average_buy_price=float(entry_price),
                current_price=float(current_price),
                market_value=float(position_value),
                cost_basis=float(margin_used),
                unrealized_pnl=float(unrealized_pnl),
                unrealized_pnl_pct=float(unrealized_pnl_pct),
                allocation_pct=float(
                    position_value / self._to_decimal(portfolio.total_value) * Decimal("100")
                    if portfolio.total_value > 0
                    else Decimal("0")
                ),
                leverage=float(lev_pos.leverage),
                liquidation_price=float(lev_pos.liquidation_price),
                last_price_update=lev_pos.last_price_update
            ))
        
        total_unrealized_pnl = sum(self._to_decimal(p.unrealized_pnl) for p in positions)
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

    async def get_holdings(
        self, 
        email: str, 
        page: int = 0, 
        size: int = 10, 
        sort_by: str = "value"
    ) -> HoldingsPaginated:
        """Get spot holdings (not leveraged positions)"""
        portfolio = self.get_portfolio_by_email(email)
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
            price = self.market_refresher.get_cached_price(holding.symbol)
            if price is None:
                price = float(holding.current_price or holding.average_buy_price)
            
            price_decimal = self._to_decimal(price)
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

    def get_history(self, portfolio_id: int, days: int = 30) -> List[PortfolioHistoryPoint]:
        """Get portfolio history including leveraged positions impact"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.db.query(PortfolioHistory).filter(
            PortfolioHistory.portfolio_id == portfolio_id,
            PortfolioHistory.timestamp >= start_date
        ).order_by(PortfolioHistory.timestamp.asc()).all()
        
        history_points = []
        for snapshot in snapshots:
            history_points.append(PortfolioHistoryPoint(
                timestamp=snapshot.timestamp,
                total_value=float(snapshot.total_value),
                cash_balance=float(snapshot.cash_balance),
                holdings_value=float(snapshot.holdings_value)
            ))
        
        return history_points

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
                holdings_value=float(snapshot.total_value - snapshot.cash_balance),
                daily_return=float(snapshot.daily_return),
                total_return=float(snapshot.total_return),
                total_return_pct=float(snapshot.total_return_pct),
                portfolio_rank=snapshot.portfolio_rank
            ))
        
        return snapshot_responses

    def get_best_worst_holdings(self, email: str, limit: int = 3) -> BestWorstHoldings:
        """Get best/worst performing positions (spot only)"""
        portfolio = self.get_portfolio_by_email(email)
        
        holdings_with_performance = []
        for holding in portfolio.holdings:
            current_price = float(holding.current_price or holding.average_buy_price)
            cost_basis = float(holding.average_buy_price)
            quantity = float(holding.quantity)
            
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
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct
            })
        
        best_performing = sorted(holdings_with_performance, key=lambda x: x["unrealized_pnl_pct"], reverse=True)[:limit]
        worst_performing = sorted(holdings_with_performance, key=lambda x: x["unrealized_pnl_pct"])[:limit]
        largest_positions = sorted(holdings_with_performance, key=lambda x: x["market_value"], reverse=True)[:limit]
        
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

    def get_rank(self, email: str) -> PortfolioRank:
        """Get portfolio rank"""
        portfolio = self.get_portfolio_by_email(email)
        all_portfolios = self.db.query(Portfolio).order_by(Portfolio.total_value.desc()).all()

        rank = 1
        for p in all_portfolios:
            if p.id == portfolio.id:
                break
            rank += 1

        total_users = len(all_portfolios)
        percentile = ((total_users - rank) / total_users * 100) if total_users > 0 else 0
        total_return_pct = ((portfolio.total_value - portfolio.initial_balance) / portfolio.initial_balance * 100) if portfolio.initial_balance > 0 else 0

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
            top_10_threshold=float(top_10_threshold),
            top_25_threshold=float(top_25_threshold)
        )

    def get_allocation(self, email: str) -> AllocationBreakdown:
        """Get asset allocation including leveraged exposure"""
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
        
        # Add leveraged positions
        leveraged_positions = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).all()
        
        leveraged_exposure = 0.0
        for lev_pos in leveraged_positions:
            position_value = float(lev_pos.current_price or lev_pos.entry_price) * float(lev_pos.quantity)
            leveraged_exposure += position_value
            
            asset_type = "LEVERAGE"
            if asset_type not in allocation_by_type:
                allocation_by_type[asset_type] = {
                    "holdings_count": 0,
                    "total_value": 0.0
                }
            allocation_by_type[asset_type]["holdings_count"] += 1
            allocation_by_type[asset_type]["total_value"] += position_value
        
        # Calculate total portfolio value
        cash_balance = float(portfolio.cash_balance)
        total_value = total_holdings_value + cash_balance + leveraged_exposure
        
        # Convert to AssetAllocation objects
        by_asset_type = []
        for asset_type, data in allocation_by_type.items():
            percentage = (data["total_value"] / total_value * 100) if total_value > 0 else 0
            by_asset_type.append(AssetAllocation(
                asset_type=AssetType(asset_type) if asset_type != "LEVERAGE" else AssetType.STOCK,
                total_value=data["total_value"],
                percentage=percentage,
                holdings_count=data["holdings_count"]
            ))
        
        # Add cash allocation
        cash_percentage = (cash_balance / total_value * 100) if total_value > 0 else 0
        
        return AllocationBreakdown(
            by_asset_type=by_asset_type,
            total_holdings_value=total_holdings_value,
            cash_balance=cash_balance,
            total_value=total_value,
            leveraged_exposure=leveraged_exposure
        )

    def calculate_portfolio_metrics(self, portfolio_id: int) -> bool:
        """Calculate portfolio metrics"""
        logger.info(f"Calculating metrics for portfolio {portfolio_id}")
        return True

    def get_available_cash(self, email: str) -> Decimal:
        """Get available cash balance (considering margin)"""
        portfolio = self.get_portfolio_by_email(email)
        cash = self._to_decimal(portfolio.cash_balance)
        margin_used = self._to_decimal(portfolio.margin_used)
        
        # Available cash is cash balance minus margin requirements
        available = cash - margin_used
        return max(available, Decimal('0'))

    def get_holding_quantity(self, email: str, symbol: str) -> Decimal:
        """Get quantity of specific holding"""
        portfolio = self.get_portfolio_by_email(email)
        
        holding = self.db.query(Holding).filter(
            Holding.portfolio_id == portfolio.id,
            Holding.symbol == symbol.upper()
        ).first()
        
        return Decimal(holding.quantity) if holding else Decimal('0.0')
    
    def get_leveraged_position_quantity(self, email: str, symbol: str) -> Dict:
        """Get leveraged position details for a symbol"""
        portfolio = self.get_portfolio_by_email(email)
        
        positions = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.symbol == symbol.upper(),
                Position.is_open == True
            )
        ).all()
        
        if not positions:
            return {
                "long_quantity": Decimal('0'),
                "short_quantity": Decimal('0'),
                "net_quantity": Decimal('0')
            }
        
        long_qty = sum(self._to_decimal(p.quantity) for p in positions if p.side == PositionSide.LONG)
        short_qty = sum(self._to_decimal(p.quantity) for p in positions if p.side == PositionSide.SHORT)
        
        return {
            "long_quantity": long_qty,
            "short_quantity": short_qty,
            "net_quantity": long_qty - short_qty
        }

    async def check_margin_health(self, email: str) -> Dict:
        """
        Check margin health and return warning status
        """
        portfolio = self.get_portfolio_by_email(email)
        await self.update_portfolio_valuation(portfolio, force_refresh=True)
        
        margin_level = float(portfolio.margin_level)
        
        # Determine health status
        if margin_level >= 200:
            status = "HEALTHY"
            risk_level = "LOW"
        elif margin_level >= 150:
            status = "GOOD"
            risk_level = "MEDIUM"
        elif margin_level >= 120:
            status = "WARNING"
            risk_level = "HIGH"
        elif margin_level >= 110:
            status = "DANGER"
            risk_level = "CRITICAL"
        else:
            status = "MARGIN_CALL"
            risk_level = "LIQUIDATION"
        
        # Check positions at risk
        positions_at_risk = []
        open_positions = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).all()
        
        for pos in open_positions:
            current_price = self._to_decimal(pos.current_price)
            liquidation_price = self._to_decimal(pos.liquidation_price)
            
            if pos.side == PositionSide.LONG:
                distance = ((current_price - liquidation_price) / current_price * Decimal('100'))
            else:
                distance = ((liquidation_price - current_price) / current_price * Decimal('100'))
            
            if abs(distance) < Decimal('20'):  # Within 20% of liquidation
                positions_at_risk.append({
                    "position_id": pos.id,
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "current_price": float(current_price),
                    "liquidation_price": float(liquidation_price),
                    "distance_pct": float(distance)
                })
        
        return {
            "status": status,
            "risk_level": risk_level,
            "margin_level": margin_level,
            "equity": float(portfolio.equity),
            "margin_used": float(portfolio.margin_used),
            "margin_available": float(portfolio.margin_available),
            "positions_at_risk": positions_at_risk,
            "positions_at_risk_count": len(positions_at_risk),
            "total_exposure": float(portfolio.total_exposure),
            "recommendation": self._get_margin_recommendation(status, margin_level)
        }
    
    def _get_margin_recommendation(self, status: str, margin_level: float) -> str:
        """Get recommendation based on margin status"""
        if status == "MARGIN_CALL":
            return "URGENT: Add funds immediately or close positions to avoid liquidation"
        elif status == "DANGER":
            return "WARNING: Margin level critically low. Consider reducing leverage or adding funds"
        elif status == "WARNING":
            return "CAUTION: Monitor positions closely. Consider reducing exposure"
        elif status == "GOOD":
            return "Margin level acceptable but consider maintaining buffer"
        else:
            return "Margin level healthy. Continue monitoring"

    async def get_portfolio_performance_summary(self, email: str) -> Dict:
        """
        Comprehensive performance summary including both spot and leveraged trading
        """
        portfolio = self.get_portfolio_by_email(email)
        await self.update_portfolio_valuation(portfolio, force_refresh=False)
        
        # Spot holdings performance
        spot_value = Decimal('0')
        spot_cost = Decimal('0')
        for holding in portfolio.holdings:
            price = self._to_decimal(holding.current_price or holding.average_buy_price)
            spot_value += self._to_decimal(holding.quantity) * price
            spot_cost += self._to_decimal(holding.quantity) * self._to_decimal(holding.average_buy_price)
        
        spot_pnl = spot_value - spot_cost
        spot_pnl_pct = (spot_pnl / spot_cost * Decimal('100')) if spot_cost > 0 else Decimal('0')
        
        # Leveraged positions performance
        leveraged_pnl = self._to_decimal(portfolio.unrealized_pnl)
        margin_used = self._to_decimal(portfolio.margin_used)
        leveraged_roi = (leveraged_pnl / margin_used * Decimal('100')) if margin_used > 0 else Decimal('0')
        
        # Overall performance
        total_value = self._to_decimal(portfolio.total_value)
        initial_balance = self._to_decimal(portfolio.initial_balance)
        total_return = total_value - initial_balance
        total_return_pct = (total_return / initial_balance * Decimal('100')) if initial_balance > 0 else Decimal('0')
        
        # Count positions
        open_positions_count = self.db.query(Position).filter(
            and_(
                Position.portfolio_id == portfolio.id,
                Position.is_open == True
            )
        ).count()
        
        return {
            "overview": {
                "total_value": float(total_value),
                "total_return": float(total_return),
                "total_return_pct": float(total_return_pct),
                "cash_balance": float(portfolio.cash_balance)
            },
            "spot_trading": {
                "holdings_value": float(spot_value),
                "cost_basis": float(spot_cost),
                "unrealized_pnl": float(spot_pnl),
                "unrealized_pnl_pct": float(spot_pnl_pct),
                "holdings_count": len(portfolio.holdings)
            },
            "leveraged_trading": {
                "unrealized_pnl": float(leveraged_pnl),
                "margin_used": float(margin_used),
                "margin_available": float(portfolio.margin_available),
                "roi": float(leveraged_roi),
                "open_positions": open_positions_count,
                "total_exposure": float(portfolio.total_exposure),
                "margin_level": float(portfolio.margin_level)
            },
            "risk_metrics": {
                "leverage_utilization": float((margin_used / total_value * Decimal('100')) if total_value > 0 else Decimal('0')),
                "exposure_ratio": float((self._to_decimal(portfolio.total_exposure) / total_value) if total_value > 0 else Decimal('0')),
                "margin_health": "HEALTHY" if portfolio.margin_level > 200 else "WARNING" if portfolio.margin_level > 120 else "CRITICAL"
            },
            "last_updated": portfolio.last_valuation_update
        }

    def get_liquidation_history(self, email: str, limit: int = 10) -> List[Dict]:
        """Get user's liquidation history"""
        portfolio = self.get_portfolio_by_email(email)
        
        liquidations = self.db.query(LiquidationEvent).filter(
            LiquidationEvent.user_id == portfolio.user_id
        ).order_by(desc(LiquidationEvent.liquidated_at)).limit(limit).all()
        
        return [
            {
                "id": liq.id,
                "symbol": liq.symbol,
                "side": liq.side.value,
                "quantity": float(liq.quantity),
                "entry_price": float(liq.entry_price),
                "liquidation_price": float(liq.liquidation_price),
                "loss_amount": float(liq.loss_amount),
                "liquidation_fee": float(liq.liquidation_fee),
                "reason": liq.reason,
                "liquidated_at": liq.liquidated_at
            }
            for liq in liquidations
        ]