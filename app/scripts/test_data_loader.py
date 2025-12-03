from app.crisis_simulator.data_loader import HistoricalDataLoader

loader = HistoricalDataLoader()

# Test each crisis
for crisis in ["great_depression", "black_monday", "dotcom_bubble", 
               "financial_crisis_2008", "covid_crash"]:
    print(f"\n=== Testing {crisis} ===")
    try:
        df = loader.load_crisis_data(crisis)
        print(f"✓ Loaded {len(df)} days")
        print(f"✓ Symbols: {list(df.columns)}")
        print(f"✓ Date range: {df.index.min()} to {df.index.max()}")
    except Exception as e:
        print(f"✗ Error: {e}")