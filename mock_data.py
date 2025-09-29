"""
Mock data generator for testing the ARGO Float Dashboard
Creates sample floats, profiles, and measurements for demonstration
"""

from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config

engine = create_engine(config.DATABASE_URL)

def create_argo_tables():
    """Create ARGO database schema"""

    create_tables_sql = """
    -- Drop existing tables if they exist
    DROP TABLE IF EXISTS measurements CASCADE;
    DROP TABLE IF EXISTS profiles CASCADE;
    DROP TABLE IF EXISTS floats CASCADE;

    -- Create floats table
    CREATE TABLE floats (
        float_id VARCHAR(20) PRIMARY KEY,
        wmo_id INTEGER,
        deployment_date DATE,
        deployment_lat FLOAT,
        deployment_lon FLOAT,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        last_contact DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create profiles table
    CREATE TABLE profiles (
        profile_id SERIAL PRIMARY KEY,
        float_id VARCHAR(20) REFERENCES floats(float_id),
        cycle_number INTEGER,
        profile_date TIMESTAMP,
        profile_lat FLOAT,
        profile_lon FLOAT,
        n_levels INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create measurements table
    CREATE TABLE measurements (
        id SERIAL PRIMARY KEY,
        profile_id INTEGER REFERENCES profiles(profile_id),
        float_id VARCHAR(20) REFERENCES floats(float_id),
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes
    CREATE INDEX idx_measurements_float_id ON measurements(float_id);
    CREATE INDEX idx_measurements_time ON measurements(time);
    CREATE INDEX idx_measurements_location ON measurements(lat, lon);
    CREATE INDEX idx_measurements_depth ON measurements(depth);
    CREATE INDEX idx_profiles_float_id ON profiles(float_id);
    CREATE INDEX idx_profiles_date ON profiles(profile_date);
    """

    with engine.connect() as conn:
        for statement in create_tables_sql.split(';'):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()

    print("✅ ARGO database schema created!")

def generate_mock_data():
    """Generate realistic mock ARGO float data"""

    # Create 3 floats in Indian Ocean region
    floats = [
        {
            'float_id': 'ARGO_0001',
            'wmo_id': 5900001,
            'deployment_date': datetime(2023, 1, 15).date(),
            'deployment_lat': 10.5,
            'deployment_lon': 75.2,
            'status': 'ACTIVE',
            'last_contact': datetime(2024, 9, 1).date()
        },
        {
            'float_id': 'ARGO_0002',
            'wmo_id': 5900002,
            'deployment_date': datetime(2023, 3, 20).date(),
            'deployment_lat': -5.8,
            'deployment_lon': 80.1,
            'status': 'ACTIVE',
            'last_contact': datetime(2024, 9, 1).date()
        },
        {
            'float_id': 'ARGO_0003',
            'wmo_id': 5900003,
            'deployment_date': datetime(2023, 5, 10).date(),
            'deployment_lat': 15.2,
            'deployment_lon': 70.5,
            'status': 'ACTIVE',
            'last_contact': datetime(2024, 9, 1).date()
        }
    ]

    profiles = []
    measurements = []

    profile_id_counter = 1

    for float_info in floats:
        float_id = float_info['float_id']
        base_lat = float_info['deployment_lat']
        base_lon = float_info['deployment_lon']

        # Create 10 profiles per float (monthly)
        for cycle in range(1, 11):
            profile_date = float_info['deployment_date'] + timedelta(days=cycle*30)
            # Slight drift in position
            lat_offset = np.random.normal(0, 0.5)
            lon_offset = np.random.normal(0, 0.5)

            profile = {
                'profile_id': profile_id_counter,
                'float_id': float_id,
                'cycle_number': cycle,
                'profile_date': profile_date,
                'profile_lat': base_lat + lat_offset,
                'profile_lon': base_lon + lon_offset,
                'n_levels': 20  # 20 depth levels
            }
            profiles.append(profile)

            # Generate measurements for this profile
            depths = np.linspace(5, 1000, 20)  # 5m to 1000m

            for depth in depths:
                # Temperature profile (realistic ocean)
                if depth < 100:
                    temp = 28 - (depth/100)*8 + np.random.normal(0, 0.5)  # Surface warm
                elif depth < 500:
                    temp = 20 - (depth-100)/400*10 + np.random.normal(0, 0.3)  # Thermocline
                else:
                    temp = 4 + np.random.normal(0, 0.2)  # Deep cold

                # Salinity profile
                sal = 35.0 + np.random.normal(0, 0.1)
                if depth > 200:
                    sal += 0.2  # Slightly saltier deep water

                # BGC parameters
                oxygen = 6.0 - (depth/1000)*3 + np.random.normal(0, 0.5)
                ph = 8.1 - (depth/15000) + np.random.normal(0, 0.02)
                chlorophyll = 0.5 * np.exp(-depth/50) + np.random.normal(0, 0.1) if depth < 200 else 0.01

                measurement = {
                    'profile_id': profile_id_counter,
                    'float_id': float_id,
                    'time': profile_date,
                    'lat': profile['profile_lat'],
                    'lon': profile['profile_lon'],
                    'depth': depth,
                    'pressure': depth * 1.025,
                    'temperature': max(0, temp),
                    'salinity': sal,
                    'oxygen': max(0, oxygen),
                    'ph': ph,
                    'chlorophyll': max(0, chlorophyll)
                }
                measurements.append(measurement)

            profile_id_counter += 1

    return pd.DataFrame(floats), pd.DataFrame(profiles), pd.DataFrame(measurements)

def insert_mock_data():
    """Insert mock data into database"""

    print("🌊 Generating mock ARGO float data...")

    # Create schema
    create_argo_tables()

    # Generate data
    floats_df, profiles_df, measurements_df = generate_mock_data()

    print(f"Generated {len(floats_df)} floats, {len(profiles_df)} profiles, {len(measurements_df)} measurements")

    # Insert data
    floats_df.to_sql('floats', engine, if_exists='append', index=False)
    print("✅ Inserted floats")

    profiles_df.to_sql('profiles', engine, if_exists='append', index=False)
    print("✅ Inserted profiles")

    # Insert measurements in batches
    batch_size = 1000
    for i in range(0, len(measurements_df), batch_size):
        batch = measurements_df.iloc[i:i+batch_size]
        batch.to_sql('measurements', engine, if_exists='append', index=False)
        print(f"✅ Inserted measurements batch {i//batch_size + 1}")

    print("🎉 Mock data insertion completed!")

if __name__ == "__main__":
    # DEPRECATED: Use argo_float_processor.py for real data ingestion from tempsal.nc
    # insert_mock_data()
    print("Mock data generation is deprecated. Use argo_float_processor.py to ingest real data from tempsal.nc")
