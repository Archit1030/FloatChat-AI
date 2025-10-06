"""
Data Migration Script for Railway Deployment
Migrates processed ARGO data from local PostgreSQL to Railway PostgreSQL
"""

import pandas as pd
import logging
from sqlalchemy import create_engine, text
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data_to_railway():
    """Migrate processed data from local to Railway PostgreSQL"""
    
    # Local database (source)
    local_db_url = "postgresql+psycopg2://postgres:Arcombad1030@localhost:5432/argo"
    
    # Railway database (destination) - get from environment
    railway_db_url = os.getenv("DATABASE_URL")
    
    if not railway_db_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Set it to your Railway PostgreSQL URL")
        return False
    
    try:
        # Connect to both databases
        logger.info("🔌 Connecting to local database...")
        local_engine = create_engine(local_db_url)
        
        logger.info("🔌 Connecting to Railway database...")
        railway_engine = create_engine(railway_db_url)
        
        # Check local data availability
        with local_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM measurements;"))
            local_count = result.fetchone()[0]
            
        if local_count == 0:
            logger.error("❌ No data found in local database")
            logger.info("Run: python argo_data_processor.py first")
            return False
        
        logger.info(f"📊 Found {local_count:,} measurements in local database")
        
        # Create tables in Railway database
        logger.info("🏗️ Creating tables in Railway database...")
        
        create_tables_sql = """
        -- Create tables if they don't exist
        CREATE TABLE IF NOT EXISTS floats (
            float_id VARCHAR(50) PRIMARY KEY,
            wmo_id INTEGER UNIQUE,
            deployment_date DATE,
            deployment_lat FLOAT,
            deployment_lon FLOAT,
            status VARCHAR(20) DEFAULT 'ACTIVE',
            last_contact DATE,
            platform_type VARCHAR(50),
            data_center VARCHAR(50)
        );
        
        CREATE TABLE IF NOT EXISTS profiles (
            profile_id SERIAL PRIMARY KEY,
            float_id VARCHAR(50) REFERENCES floats(float_id),
            cycle_number INTEGER,
            profile_date DATE,
            profile_lat FLOAT,
            profile_lon FLOAT,
            n_levels INTEGER,
            quality_flag INTEGER DEFAULT 1,
            UNIQUE(float_id, cycle_number)
        );
        
        CREATE TABLE IF NOT EXISTS measurements (
            id SERIAL PRIMARY KEY,
            profile_id INTEGER REFERENCES profiles(profile_id),
            float_id VARCHAR(50) REFERENCES floats(float_id),
            time TIMESTAMP,
            lat FLOAT,
            lon FLOAT,
            depth FLOAT,
            pressure FLOAT,
            temperature FLOAT,
            salinity FLOAT,
            oxygen FLOAT,
            ph FLOAT,
            chlorophyll FLOAT,
            quality_flag INTEGER DEFAULT 1
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_measurements_float_id ON measurements(float_id);
        CREATE INDEX IF NOT EXISTS idx_measurements_time ON measurements(time);
        CREATE INDEX IF NOT EXISTS idx_measurements_lat_lon ON measurements(lat, lon);
        CREATE INDEX IF NOT EXISTS idx_measurements_depth ON measurements(depth);
        """
        
        with railway_engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        
        # Migrate data table by table
        tables = ['floats', 'profiles', 'measurements']
        
        for table in tables:
            logger.info(f"📦 Migrating {table} table...")
            
            # Read from local
            df = pd.read_sql_query(f"SELECT * FROM {table};", local_engine)
            
            if not df.empty:
                # Write to Railway (replace existing data)
                df.to_sql(table, railway_engine, if_exists='replace', index=False, method='multi')
                logger.info(f"✅ Migrated {len(df):,} records to {table}")
            else:
                logger.warning(f"⚠️ No data found in {table}")
        
        # Verify migration
        with railway_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM measurements;"))
            railway_count = result.fetchone()[0]
        
        logger.info(f"🎉 Migration complete! {railway_count:,} measurements in Railway database")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--railway-url":
        if len(sys.argv) < 3:
            print("Usage: python migrate_data_to_railway.py --railway-url <DATABASE_URL>")
            sys.exit(1)
        
        os.environ["DATABASE_URL"] = sys.argv[2]
    
    success = migrate_data_to_railway()
    
    if success:
        print("🎉 Data migration successful!")
        print("Your Railway deployment now has real ARGO data!")
    else:
        print("❌ Migration failed. Check the logs above.")
        sys.exit(1)