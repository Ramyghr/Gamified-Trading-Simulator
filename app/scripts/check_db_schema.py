# app/scripts/check_db_schema.py
from sqlalchemy import inspect, text
from app.config.database import SessionLocal, engine
import sys

db = SessionLocal()

try:
    # Check if bot_trades table has position_id column
    inspector = inspect(engine)
    
    print("=== Checking bot_trades table ===")
    columns = inspector.get_columns('bot_trades')
    has_position_id = False
    for column in columns:
        print(f"  {column['name']}: {column['type']}")
        if column['name'] == 'position_id':
            has_position_id = True
    
    print(f"\nposition_id column exists: {has_position_id}")
    
    # Check foreign keys
    print("\n=== Foreign keys in bot_trades ===")
    fks = inspector.get_foreign_keys('bot_trades')
    for fk in fks:
        print(f"  {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Check sample data
    print("\n=== Sample bot_trades data (open leveraged trades) ===")
    result = db.execute(text("""
        SELECT id, symbol, quantity, entry_price, leverage_used, position_id, is_open
        FROM bot_trades 
        WHERE is_open = true 
        AND leverage_used > 1.0
        LIMIT 5
    """))
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"  Trade {row[0]}: {row[1]}, Qty={row[2]}, Price={row[3]}, Leverage={row[4]}, PositionID={row[5]}")
    else:
        print("  No open leveraged trades found")
    
    # Check positions table
    print("\n=== Sample positions data ===")
    result = db.execute(text("""
        SELECT id, symbol, quantity, entry_price, is_open
        FROM positions 
        WHERE is_open = true
        LIMIT 5
    """))
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"  Position {row[0]}: {row[1]}, Qty={row[2]}, Price={row[3]}")
    else:
        print("  No open positions found")
    
    # Check if we need to run a migration
    print("\n=== Checking if migration needed ===")
    if not has_position_id:
        print("  ❌ position_id column NOT FOUND in bot_trades table!")
        print("  You need to run a migration to add it.")
    else:
        print("  ✅ position_id column found")
        
finally:
    db.close()

print("\n=== Quick fix SQL commands ===")
print("""
-- If position_id column doesn't exist, run:
ALTER TABLE bot_trades ADD COLUMN IF NOT EXISTS position_id INTEGER NULL;

-- Add foreign key constraint:
ALTER TABLE bot_trades 
ADD CONSTRAINT fk_bot_trades_position_id 
FOREIGN KEY (position_id) 
REFERENCES positions(id);

-- Link existing trades to positions:
UPDATE bot_trades bt
SET position_id = p.id
FROM positions p
WHERE bt.user_id = p.user_id 
AND bt.symbol = p.symbol 
AND p.is_open = true
AND bt.is_open = true
AND bt.leverage_used > 1.0
AND bt.position_id IS NULL;

-- Verify:
SELECT id, symbol, position_id FROM bot_trades WHERE is_open = true AND leverage_used > 1.0;
""")