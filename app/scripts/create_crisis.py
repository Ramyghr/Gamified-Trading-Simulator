# scripts/fix_crisis_tables.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://ramy:Azert-11@localhost:5433/trading_simulator"

def fix_crisis_tables():
    print("Creating crisis simulation tables...")
    engine = create_engine(DATABASE_URL)
    
    crisis_tables = [
        text("""
        CREATE TABLE IF NOT EXISTS crisis_simulations (
            id SERIAL PRIMARY KEY,
            crisis_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            real_start_time TIMESTAMP,
            real_end_time TIMESTAMP,
            historical_start_date TIMESTAMP NOT NULL,
            historical_end_date TIMESTAMP NOT NULL,
            current_historical_time TIMESTAMP,
            duration_minutes INTEGER DEFAULT 60,
            time_compression_ratio FLOAT NOT NULL,
            phase_config JSON NOT NULL,
            current_phase VARCHAR(50),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            max_participants INTEGER DEFAULT 100,
            is_competitive BOOLEAN DEFAULT true
        )
        """),
        text("""
        CREATE TABLE IF NOT EXISTS simulation_participants (
            id SERIAL PRIMARY KEY,
            simulation_id INTEGER,
            user_id INTEGER,
            joined_at TIMESTAMP DEFAULT NOW(),
            is_active BOOLEAN DEFAULT true,
            finished_at TIMESTAMP,
            initial_cash FLOAT DEFAULT 100000.0,
            initial_portfolio_value FLOAT DEFAULT 100000.0,
            current_cash FLOAT DEFAULT 100000.0,
            current_portfolio_value FLOAT,
            current_total_value FLOAT,
            total_return_pct FLOAT DEFAULT 0.0,
            max_drawdown_pct FLOAT DEFAULT 0.0,
            sharpe_ratio FLOAT,
            total_trades INTEGER DEFAULT 0,
            profitable_trades INTEGER DEFAULT 0,
            max_leverage_used FLOAT DEFAULT 1.0,
            margin_calls_count INTEGER DEFAULT 0,
            detected_biases JSON DEFAULT '{}',
            final_rank INTEGER,
            final_score FLOAT
        )
        """),
        text("""
        CREATE TABLE IF NOT EXISTS simulation_orders (
            id SERIAL PRIMARY KEY,
            participant_id INTEGER,
            symbol VARCHAR(20) NOT NULL,
            order_type VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            quantity FLOAT NOT NULL,
            limit_price FLOAT,
            stop_price FLOAT,
            filled_price FLOAT,
            filled_quantity FLOAT DEFAULT 0.0,
            status VARCHAR(20) DEFAULT 'PENDING',
            placed_at_historical TIMESTAMP NOT NULL,
            filled_at_historical TIMESTAMP,
            placed_at_real TIMESTAMP DEFAULT NOW(),
            filled_at_real TIMESTAMP,
            commission FLOAT DEFAULT 0.0,
            rejection_reason VARCHAR(255)
        )
        """),
        text("""
        CREATE TABLE IF NOT EXISTS simulation_positions (
            id SERIAL PRIMARY KEY,
            participant_id INTEGER,
            symbol VARCHAR(20) NOT NULL,
            quantity FLOAT NOT NULL,
            average_cost FLOAT NOT NULL,
            current_price FLOAT,
            unrealized_pnl FLOAT DEFAULT 0.0,
            unrealized_pnl_pct FLOAT DEFAULT 0.0,
            realized_pnl FLOAT DEFAULT 0.0,
            opened_at TIMESTAMP DEFAULT NOW(),
            last_updated TIMESTAMP DEFAULT NOW()
        )
        """),
        text("""
        CREATE TABLE IF NOT EXISTS simulation_leaderboard (
            id SERIAL PRIMARY KEY,
            simulation_id INTEGER,
            user_id INTEGER,
            current_rank INTEGER NOT NULL,
            previous_rank INTEGER,
            total_value FLOAT NOT NULL,
            total_return_pct FLOAT NOT NULL,
            sharpe_ratio FLOAT,
            competition_score FLOAT NOT NULL,
            snapshot_at_historical TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """),
        text("""
        CREATE TABLE IF NOT EXISTS simulation_snapshots (
            id SERIAL PRIMARY KEY,
            participant_id INTEGER,
            historical_time TIMESTAMP NOT NULL,
            real_time TIMESTAMP DEFAULT NOW(),
            portfolio_state JSON NOT NULL,
            total_return_pct FLOAT DEFAULT 0.0,
            total_value FLOAT NOT NULL
        )
        """)
    ]
    
    try:
        with engine.connect() as conn:
            for sql in crisis_tables:
                conn.execute(sql)
            conn.commit()
        print("✅ Crisis tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if fix_crisis_tables():
        print("🎉 Crisis tables fixed!")
    else:
        print("💥 Failed to create crisis tables!")