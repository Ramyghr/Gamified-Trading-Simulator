"""
Database migration helper for upgrading from basic to enhanced portfolio system
Run this script ONCE to migrate your existing data
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def run_migration():
    """Run all migration steps"""
    print("🚀 Starting Portfolio System Migration...")
    
    with engine.begin() as conn:
        try:
            # Step 1: Backup existing data
            print("\n📦 Step 1: Creating backup...")
            backup_existing_data(conn)
            
            # Step 2: Add new columns to existing tables
            print("\n🔧 Step 2: Updating portfolios table...")
            update_portfolios_table(conn)
            
            # Step 3: Migrate stock_holdings to holdings
            print("\n📊 Step 3: Migrating holdings table...")
            migrate_holdings_table(conn)
            
            # Step 4: Update portfolio_history
            print("\n📈 Step 4: Updating portfolio_history...")
            update_history_table(conn)
            
            # Step 5: Create new tables
            print("\n✨ Step 5: Creating new tables...")
            create_new_tables(conn)
            
            # Step 6: Initialize data
            print("\n🎯 Step 6: Initializing portfolio metrics...")
            initialize_metrics(conn)
            
            print("\n✅ Migration completed successfully!")
            print("\n📋 Next steps:")
            print("1. Test the API endpoints")
            print("2. Run: python -m app.background.portfolio_tasks update")
            print("3. Set up background scheduler in main.py")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            print("Rolling back changes...")
            raise

def backup_existing_data(conn):
    """Create backup tables"""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS portfolios_backup AS 
        SELECT * FROM portfolios;
    """))
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stock_holdings_backup AS 
        SELECT * FROM stock_holdings;
    """))
    
    print("   ✓ Backup tables created")

def update_portfolios_table(conn):
    """Add new columns to portfolios table"""
    
    # Add initial_balance
    try:
        conn.execute(text("""
            ALTER TABLE portfolios 
            ADD COLUMN IF NOT EXISTS initial_balance FLOAT DEFAULT 10000.00;
        """))
        print("   ✓ Added initial_balance column")
    except Exception as e:
        print(f"   ⚠ initial_balance: {e}")
    
    # Add last_valuation_update
    try:
        conn.execute(text("""
            ALTER TABLE portfolios 
            ADD COLUMN IF NOT EXISTS last_valuation_update TIMESTAMP DEFAULT NOW();
        """))
        print("   ✓ Added last_valuation_update column")
    except Exception as e:
        print(f"   ⚠ last_valuation_update: {e}")
    
    # Add updated_at
    try:
        conn.execute(text("""
            ALTER TABLE portfolios 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
        """))
        print("   ✓ Added updated_at column")
    except Exception as e:
        print(f"   ⚠ updated_at: {e}")
    
    # Set initial_balance for existing portfolios
    conn.execute(text("""
        UPDATE portfolios 
        SET initial_balance = 10000.00 
        WHERE initial_balance IS NULL;
    """))
    print("   ✓ Initialized existing portfolio balances")

def migrate_holdings_table(conn):
    """Migrate stock_holdings to holdings with new structure"""
    
    # Check if holdings table already exists
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'holdings'
        );
    """))
    
    if result.scalar():
        print("   ⚠ Holdings table already exists, skipping migration")
        return
    
    # Rename table
    try:
        conn.execute(text("""
            ALTER TABLE stock_holdings RENAME TO holdings;
        """))
        print("   ✓ Renamed stock_holdings to holdings")
    except Exception as e:
        print(f"   ⚠ Rename table: {e}")
    
    # Add asset_type column
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            ADD COLUMN IF NOT EXISTS asset_type VARCHAR(20) DEFAULT 'STOCK';
        """))
        print("   ✓ Added asset_type column")
    except Exception as e:
        print(f"   ⚠ asset_type: {e}")
    
    # Add current_price
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            ADD COLUMN IF NOT EXISTS current_price FLOAT;
        """))
        print("   ✓ Added current_price column")
    except Exception as e:
        print(f"   ⚠ current_price: {e}")
    
    # Add last_price_update
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            ADD COLUMN IF NOT EXISTS last_price_update TIMESTAMP;
        """))
        print("   ✓ Added last_price_update column")
    except Exception as e:
        print(f"   ⚠ last_price_update: {e}")
    
    # Rename average_price to average_buy_price
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            RENAME COLUMN average_price TO average_buy_price;
        """))
        print("   ✓ Renamed average_price to average_buy_price")
    except Exception as e:
        print(f"   ⚠ Rename column: {e}")
    
    # Change quantity to FLOAT (for crypto/fractional shares)
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            ALTER COLUMN quantity TYPE FLOAT USING quantity::FLOAT;
        """))
        print("   ✓ Changed quantity type to FLOAT")
    except Exception as e:
        print(f"   ⚠ quantity type: {e}")
    
    # Add created_at and updated_at if not exist
    try:
        conn.execute(text("""
            ALTER TABLE holdings 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
        """))
        print("   ✓ Added timestamp columns")
    except Exception as e:
        print(f"   ⚠ timestamp columns: {e}")
    
    # Create indexes
    try:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_symbol 
            ON holdings(portfolio_id, symbol);
        """))
        print("   ✓ Created portfolio_symbol index")
    except Exception as e:
        print(f"   ⚠ index: {e}")

def update_history_table(conn):
    """Update portfolio_history table"""
    
    # Add cash_balance
    try:
        conn.execute(text("""
            ALTER TABLE portfolio_history 
            ADD COLUMN IF NOT EXISTS cash_balance FLOAT DEFAULT 0;
        """))
        
        # Populate cash_balance from portfolios
        conn.execute(text("""
            UPDATE portfolio_history ph
            SET cash_balance = p.cash_balance
            FROM portfolios p
            WHERE ph.portfolio_id = p.id AND ph.cash_balance = 0;
        """))
        print("   ✓ Added and populated cash_balance")
    except Exception as e:
        print(f"   ⚠ cash_balance: {e}")
    
    # Add holdings_value
    try:
        conn.execute(text("""
            ALTER TABLE portfolio_history 
            ADD COLUMN IF NOT EXISTS holdings_value FLOAT DEFAULT 0;
        """))
        
        # Calculate holdings_value from total_value and cash_balance
        conn.execute(text("""
            UPDATE portfolio_history 
            SET holdings_value = total_value - cash_balance
            WHERE holdings_value = 0;
        """))
        print("   ✓ Added and populated holdings_value")
    except Exception as e:
        print(f"   ⚠ holdings_value: {e}")
    
    # Rename date to timestamp if needed
    try:
        conn.execute(text("""
            ALTER TABLE portfolio_history 
            RENAME COLUMN date TO timestamp;
        """))
        print("   ✓ Renamed date to timestamp")
    except Exception as e:
        print(f"   ⚠ Rename date column: {e}")
    
    # Create index
    try:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp 
            ON portfolio_history(portfolio_id, timestamp);
        """))
        print("   ✓ Created portfolio_timestamp index")
    except Exception as e:
        print(f"   ⚠ index: {e}")

def create_new_tables(conn):
    """Create new tables for enhanced features"""
    
    # Create portfolio_daily_snapshots
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS portfolio_daily_snapshots (
            id SERIAL PRIMARY KEY,
            portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
            date TIMESTAMP NOT NULL,
            total_value FLOAT NOT NULL,
            cash_balance FLOAT NOT NULL,
            holdings_value FLOAT NOT NULL,
            daily_return FLOAT DEFAULT 0.0,
            total_return FLOAT DEFAULT 0.0,
            total_return_pct FLOAT DEFAULT 0.0,
            volatility FLOAT,
            sharpe_ratio FLOAT,
            max_drawdown FLOAT,
            portfolio_rank INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """))
    print("   ✓ Created portfolio_daily_snapshots table")
    
    # Create index
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_portfolio_date 
        ON portfolio_daily_snapshots(portfolio_id, date);
    """))
    print("   ✓ Created portfolio_date index")
    
    # Create portfolio_metrics
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS portfolio_metrics (
            id SERIAL PRIMARY KEY,
            portfolio_id INTEGER NOT NULL UNIQUE REFERENCES portfolios(id) ON DELETE CASCADE,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            win_rate FLOAT DEFAULT 0.0,
            realized_pnl FLOAT DEFAULT 0.0,
            unrealized_pnl FLOAT DEFAULT 0.0,
            total_pnl FLOAT DEFAULT 0.0,
            best_trade FLOAT DEFAULT 0.0,
            worst_trade FLOAT DEFAULT 0.0,
            avg_win FLOAT DEFAULT 0.0,
            avg_loss FLOAT DEFAULT 0.0,
            max_drawdown FLOAT DEFAULT 0.0,
            current_drawdown FLOAT DEFAULT 0.0,
            sharpe_ratio FLOAT,
            last_updated TIMESTAMP DEFAULT NOW()
        );
    """))
    print("   ✓ Created portfolio_metrics table")

def initialize_metrics(conn):
    """Initialize metrics for all existing portfolios"""
    
    # Get all portfolio IDs
    result = conn.execute(text("SELECT id FROM portfolios;"))
    portfolio_ids = [row[0] for row in result]
    
    # Insert metrics records
    for portfolio_id in portfolio_ids:
        conn.execute(text("""
            INSERT INTO portfolio_metrics (portfolio_id)
            VALUES (:portfolio_id)
            ON CONFLICT (portfolio_id) DO NOTHING;
        """), {"portfolio_id": portfolio_id})
    
    print(f"   ✓ Initialized metrics for {len(portfolio_ids)} portfolios")

if __name__ == "__main__":
    print("=" * 60)
    print("  Portfolio System Migration Script")
    print("=" * 60)
    print("\n⚠️  WARNING: This will modify your database!")
    print("Make sure you have a backup before proceeding.")
    print("\nThis script will:")
    print("  • Create backup tables")
    print("  • Add new columns to existing tables")
    print("  • Migrate stock_holdings → holdings")
    print("  • Create portfolio_daily_snapshots table")
    print("  • Create portfolio_metrics table")
    print("  • Initialize metrics for all portfolios")
    
    response = input("\n🤔 Do you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        run_migration()
    else:
        print("\n❌ Migration cancelled.")
        print("No changes were made to your database.")