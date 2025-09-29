import pandas as pd
from sqlalchemy import create_engine
import config

engine = create_engine(config.DATABASE_URL)

print("Testing DB counts:")
print("Measurements:", pd.read_sql('SELECT COUNT(*) FROM measurements', engine).iloc[0,0])
print("Floats:", pd.read_sql('SELECT COUNT(*) FROM floats', engine).iloc[0,0])
print("Profiles:", pd.read_sql('SELECT COUNT(*) FROM profiles', engine).iloc[0,0])
