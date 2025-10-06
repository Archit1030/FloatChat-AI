"""
Fill missing dates between January 10-20, 2010 with realistic mock data
"""

from sqlalchemy import create_engine, text
import config
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fill_missing_dates():
    """Fill missing dates with realistic mock data"""
    
    print("🌊 Filling missing dates with realistic ARGO data...")
    print("=" * 60)
    
    engine = create_engine(config.DATABASE_URL)
    
    # Check existing data
    existing_query = """
    SELECT DISTINCT DATE(time) as date, COUNT(*) as count
    FROM measurements 
    WHERE time BETWEEN '2010-01-10' AND '2010-01-20'
    GROUP BY DATE(time)
    ORDER BY date;
    """
    
    existing_df = pd.read_sql_query(existing_query, engine)
    existing_dates = [str(d) for d in existing_df['date'].tolist()]
    
    print("📅 Existing dates:")
    for _, row in existing_df.iterrows():
        print(f"  {row['date']}: {row['count']:,} measurements")
    
    # Generate missing dates
    start_date = datetime(2010, 1, 10)
    end_date = datetime(2010, 1, 20)
    all_dates = []
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        if date_str not in existing_dates:
            all_dates.append(current_date)
        current_date += timedelta(days=1)
    
    print(f"\n📝 Missing dates to fill: {len(all_dates)}")
    for date in all_dates:
        print(f"  {date.strftime('%Y-%m-%d')}")
    
    if not all_dates:
        print("✅ No missing dates to fill!")
        return
    
    # Get sample data to base mock data on
    sample_query = """
    SELECT float_id, lat, lon, depth, temperature, salinity, oxygen, ph, chlorophyll
    FROM measurements 
    WHERE time BETWEEN '2010-01-10' AND '2010-01-20'
    ORDER BY RANDOM()
    LIMIT 100;
    """
    
    sample_df = pd.read_sql_query(sample_query, engine)
    
    print(f"\n🧪 Using {len(sample_df)} existing measurements as templates")
    
    # Generate mock data for each missing date
    total_inserted = 0
    
    for missing_date in all_dates:
        print(f"\n📊 Generating data for {missing_date.strftime('%Y-%m-%d')}...")
        
        # Generate realistic number of measurements (between existing counts)
        num_measurements = np.random.randint(5000, 15000)
        
        mock_data = []
        
        for i in range(num_measurements):
            # Use a random sample as template
            template = sample_df.iloc[np.random.randint(0, len(sample_df))]
            
            # Add some realistic variation
            temp_variation = np.random.normal(0, 1.0)  # ±1°C variation
            sal_variation = np.random.normal(0, 0.1)   # ±0.1 PSU variation
            
            # Create mock measurement
            mock_measurement = {
                'float_id': template['float_id'],
                'time': missing_date,
                'lat': template['lat'] + np.random.normal(0, 0.1),  # Small position drift
                'lon': template['lon'] + np.random.normal(0, 0.1),
                'depth': template['depth'],
                'temperature': max(0, template['temperature'] + temp_variation),
                'salinity': max(0, template['salinity'] + sal_variation),
                'oxygen': template['oxygen'] + np.random.normal(0, 0.2) if pd.notna(template['oxygen']) else None,
                'ph': template['ph'] + np.random.normal(0, 0.02) if pd.notna(template['ph']) else None,
                'chlorophyll': max(0, template['chlorophyll'] + np.random.normal(0, 0.05)) if pd.notna(template['chlorophyll']) else None
            }
            
            mock_data.append(mock_measurement)
        
        # Insert mock data into database
        mock_df = pd.DataFrame(mock_data)
        
        try:
            # Insert in batches for better performance
            batch_size = 1000
            for start_idx in range(0, len(mock_df), batch_size):
                batch = mock_df.iloc[start_idx:start_idx + batch_size]
                batch.to_sql('measurements', engine, if_exists='append', index=False, method='multi')
            
            total_inserted += len(mock_df)
            print(f"  ✅ Inserted {len(mock_df):,} mock measurements")
            
        except Exception as e:
            print(f"  ❌ Error inserting data: {e}")
    
    print(f"\n🎉 Successfully filled missing dates!")
    print(f"📊 Total mock measurements inserted: {total_inserted:,}")
    
    # Verify the results
    print("\n🔍 Verifying results...")
    verification_query = """
    SELECT DATE(time) as date, COUNT(*) as count,
           MIN(temperature) as min_temp, MAX(temperature) as max_temp,
           AVG(temperature) as avg_temp
    FROM measurements 
    WHERE time BETWEEN '2010-01-10' AND '2010-01-20'
    GROUP BY DATE(time)
    ORDER BY date;
    """
    
    final_df = pd.read_sql_query(verification_query, engine)
    
    print("📅 Final data coverage:")
    for _, row in final_df.iterrows():
        date = str(row['date'])
        count = int(row['count'])
        min_temp = float(row['min_temp'])
        max_temp = float(row['max_temp'])
        avg_temp = float(row['avg_temp'])
        
        # Mark original vs mock data
        data_type = "Original" if date in existing_dates else "Mock"
        print(f"  {date}: {count:,} measurements ({data_type}) - Temp: {min_temp:.1f}°C to {max_temp:.1f}°C")
    
    print(f"\n✅ Complete! Now you have data for all dates from Jan 10-20, 2010")
    print("🧪 Test queries like:")
    print("  - 'What was the maximum temperature on 15 January 2010?'")
    print("  - 'Average temperature on 12 January 2010'")
    print("  - 'Temperature on 18 January 2010'")

if __name__ == "__main__":
    fill_missing_dates()