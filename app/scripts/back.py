# app/scripts/backfill_position_ids.py
import asyncio
from decimal import Decimal
from sqlalchemy import and_
from app.config.database import SessionLocal
from app.models.bot import BotTrade
from app.services.leverage_trading_service import LeverageTradingService

def backfill_position_ids():
    db = SessionLocal()
    try:
        # Get all open leveraged trades without position_id
        open_trades = db.query(BotTrade).filter(
            and_(
                BotTrade.is_open == True,
                BotTrade.leverage_used > 1.0,
                BotTrade.position_id == None
            )
        ).all()
        
        print(f"Found {len(open_trades)} trades to backfill")
        
        leverage_service = LeverageTradingService(db)
        
        for trade in open_trades:
            print(f"\nProcessing trade {trade.id}:")
            print(f"  Symbol: {trade.symbol}")
            print(f"  Quantity: {trade.quantity}")
            print(f"  Entry price: {trade.entry_price}")
            print(f"  Leverage: {trade.leverage_used}")
            
            # Find open positions for this user and symbol
            open_positions = leverage_service.get_open_positions(
                user_id=trade.user_id,
                symbol=trade.symbol
            )
            
            print(f"  Found {len(open_positions)} open positions")
            
            if open_positions:
                # Try to find a matching position
                matched_position = None
                for position in open_positions:
                    print(f"    Checking position {position.id}:")
                    print(f"      Position quantity: {position.quantity}")
                    print(f"      Position entry price: {position.entry_price}")
                    
                    # Convert to Decimal for comparison
                    trade_qty = Decimal(str(trade.quantity))
                    trade_price = Decimal(str(trade.entry_price))
                    pos_qty = Decimal(str(position.quantity))
                    pos_price = Decimal(str(position.entry_price))
                    
                    qty_match = abs(pos_qty - trade_qty) < Decimal('0.001')
                    price_match = abs(pos_price - trade_price) < Decimal('0.01')
                    
                    if qty_match and price_match:
                        matched_position = position
                        print(f"    ✓ MATCH FOUND: Trade {trade.id} matches Position {position.id}")
                        break
                    else:
                        print(f"    ✗ No match: qty_match={qty_match}, price_match={price_match}")
                
                if matched_position:
                    trade.position_id = matched_position.id
                    print(f"  Linked trade {trade.id} to position {matched_position.id}")
                else:
                    # If no exact match, use the first position
                    trade.position_id = open_positions[0].id
                    print(f"  Linked trade {trade.id} to first position {open_positions[0].id}")
            else:
                print(f"  No open positions found for symbol {trade.symbol}")
        
        db.commit()
        print(f"\nBackfill completed. Updated {len(open_trades)} trades.")
        
        # Verify the updates
        updated_trades = db.query(BotTrade).filter(
            and_(
                BotTrade.is_open == True,
                BotTrade.leverage_used > 1.0,
                BotTrade.position_id != None
            )
        ).all()
        
        print(f"\nVerification: {len(updated_trades)} trades now have position_id:")
        for trade in updated_trades:
            print(f"  Trade {trade.id}: position_id = {trade.position_id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    backfill_position_ids()