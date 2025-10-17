import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection info
DB_NAME = "trading-postgres"
DB_USER = "ramy"
DB_PASSWORD = "Azert11-"
DB_HOST = "localhost"
DB_PORT = 5433

# Connect to the default 'postgres' database
conn = psycopg2.connect(
    dbname="postgres",
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Terminate all connections to the database
cur.execute(f"""
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();
""")

# Drop the database
cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
print(f"Database '{DB_NAME}' has been deleted.")

cur.close()
conn.close()
