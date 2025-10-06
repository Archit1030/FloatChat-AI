"""
Add mock data for missing dates between Jan 10-20, 2010
"""

from sqlalchemy import create_engine, text
import config
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def add_mock_dates():
    engine = create_engine(config.DATABASE_URL)
    
    print("🌊 Adding mock data for missing dates...")
    
    # Get existing dates
    existing_query = """
    SELECT DISTINCT DATE(time) as date
    FROM measurements 
    WHERE time BETWEEN '2010-01-10' AND '2010-01-20'
    ORDER BY date;
    """
    
    existing_df = pd.read_sql_query(existing_query, engine)
    existing_dates = [str(d) for d in existing_df['date'].tolist()]
    
    print(f"Existing dates: {existing_dates}")
    
    # Generate missing dates
    all_dates = []
    for day in range(10, 21):  # Jan 10 to Jan 20
        date_str = f"2010-01-{day:02d}"
        if date_str not in existing_dates:
            all_dates.append(date_str)
    
    print(f"Missing dates to fill: {all_dates}")
    
    if not all_dates:
        print("No missing dates!")
        return
    
    # Get sample data for templates
    sample_query = """
    SELECT float_id, lat, lon, depth, temperature, salinity
    FROM measurements 
    WHERE DATE(time) = '2010-01-10'
    LIMIT 50;
    """
    
    sample_df = pd.read_sql_query(sample_query, engine)
    print(f"Using {len(sample_df)} sample measurements as templates")
    
    # Add mock data for each missing date
    for date_str in all_dates:
        print(f"Adding data for {date_str}...")
        
        mock_data = []
        num_measurements = 8000  # Reasonable number
        
        for i in range(num_measurements):
            # Use random sample as template
            template_idx = np.random.randint(0, len(sample_df))
            template = sample_df.iloc[template_idx]
            
            # Add realistic variations
            temp_var = np.random.normal(0, 0.8)
            sal_var = np.random.normal(0, 0.05)
            
            mock_data.append({
                'float_id': template['float_id'],
                'time': f"{date_str} 00:00:00",
                'lat': template['lat'] + np.random.normal(0, 0.05),
                'lon': template['lon'] + np.random.normal(0, 0.05),
                'depth': template['depth'],
                'temperature': max(1.0, template['temperature'] + temp_var),
                'salinity': max(30.0, template['salinity'] + sal_var),
                'pressure': template['depth'] * 1.025,
                'oxygen': None,
                'ph': None,
                'chlorophyll': None,
                'quality_flag': 1
            })
        
        # Insert in batches
        mock_df = pd.DataFrame(mock_data)
        
        try:
            mock_df.to_sql('measurements', engine, if_exists='append', index=False, method='multi')
            print(f"  ✅ Added {len(mock_df):,} measurements for {date_str}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("🎉 Mock data generation complete!")
    
    # Verify results
    verify_query = """
    SELECT DATE(time) as date, COUNT(*) as count, 
           MIN(temperature) as min_temp, MAX(temperature) as max_temp
    FROM measurements 
    WHERE time BETWEEN '2010-01-10' AND '2010-01-20'
    GROUP BY DATE(time)
    ORDER BY date;
    """
    
    result_df = pd.read_sql_query(verify_query, engine)
    
    print("\n📊 Final coverage:")
    for _, row in result_df.iterrows():
        date = str(row['date'])
        count = int(row['count'])
        min_temp = float(row['min_temp'])
        max_temp = float(row['max_temp'])
        print(f"  {date}: {count:,} measurements, {min_temp:.1f}°C to {max_temp:.1f}°C")

if __name__ == "__main__":
    add_mock_dates()