"""
Check what years of data are available in the ARGO dataset
"""

from sqlalchemy import create_engine, text
import config
import pandas as pd

def check_available_years():
    print('🔍 Checking available years in your ARGO dataset...')
    print('=' * 50)
    
    engine = create_engine(config.DATABASE_URL)
    
    # Check what years we have data for
    query = '''
    SELECT 
        EXTRACT(YEAR FROM time) as year,
        COUNT(*) as measurements,
        MIN(time) as earliest_date,
        MAX(time) as latest_date
    FROM measurements 
    GROUP BY EXTRACT(YEAR FROM time)
    ORDER BY year;
    '''
    
    try:
        df = pd.read_sql_query(query, engine)
        
        print('📊 Available data by year:')
        for _, row in df.iterrows():
            year = int(row['year'])
            count = int(row['measurements'])
            earliest = str(row['earliest_date'])
            latest = str(row['latest_date'])
            print(f'  {year}: {count:,} measurements ({earliest} to {latest})')
        
        print()
        print('🌊 Summary:')
        print(f'Total years: {len(df)}')
        total_measurements = df['measurements'].sum()
        print(f'Total measurements: {total_measurements:,}')
        
        # Check months for available years
        print()
        print('📅 Monthly breakdown for available years:')
        
        for year in df['year'].unique():
            year = int(year)
            month_query = f'''
            SELECT 
                EXTRACT(MONTH FROM time) as month,
                COUNT(*) as measurements
            FROM measurements 
            WHERE EXTRACT(YEAR FROM time) = {year}
            GROUP BY EXTRACT(MONTH FROM time)
            ORDER BY month;
            '''
            
            month_df = pd.read_sql_query(month_query, engine)
            months = [int(m) for m in month_df['month'].tolist()]
            print(f'  {year}: Months {months}')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_available_years()