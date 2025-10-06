#!/usr/bin/env python3
"""
Migrate processed ARGO data from local PostgreSQL to Railway PostgreSQL
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_engine():
    """Get local PostgreSQL engine"""
    try:
        # Try local config first
        import config
        return create_engine(config.DATABASE_URL)
    except ImportError:
        # Fallback to environment or default
        db_password = os.getenv("DB_PASSWORD", "Arcombad1030")
        local_url = f"postgresql+psycopg2://postgres:{quote_plus(db_password)}@localhost:5432/argo"
        return create_engine(local_url)

def get_railway_engine():
    """Get Railway PostgreSQL engine from environment"""
    railway_url = os.getenv("RAILWAY_DATABASE_URL")
    if not railway_url:
        logger.error("❌ RAILWAY_DATABASE_URL environment variable not set")
        logger.info("💡 Get this from Railway dashboard → PostgreSQL → Connect → Database URL")
        return None
    
    return create_engine(railway_url)

def check_local_data():
    """Check what data exists locally"""
    try:
        local_engine = get_local_engine()
        
        with local_engine.connect() as conn:
            # Check tables exist
            tables_query = """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('floats', 'profiles', 'measurements');
            """
            tables_df = pd.read_sql_query(tables_query, conn)
            
            if tables_df.empty:
                logger.error("❌ No ARGO tables found in local database")
                return False
            
            logger.info(f"✅ Found tables: {', '.join(tables_df['table_name'].tolist())}")
            
            # Check data counts
            for table in ['floats', 'profiles', 'measurements']:
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    logger.info(f"📊 {table}: {count:,} records")
                except Exception as e:
                    logger.warning(f"⚠️ Could not count {table}: {e}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error checking local data: {e}")
        return False

def create_railway_tables(railway_engine):
    """Create tables in Railway PostgreSQL"""
    
    create_tables_sql = [
        """CREATE TABLE IF NOT EXISTS floats (
            float_id VARCHAR(50) PRIMARY KEY,
            wmo_id INTEGER,
            deployment_date DATE,
            deployment_lat FLOAT,
            deployment_lon FLOAT,
            status VARCHAR(20) DEFAULT 'ACTIVE',
            last_contact DATE,
            created_at TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS profiles (
            profile_id SERIAL PRIMARY KEY,
            float_id VARCHAR(50),
            cycle_number INTEGER,
            profile_date DATE,
            profile_lat FLOAT,
            profile_lon FLOAT,
            n_levels INTEGER
        )""",
        
        """CREATE TABLE IF NOT EXISTS measurements (
            id SERIAL PRIMARY KEY,
            profile_id INTEGER,
            float_id VARCHAR(50),
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
        )""",
        
        "CREATE INDEX IF NOT EXISTS idx_measurements_time ON measurements(time)",
        "CREATE INDEX IF NOT EXISTS idx_measurements_float_id ON measurements(float_id)"
    ]
    
    try:
        with railway_engine.connect() as conn:
            for sql_statement in create_tables_sql:
                conn.execute(text(sql_statement))
            conn.commit()
            logger.info("✅ Railway tables created successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Error creating Railway tables: {e}")
        return False

def get_table_columns(engine, table_name):
    """Get column names for a table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND table_schema = 'public'
                ORDER BY ordinal_position
            """))
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.warning(f"Could not get columns for {table_name}: {e}")
        return []

def migrate_table_data(local_engine, railway_engine, table_name, chunk_size=1000):
    """Migrate data from local to Railway for a specific table"""
    
    try:
        logger.info(f"🔄 Migrating {table_name}...")
        
        # Get column schemas for both databases
        local_columns = get_table_columns(local_engine, table_name)
        railway_columns = get_table_columns(railway_engine, table_name)
        
        logger.info(f"📋 Local columns: {local_columns}")
        logger.info(f"📋 Railway columns: {railway_columns}")
        
        # Find common columns
        common_columns = [col for col in local_columns if col in railway_columns]
        logger.info(f"🔗 Common columns: {common_columns}")
        
        if not common_columns:
            logger.error(f"❌ No common columns found between local and Railway {table_name}")
            return False
        
        # Get total count
        with local_engine.connect() as conn:
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            total_rows = count_result.fetchone()[0]
        
        if total_rows == 0:
            logger.info(f"⚠️ No data in {table_name} to migrate")
            return True
        
        logger.info(f"📊 Migrating {total_rows:,} rows from {table_name}")
        
        # Read and migrate in chunks
        migrated_rows = 0
        
        for chunk_start in range(0, total_rows, chunk_size):
            # Read chunk from local with only common columns
            columns_str = ", ".join(common_columns)
            chunk_query = f"SELECT {columns_str} FROM {table_name} LIMIT {chunk_size} OFFSET {chunk_start}"
            chunk_df = pd.read_sql_query(chunk_query, local_engine)
            
            if chunk_df.empty:
                break
            
            # Write chunk to Railway
            chunk_df.to_sql(table_name, railway_engine, if_exists='append', index=False)
            migrated_rows += len(chunk_df)
            
            logger.info(f"   📈 Migrated {migrated_rows:,}/{total_rows:,} rows ({migrated_rows/total_rows*100:.1f}%)")
        
        logger.info(f"✅ {table_name} migration completed: {migrated_rows:,} rows")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error migrating {table_name}: {e}")
        return False

def verify_migration(railway_engine):
    """Verify the migrated data in Railway"""
    
    try:
        with railway_engine.connect() as conn:
            logger.info("🔍 Verifying migrated data...")
            
            for table in ['floats', 'profiles', 'measurements']:
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.fetchone()[0]
                logger.info(f"✅ Railway {table}: {count:,} records")
            
            # Test a sample query
            sample_query = """
            SELECT COUNT(*) as total_measurements,
                   COUNT(DISTINCT float_id) as unique_floats,
                   MIN(time) as earliest_date,
                   MAX(time) as latest_date,
                   AVG(temperature) as avg_temp
            FROM measurements 
            WHERE temperature IS NOT NULL;
            """
            
            result_df = pd.read_sql_query(sample_query, conn)
            
            if not result_df.empty:
                row = result_df.iloc[0]
                logger.info("📊 Migration verification:")
                logger.info(f"   • Total measurements: {row['total_measurements']:,}")
                logger.info(f"   • Unique floats: {row['unique_floats']:,}")
                logger.info(f"   • Date range: {row['earliest_date']} to {row['latest_date']}")
                logger.info(f"   • Average temperature: {row['avg_temp']:.2f}°C")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")
        return False

def main():
    """Main migration process"""
    
    logger.info("🚀 Starting ARGO data migration to Railway...")
    
    # Step 1: Check local data
    logger.info("\n📋 Step 1: Checking local data...")
    if not check_local_data():
        logger.error("❌ Local data check failed. Please ensure your ARGO data is processed locally first.")
        return False
    
    # Step 2: Connect to Railway
    logger.info("\n🔗 Step 2: Connecting to Railway PostgreSQL...")
    railway_engine = get_railway_engine()
    if not railway_engine:
        logger.error("❌ Could not connect to Railway PostgreSQL")
        logger.info("💡 Instructions:")
        logger.info("   1. Add PostgreSQL to your Railway project")
        logger.info("   2. Copy the DATABASE_URL from Railway dashboard")
        logger.info("   3. Set environment variable: RAILWAY_DATABASE_URL=<your_database_url>")
        return False
    
    # Test Railway connection
    try:
        with railway_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Railway PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"❌ Railway connection failed: {e}")
        return False
    
    # Step 3: Create Railway tables
    logger.info("\n🏗️ Step 3: Creating Railway tables...")
    if not create_railway_tables(railway_engine):
        return False
    
    # Step 4: Migrate data
    logger.info("\n📦 Step 4: Migrating data...")
    local_engine = get_local_engine()
    
    # Migrate in order (floats first, then profiles, then measurements)
    migration_order = ['floats', 'profiles', 'measurements']
    
    for table in migration_order:
        if not migrate_table_data(local_engine, railway_engine, table):
            logger.error(f"❌ Migration failed at table: {table}")
            return False
    
    # Step 5: Verify migration
    logger.info("\n✅ Step 5: Verifying migration...")
    if not verify_migration(railway_engine):
        return False
    
    logger.info("\n🎉 Migration completed successfully!")
    logger.info("🔗 Your Railway API now has access to real ARGO data")
    logger.info("📊 Next: Test your API endpoints with real data")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)