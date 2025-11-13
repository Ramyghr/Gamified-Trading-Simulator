"""
Benchmark market data provider performance
Tests speed, reliability, and data quality
Run: python scripts/benchmark_performance.py
"""
import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.market_data.aggregator import market_data_service
from app.constants.market_constants import AssetClass
from app.constants.timeframes import Timeframe
from app.schemas.candle import CandleRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Benchmark market data providers"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
    
    async def benchmark_quote_speed(self, symbol: str, runs: int = 10) -> Dict:
        """Benchmark single quote fetching speed"""
        logger.info(f"\n📊 Benchmarking quote speed: {symbol} ({runs} runs)")
        
        times = []
        errors = 0
        
        for i in range(runs):
            start = time.time()
            try:
                quote = await market_data_service.get_quote(symbol)
                elapsed = (time.time() - start) * 1000  # Convert to ms
                times.append(elapsed)
                logger.info(f"  Run {i+1}: {elapsed:.2f}ms - ${quote.close:.2f}")
            except Exception as e:
                errors += 1
                logger.error(f"  Run {i+1}: FAILED - {e}")
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        if times:
            return {
                "avg_ms": mean(times),
                "median_ms": median(times),
                "min_ms": min(times),
                "max_ms": max(times),
                "success_rate": ((runs - errors) / runs) * 100,
                "total_runs": runs
            }
        return {"error": "All runs failed"}
    
    async def benchmark_batch_quotes(self, symbols: List[str]) -> Dict:
        """Benchmark batch quote fetching"""
        logger.info(f"\n📊 Benchmarking batch quotes: {len(symbols)} symbols")
        
        start = time.time()
        try:
            from app.schemas.quote import QuoteRequest
            request = QuoteRequest(symbols=symbols)
            quotes = await market_data_service.get_quotes(request)
            elapsed = (time.time() - start) * 1000
            
            logger.info(f"  ✓ Retrieved {len(quotes)}/{len(symbols)} quotes in {elapsed:.2f}ms")
            logger.info(f"  ✓ Average: {elapsed/len(symbols):.2f}ms per quote")
            
            return {
                "total_ms": elapsed,
                "per_quote_ms": elapsed / len(symbols),
                "success_count": len(quotes),
                "requested_count": len(symbols),
                "success_rate": (len(quotes) / len(symbols)) * 100
            }
        except Exception as e:
            logger.error(f"  ✗ Batch failed: {e}")
            return {"error": str(e)}
    
    async def benchmark_candles(self, symbol: str, timeframe: Timeframe, limit: int = 100) -> Dict:
        """Benchmark historical candle fetching"""
        logger.info(f"\n📊 Benchmarking candles: {symbol} {timeframe.value} (limit={limit})")
        
        start = time.time()
        try:
            request = CandleRequest(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            candles = await market_data_service.get_candles(request)
            elapsed = (time.time() - start) * 1000
            
            logger.info(f"  ✓ Retrieved {len(candles)} candles in {elapsed:.2f}ms")
            
            if candles:
                latest = candles[-1]
                logger.info(f"  ✓ Latest: {latest.timestamp.date()} - Close: ${latest.close:.2f}")
            
            return {
                "total_ms": elapsed,
                "per_candle_ms": elapsed / len(candles) if candles else 0,
                "candle_count": len(candles),
                "requested_limit": limit
            }
        except Exception as e:
            logger.error(f"  ✗ Candles failed: {e}")
            return {"error": str(e)}
    
    async def benchmark_provider_health(self) -> Dict:
        """Check health of all providers"""
        logger.info("\n📊 Checking provider health")
        
        health = await market_data_service.health_check()
        
        for provider, status in health.items():
            icon = "✅" if status else "❌"
            logger.info(f"  {icon} {provider}: {'HEALTHY' if status else 'UNHEALTHY'}")
        
        healthy_count = sum(1 for status in health.values() if status)
        
        return {
            "providers": health,
            "healthy_count": healthy_count,
            "total_count": len(health),
            "health_percentage": (healthy_count / len(health)) * 100 if health else 0
        }
    
    async def benchmark_cache_effectiveness(self, symbol: str, runs: int = 5) -> Dict:
        """Benchmark cache hit rate"""
        logger.info(f"\n📊 Benchmarking cache effectiveness: {symbol}")
        
        # Clear cache first
        from app.services.market_data.cache_service import CacheService
        cache = CacheService()
        await cache.connect()
        await cache.delete(f"quote:{symbol}")
        
        uncached_times = []
        cached_times = []
        
        # First run (uncached)
        logger.info("  Testing uncached requests...")
        for i in range(2):
            start = time.time()
            await market_data_service.get_quote(symbol)
            elapsed = (time.time() - start) * 1000
            uncached_times.append(elapsed)
            await cache.delete(f"quote:{symbol}")  # Clear between runs
            await asyncio.sleep(0.5)
        
        # Subsequent runs (cached)
        logger.info("  Testing cached requests...")
        await market_data_service.get_quote(symbol)  # Prime cache
        
        for i in range(runs):
            start = time.time()
            await market_data_service.get_quote(symbol)
            elapsed = (time.time() - start) * 1000
            cached_times.append(elapsed)
            await asyncio.sleep(0.1)
        
        avg_uncached = mean(uncached_times)
        avg_cached = mean(cached_times)
        speedup = avg_uncached / avg_cached if avg_cached else 0
        
        logger.info(f"  Uncached avg: {avg_uncached:.2f}ms")
        logger.info(f"  Cached avg: {avg_cached:.2f}ms")
        logger.info(f"  Speedup: {speedup:.2f}x faster")
        
        return {
            "avg_uncached_ms": avg_uncached,
            "avg_cached_ms": avg_cached,
            "speedup_factor": speedup,
            "cache_savings_ms": avg_uncached - avg_cached
        }
    
    async def benchmark_concurrent_load(self, symbols: List[str], concurrent: int = 10) -> Dict:
        """Benchmark concurrent request handling"""
        logger.info(f"\n📊 Benchmarking concurrent load: {concurrent} concurrent requests")
        
        async def fetch_quote(symbol: str) -> float:
            start = time.time()
            try:
                await market_data_service.get_quote(symbol)
                return (time.time() - start) * 1000
            except:
                return -1
        
        start = time.time()
        
        # Create batches of concurrent requests
        tasks = []
        for symbol in symbols[:concurrent]:
            tasks.append(fetch_quote(symbol))
        
        results = await asyncio.gather(*tasks)
        total_elapsed = (time.time() - start) * 1000
        
        successful = [r for r in results if r > 0]
        
        logger.info(f"  ✓ Completed {len(successful)}/{concurrent} in {total_elapsed:.2f}ms")
        logger.info(f"  ✓ Average per request: {mean(successful):.2f}ms")
        
        return {
            "total_ms": total_elapsed,
            "successful_count": len(successful),
            "requested_count": concurrent,
            "avg_request_ms": mean(successful) if successful else 0,
            "success_rate": (len(successful) / concurrent) * 100
        }
    
    async def run_full_benchmark(self):
        """Run complete benchmark suite"""
        logger.info("=" * 60)
        logger.info("🚀 MARKET DATA PERFORMANCE BENCHMARK")
        logger.info("=" * 60)
        
        # 1. Provider Health
        self.results["health"] = await self.benchmark_provider_health()
        
        # 2. Single Quote Speed
        self.results["quote_speed_aapl"] = await self.benchmark_quote_speed("AAPL", runs=5)
        self.results["quote_speed_btc"] = await self.benchmark_quote_speed("BTC", runs=5)
        
        # 3. Batch Quotes
        batch_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        self.results["batch_quotes"] = await self.benchmark_batch_quotes(batch_symbols)
        
        # 4. Historical Candles
        self.results["candles_1d"] = await self.benchmark_candles("AAPL", Timeframe.ONE_DAY, limit=30)
        self.results["candles_1h"] = await self.benchmark_candles("AAPL", Timeframe.ONE_HOUR, limit=24)
        
        # 5. Cache Effectiveness
        self.results["cache"] = await self.benchmark_cache_effectiveness("AAPL", runs=5)
        
        # 6. Concurrent Load
        concurrent_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "AMD", "NFLX", "PYPL"]
        self.results["concurrent"] = await self.benchmark_concurrent_load(concurrent_symbols, concurrent=10)
        
        self.print_summary()
    
    def print_summary(self):
        """Print benchmark summary"""
        logger.info("\n" + "=" * 60)
        logger.info("📈 BENCHMARK SUMMARY")
        logger.info("=" * 60)
        
        # Provider Health
        health = self.results.get("health", {})
        logger.info(f"\n🏥 Provider Health:")
        logger.info(f"  Healthy: {health.get('healthy_count', 0)}/{health.get('total_count', 0)}")
        logger.info(f"  Rate: {health.get('health_percentage', 0):.1f}%")
        
        # Quote Speed
        if "quote_speed_aapl" in self.results:
            qs = self.results["quote_speed_aapl"]
            logger.info(f"\n⚡ Single Quote Speed (AAPL):")
            logger.info(f"  Average: {qs.get('avg_ms', 0):.2f}ms")
            logger.info(f"  Median: {qs.get('median_ms', 0):.2f}ms")
            logger.info(f"  Range: {qs.get('min_ms', 0):.2f}ms - {qs.get('max_ms', 0):.2f}ms")
            logger.info(f"  Success Rate: {qs.get('success_rate', 0):.1f}%")
        
        # Batch Performance
        if "batch_quotes" in self.results:
            bq = self.results["batch_quotes"]
            logger.info(f"\n📦 Batch Quotes:")
            logger.info(f"  Total Time: {bq.get('total_ms', 0):.2f}ms")
            logger.info(logger.info(f"  Per Quote: {bq.get('per_quote_ms', 0):.2f}ms")
            logger.info(f"  Success Rate: {bq.get('success_rate', 0):.1f}%")
        
        # Cache Performance
        if "cache" in self.results:
            cache = self.results["cache"]
            logger.info(f"\n💾 Cache Performance:")
            logger.info(f"  Uncached: {cache.get('avg_uncached_ms', 0):.2f}ms")
            logger.info(f"  Cached: {cache.get('avg_cached_ms', 0):.2f}ms")
            logger.info(f"  Speedup: {cache.get('speedup_factor', 0):.2f}x")
            logger.info(f"  Savings: {cache.get('cache_savings_ms', 0):.2f}ms per request")
        
        # Candles Performance
        if "candles_1d" in self.results:
            candles = self.results["candles_1d"]
            logger.info(f"\n📊 Historical Candles (1D):")
            logger.info(f"  Total Time: {candles.get('total_ms', 0):.2f}ms")
            logger.info(f"  Candles Retrieved: {candles.get('candle_count', 0)}")
            logger.info(f"  Per Candle: {candles.get('per_candle_ms', 0):.2f}ms")
        
        # Concurrent Load
        if "concurrent" in self.results:
            conc = self.results["concurrent"]
            logger.info(f"\n🔄 Concurrent Load (10 requests):")
            logger.info(f"  Total Time: {conc.get('total_ms', 0):.2f}ms")
            logger.info(f"  Avg Per Request: {conc.get('avg_request_ms', 0):.2f}ms")
            logger.info(f"  Success Rate: {conc.get('success_rate', 0):.1f}%")
        
        logger.info("\n" + "=" * 60)
        
        # Performance grades
        self.calculate_grades()
    
    def calculate_grades(self):
        """Calculate performance grades"""
        logger.info("\n🎯 PERFORMANCE GRADES:")
        
        grades = []
        
        # Speed grade (based on avg quote speed)
        if "quote_speed_aapl" in self.results:
            avg_ms = self.results["quote_speed_aapl"].get("avg_ms", 1000)
            if avg_ms < 100:
                grade = "A+"
            elif avg_ms < 200:
                grade = "A"
            elif avg_ms < 500:
                grade = "B"
            elif avg_ms < 1000:
                grade = "C"
            else:
                grade = "D"
            grades.append(("Speed", grade, f"{avg_ms:.0f}ms"))
        
        # Reliability grade (based on success rate)
        if "quote_speed_aapl" in self.results:
            success_rate = self.results["quote_speed_aapl"].get("success_rate", 0)
            if success_rate >= 99:
                grade = "A+"
            elif success_rate >= 95:
                grade = "A"
            elif success_rate >= 90:
                grade = "B"
            elif success_rate >= 80:
                grade = "C"
            else:
                grade = "D"
            grades.append(("Reliability", grade, f"{success_rate:.1f}%"))
        
        # Cache effectiveness grade
        if "cache" in self.results:
            speedup = self.results["cache"].get("speedup_factor", 1)
            if speedup > 10:
                grade = "A+"
            elif speedup > 5:
                grade = "A"
            elif speedup > 3:
                grade = "B"
            elif speedup > 2:
                grade = "C"
            else:
                grade = "D"
            grades.append(("Cache", grade, f"{speedup:.1f}x"))
        
        # Provider health grade
        if "health" in self.results:
            health_pct = self.results["health"].get("health_percentage", 0)
            if health_pct == 100:
                grade = "A+"
            elif health_pct >= 80:
                grade = "A"
            elif health_pct >= 60:
                grade = "B"
            elif health_pct >= 40:
                grade = "C"
            else:
                grade = "D"
            grades.append(("Health", grade, f"{health_pct:.0f}%"))
        
        for category, grade, value in grades:
            logger.info(f"  {category:15} {grade:3} ({value})")
        
        # Overall grade
        grade_values = {"A+": 4.3, "A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0}
        if grades:
            avg_grade = sum(grade_values.get(g[1], 0) for g in grades) / len(grades)
            if avg_grade >= 4.0:
                overall = "A+ Excellent"
            elif avg_grade >= 3.5:
                overall = "A  Great"
            elif avg_grade >= 2.5:
                overall = "B  Good"
            elif avg_grade >= 1.5:
                overall = "C  Fair"
            else:
                overall = "D  Needs Work"
            
            logger.info(f"\n  {'OVERALL':15} {overall}")


async def main():
    benchmark = PerformanceBenchmark()
    await benchmark.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())