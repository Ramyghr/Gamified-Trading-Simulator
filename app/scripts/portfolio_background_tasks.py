"""
Background tasks for portfolio management
These should be run periodically using a task scheduler (Celery, APScheduler, or cron)
"""

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models.portfolio import Portfolio
from app.services.portfolio_service import PortfolioService
from datetime import datetime, time
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= Periodic Update Tasks =============

async def update_all_portfolio_valuations():
    """
    Update all portfolio valuations with latest market prices
    Run this every 5-15 minutes during market hours
    """
    db = SessionLocal()
    try:
        service = PortfolioService(db)
        portfolios = db.query(Portfolio).all()
        
        logger.info(f"Updating valuations for {len(portfolios)} portfolios")
        
        for portfolio in portfolios:
            try:
                await service.update_portfolio_valuation(portfolio)
                logger.info(f"Updated portfolio {portfolio.id} - Total value: ${portfolio.total_value:.2f}")
            except Exception as e:
                logger.error(f"Error updating portfolio {portfolio.id}: {e}")
        
        logger.info("All portfolio valuations updated successfully")
        
    except Exception as e:
        logger.error(f"Error in update_all_portfolio_valuations: {e}")
    finally:
        db.close()

def create_all_daily_snapshots():
    """
    Create end-of-day snapshots for all portfolios
    Run this once per day after market close (e.g., 5 PM ET)
    """
    db = SessionLocal()
    try:
        service = PortfolioService(db)
        portfolios = db.query(Portfolio).all()
        
        logger.info(f"Creating daily snapshots for {len(portfolios)} portfolios")
        
        for portfolio in portfolios:
            try:
                service.create_daily_snapshot(portfolio.id)
                logger.info(f"Created snapshot for portfolio {portfolio.id}")
            except Exception as e:
                logger.error(f"Error creating snapshot for portfolio {portfolio.id}: {e}")
        
        logger.info("All daily snapshots created successfully")
        
    except Exception as e:
        logger.error(f"Error in create_all_daily_snapshots: {e}")
    finally:
        db.close()

def calculate_all_portfolio_metrics():
    """
    Recalculate metrics for all portfolios
    Run this daily or after major events
    """
    db = SessionLocal()
    try:
        service = PortfolioService(db)
        portfolios = db.query(Portfolio).all()
        
        logger.info(f"Calculating metrics for {len(portfolios)} portfolios")
        
        for portfolio in portfolios:
            try:
                service.calculate_portfolio_metrics(portfolio.id)
                logger.info(f"Calculated metrics for portfolio {portfolio.id}")
            except Exception as e:
                logger.error(f"Error calculating metrics for portfolio {portfolio.id}: {e}")
        
        logger.info("All portfolio metrics calculated successfully")
        
    except Exception as e:
        logger.error(f"Error in calculate_all_portfolio_metrics: {e}")
    finally:
        db.close()

def update_portfolio_rankings():
    """
    Update portfolio rankings in daily snapshots
    Run this once per day after snapshots are created
    """
    db = SessionLocal()
    try:
        from app.models.portfolio import PortfolioDailySnapshot
        from sqlalchemy import func, desc
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get today's snapshots sorted by return percentage
        snapshots = db.query(PortfolioDailySnapshot).filter(
            PortfolioDailySnapshot.date == today
        ).order_by(desc(PortfolioDailySnapshot.total_return_pct)).all()
        
        logger.info(f"Updating rankings for {len(snapshots)} portfolio snapshots")
        
        # Assign ranks
        for rank, snapshot in enumerate(snapshots, start=1):
            snapshot.portfolio_rank = rank
        
        db.commit()
        logger.info("Portfolio rankings updated successfully")
        
    except Exception as e:
        logger.error(f"Error in update_portfolio_rankings: {e}")
        db.rollback()
    finally:
        db.close()

# ============= Scheduled Task Runners =============

def run_market_hours_update():
    """
    Update valuations during market hours
    Schedule: Every 5-15 minutes, Monday-Friday, 9:30 AM - 4:00 PM ET
    """
    now = datetime.now().time()
    market_open = time(9, 30)
    market_close = time(16, 0)
    
    # Check if during market hours (simplified - doesn't account for holidays)
    if now >= market_open and now <= market_close:
        logger.info("Running market hours valuation update")
        asyncio.run(update_all_portfolio_valuations())
    else:
        logger.info("Outside market hours, skipping valuation update")

def run_end_of_day_tasks():
    """
    Run all end-of-day tasks
    Schedule: Daily at 5:00 PM ET (after market close)
    """
    logger.info("Running end-of-day tasks")
    
    # 1. Final valuation update
    asyncio.run(update_all_portfolio_valuations())
    
    # 2. Create daily snapshots
    create_all_daily_snapshots()
    
    # 3. Calculate metrics
    calculate_all_portfolio_metrics()
    
    # 4. Update rankings
    update_portfolio_rankings()
    
    logger.info("End-of-day tasks completed")

# ============= APScheduler Configuration Example =============

def setup_scheduler():
    """
    Example setup using APScheduler
    Add this to your main.py or create a separate scheduler.py
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BackgroundScheduler()
    
    # Update valuations every 10 minutes during market hours
    scheduler.add_job(
        run_market_hours_update,
        CronTrigger(
            day_of_week='mon-fri',
            hour='9-16',
            minute='*/10',
            timezone='America/New_York'
        ),
        id='market_hours_update',
        name='Update portfolio valuations during market hours'
    )
    
    # End-of-day tasks at 5 PM ET
    scheduler.add_job(
        run_end_of_day_tasks,
        CronTrigger(
            day_of_week='mon-fri',
            hour=17,
            minute=0,
            timezone='America/New_York'
        ),
        id='end_of_day_tasks',
        name='Run end-of-day portfolio tasks'
    )
    
    scheduler.start()
    logger.info("Portfolio background scheduler started")
    
    return scheduler

# ============= Celery Tasks Example =============

"""
If using Celery, define tasks like this:

from celery import Celery

celery_app = Celery('portfolio_tasks', broker='redis://localhost:6379/0')

@celery_app.task
def celery_update_valuations():
    asyncio.run(update_all_portfolio_valuations())

@celery_app.task
def celery_create_snapshots():
    create_all_daily_snapshots()

@celery_app.task
def celery_calculate_metrics():
    calculate_all_portfolio_metrics()

# In celerybeat-schedule.py:
celery_app.conf.beat_schedule = {
    'update-valuations': {
        'task': 'tasks.celery_update_valuations',
        'schedule': 600.0,  # Every 10 minutes
    },
    'create-snapshots': {
        'task': 'tasks.celery_create_snapshots',
        'schedule': crontab(hour=17, minute=0),  # 5 PM daily
    },
}
"""

# ============= Main Entry Point for Testing =============

if __name__ == "__main__":
    """
    For testing purposes - run tasks manually
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python portfolio_background_tasks.py [update|snapshot|metrics|rankings|all]")
        sys.exit(1)
    
    task = sys.argv[1]
    
    if task == "update":
        asyncio.run(update_all_portfolio_valuations())
    elif task == "snapshot":
        create_all_daily_snapshots()
    elif task == "metrics":
        calculate_all_portfolio_metrics()
    elif task == "rankings":
        update_portfolio_rankings()
    elif task == "all":
        run_end_of_day_tasks()
    else:
        print(f"Unknown task: {task}")
        sys.exit(1)
