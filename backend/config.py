import os

# DB Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@emm_postgres_db/backend_db")
