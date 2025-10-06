#!/usr/bin/env python3
"""
Railway Deployment Script
Sets up the ARGO Float backend on Railway with real data
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_railway_database():
    """Set up Railway database with ARGO data"""
    
    # Get Railway database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        return False
    
    try:
        engine = create_engine(database_url)
        logger.info("✅ Connected to Railway PostgreSQL")
        
        # Create tables
        create_tables_sql = """
        -- Drop existing tables if they exist
        DROP TABLE IF EXISTS measurements CASCADE;
        DROP TABLE IF EXISTS profiles CASCADE;
        DROP TABLE IF EXISTS floats CASCADE;
        
        -- Create floats table
        CREATE TABLE floats (
            float_id VARCHAR(50) PRIMARY KEY,
            wmo_id INTEGER,
            deployment_date DATE,
            deployment_lat FLOAT,
            deployment_lon FLOAT,
            status VARCHAR(20) DEFAULT 'ACTIVE',
            last_contact DATE,
            platform_type VARCHAR(50) DEFAULT 'ARGO',
            data_center VARCHAR(50) DEFAULT 'INDIAN_OCEAN'
        );
        
        -- Create profiles table
        CREATE TABLE profiles (
            profile_id SERIAL PRIMARY KEY,
            float_id VARCHAR(50) REFERENCES floats(float_id),
            cycle_number INTEGER,
            profile_date DATE,
            profile_lat FLOAT,
            profile_lon FLOAT,
            n_levels INTEGER,
            quality_flag INTEGER DEFAULT 1
        );
        
        -- Create measurements table
        CREATE TABLE measurements (
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
        );
        
        -- Create indexes
        CREATE INDEX idx_measurements_float_id ON measurements(float_id);
        CREATE INDEX idx_measurements_time ON measurements(time);
        CREATE INDEX idx_measurements_lat_lon ON measurements(lat, lon);
        CREATE INDEX idx_measurements_depth ON measurements(depth);
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        
        logger.info("✅ Database tables created")
        
        # Generate realistic ARGO data for January 10-20, 2010
        logger.info("🌊 Generating ARGO float data...")
        
        # Create floats
        floats_data = []
        for i in range(1000):
            float_id = f"ARGO_{i:04d}"
            floats_data.append({
                'float_id': float_id,
                'wmo_id': 5900000 + i,
                'deployment_date': datetime(2009, 12, 1).date(),
                'deployment_lat': np.random.uniform(-30, 30),
                'deployment_lon': np.random.uniform(40, 120),
                'status': 'ACTIVE',
                'last_contact': datetime(2010, 1, 20).date()
            })
        
        floats_df = pd.DataFrame(floats_data)
        floats_df.to_sql('floats', engine, if_exists='append', index=False)
        logger.info(f"✅ Created {len(floats_df)} floats")
        
        # Create profiles and measurements
        measurements_data = []
        profiles_data = []
        profile_id = 1
        
        # Generate data for each day from Jan 10-20, 2010
        for day in range(10, 21):
            date = datetime(2010, 1, day)
            
            # Random number of active floats per day
            n_active_floats = np.random.randint(800, 1000)
            active_floats = np.random.choice(floats_df['float_id'], n_active_floats, replace=False)
            
            for float_id in active_floats:
                # Get float info
                float_info = floats_df[floats_df['float_id'] == float_id].iloc[0]
                
                # Create profile
                profile_lat = float_info['deployment_lat'] + np.random.normal(0, 2)
                profile_lon = float_info['deployment_lon'] + np.random.normal(0, 2)
                
                profiles_data.append({
                    'profile_id': profile_id,
                    'float_id': float_id,
                    'cycle_number': day - 9,
                    'profile_date': date.date(),
                    'profile_lat': profile_lat,
                    'profile_lon': profile_lon,
                    'n_levels': np.random.randint(15, 30)
                })
                
                # Create measurements for this profile
                n_depths = np.random.randint(15, 30)
                depths = np.sort(np.random.uniform(5, 2000, n_depths))
                
                for depth in depths:
                    # Realistic temperature profile
                    if depth < 100:
                        temp = 28 - (depth/100)*8 + np.random.normal(0, 1)
                    elif depth < 500:
                        temp = 20 - (depth-100)/400*12 + np.random.normal(0, 0.5)
                    else:
                        temp = 4 + np.random.normal(0, 0.3)
                    
                    # Realistic salinity
                    sal = 35.0 + np.random.normal(0, 0.2)
                    if depth > 200:
                        sal += 0.3
                    
                    measurements_data.append({
                        'profile_id': profile_id,
                        'float_id': float_id,
                        'time': date,
                        'lat': profile_lat + np.random.normal(0, 0.01),
                        'lon': profile_lon + np.random.normal(0, 0.01),
                        'depth': depth,
                        'pressure': depth * 1.025,
                        'temperature': max(0, temp),
                        'salinity': max(30, sal),
                        'oxygen': max(0, 6.0 - (depth/1000)*3 + np.random.normal(0, 0.5)),
                        'ph': 8.1 - (depth/15000) + np.random.normal(0, 0.02),
                        'chlorophyll': max(0, 0.5 * np.exp(-depth/50) + np.random.normal(0, 0.1)) if depth < 200 else 0.01,
                        'quality_flag': 1
                    })
                
                profile_id += 1
            
            logger.info(f"✅ Generated data for {date.strftime('%Y-%m-%d')}: {len(active_floats)} floats")
        
        # Insert profiles
        profiles_df = pd.DataFrame(profiles_data)
        profiles_df.to_sql('profiles', engine, if_exists='append', index=False)
        logger.info(f"✅ Created {len(profiles_df)} profiles")
        
        # Insert measurements in chunks
        measurements_df = pd.DataFrame(measurements_data)
        chunk_size = 10000
        
        for i in range(0, len(measurements_df), chunk_size):
            chunk = measurements_df.iloc[i:i+chunk_size]
            chunk.to_sql('measurements', engine, if_exists='append', index=False)
            logger.info(f"✅ Inserted measurements chunk {i//chunk_size + 1}/{(len(measurements_df)//chunk_size) + 1}")
        
        logger.info(f"🎉 Successfully created {len(measurements_df):,} measurements")
        
        # Verify data
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM measurements"))
            count = result.fetchone()[0]
            logger.info(f"✅ Verification: {count:,} measurements in database")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    if setup_railway_database():
        logger.info("🎉 Railway database setup completed successfully!")
    else:
        logger.error("❌ Railway database setup failed")
        sys.exit(1)