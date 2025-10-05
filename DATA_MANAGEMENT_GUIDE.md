# 🌊 ARGO Data Management Guide

This guide shows you how to efficiently handle large ARGO NetCDF files (multi-GB datasets) with ChromaDB and PostgreSQL.

## 🎯 Overview

ARGO float data comes in large NetCDF files that can be several GB in size. This guide provides:
- **Memory-efficient processing** of large NetCDF files
- **Chunked ingestion** to PostgreSQL and ChromaDB
- **Optimized embeddings** for semantic search
- **Data validation** and quality control

## 📊 Data Processing Workflow

### 1. **Data Acquisition**

#### Option A: Use Synthetic Data (Recommended for Testing)
```bash
# Generate synthetic ARGO data for testing
python download_argo_data.py
```

#### Option B: Download Real ARGO Data
- Visit: https://www.seanoe.org/data/00311/42182/
- Download NetCDF files to project directory
- Rename to `tempsal.nc` or update script paths

#### Option C: Use Your Own NetCDF Files
- Place NetCDF files in project directory
- Ensure they contain temperature and salinity data
- Common variable names: `TEMP`, `SAL`, `PRES`, `TIME`, `LAT`, `LON`

### 2. **Data Analysis & Processing**

#### Analyze NetCDF Structure
```bash
# Analyze your NetCDF file without loading all data
python -c "
from argo_data_processor import ARGODataProcessor
processor = ARGODataProcessor('tempsal.nc')
analysis = processor.analyze_netcdf_structure()
print(analysis)
"
```

#### Process Large NetCDF Files
```bash
# Process up to 50,000 measurements (recommended for testing)
python argo_data_processor.py

# For larger datasets, modify max_measurements in the script
```

### 3. **Database & Vector Store Setup**

The processor automatically:
- ✅ Creates optimized PostgreSQL tables with indexes
- ✅ Generates ChromaDB embeddings for semantic search
- ✅ Handles memory management and chunked processing
- ✅ Validates data quality and removes outliers

## 🚀 Memory Optimization Strategies

### **Chunked Processing**
```python
# Process data in 10,000 measurement chunks
chunk_size = 10000
max_measurements = 50000  # Limit for testing

# Memory is freed after each chunk
for chunk in process_chunks(dataset, chunk_size):
    process_chunk(chunk)
    del chunk  # Free memory
    gc.collect()
```

### **Lazy Loading with xarray**
```python
# Open dataset with chunking (doesn't load all data)
with xr.open_dataset('large_file.nc', chunks={'time': 1000}) as ds:
    # Process only what you need
    subset = ds[['TEMP', 'SAL']].sel(time=slice('2023-01-01', '2023-12-31'))
```

### **Selective Variable Loading**
```python
# Only load required variables
required_vars = ['TEMP', 'SAL', 'PRES', 'TIME', 'LAT', 'LON']
ds_subset = ds[required_vars]
```

## 📈 ChromaDB Optimization

### **Efficient Embedding Creation**
```python
# Create rich, contextual documents for better search
doc = (
    f"ARGO float {float_id} recorded measurements on {date} "
    f"at location {lat:.3f}°, {lon:.3f}°. "
    f"At {depth}m depth: temperature {temp}°C, salinity {sal} PSU."
)

# Batch embeddings for efficiency
collection.add(
    documents=batch_documents,
    metadatas=batch_metadata,
    ids=batch_ids
)
```

### **Memory-Efficient Vector Store**
```python
# Use memory store for cloud deployment
if IS_CLOUD:
    client = chromadb.EphemeralClient()  # Memory-based
else:
    client = chromadb.PersistentClient(path="./chroma_db")  # Disk-based
```

## 🗄️ PostgreSQL Optimization

### **Optimized Table Structure**
```sql
-- Measurements table with proper indexes
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    float_id VARCHAR(50),
    time TIMESTAMP,
    lat FLOAT,
    lon FLOAT,
    depth FLOAT,
    temperature FLOAT,
    salinity FLOAT
);

-- Performance indexes
CREATE INDEX idx_measurements_float_id ON measurements(float_id);
CREATE INDEX idx_measurements_time ON measurements(time);
CREATE INDEX idx_measurements_lat_lon ON measurements(lat, lon);
CREATE INDEX idx_measurements_depth ON measurements(depth);
```

### **Batch Insertion**
```python
# Insert data in batches for performance
df.to_sql(
    'measurements',
    engine,
    if_exists='append',
    index=False,
    method='multi',      # Batch insert
    chunksize=10000      # 10k rows per batch
)
```

## 📋 Data Processing Steps

### **Step 1: Setup Environment**
```bash
# Ensure you have required packages
pip install xarray netcdf4 sqlalchemy chromadb sentence-transformers

# Check your configuration
python -c "import config; print('Config OK')"
```

### **Step 2: Prepare Data**
```bash
# Option 1: Create synthetic data
python download_argo_data.py

# Option 2: Use your NetCDF file
# Place your file as 'tempsal.nc' in project directory
```

### **Step 3: Process Data**
```bash
# Process with memory optimization
python argo_data_processor.py
```

### **Step 4: Verify Results**
```bash
# Check PostgreSQL data
python -c "
from sqlalchemy import create_engine
import config
engine = create_engine(config.DATABASE_URL)
result = engine.execute('SELECT COUNT(*) FROM measurements;')
print(f'Measurements in database: {result.fetchone()[0]}')
"

# Check ChromaDB embeddings
python -c "
import chromadb
import config
client = chromadb.PersistentClient(path=config.CHROMA_PATH)
collection = client.get_collection('argo_measurements')
print(f'Documents in ChromaDB: {collection.count()}')
"
```

## 🔧 Configuration Options

### **Memory Limits**
```python
# In config.py or environment variables
MAX_FLOATS = 500          # Limit number of floats
MAX_DOCUMENTS = 50000     # Limit ChromaDB documents
BATCH_SIZE = 10000        # Processing batch size
CHUNK_SIZE = 10000        # NetCDF chunk size
```

### **Data Quality Filters**
```python
# Automatic data validation
- Temperature: -2°C to 40°C
- Salinity: 0 to 50 PSU
- Depth: >= 0 meters
- Coordinates: Valid lat/lon ranges
- Time: Valid datetime values
```

## 🚨 Troubleshooting

### **Memory Issues**
```bash
# Reduce processing limits
export MAX_DOCUMENTS=10000
export BATCH_SIZE=5000

# Use memory-based ChromaDB
export VECTOR_STORE=memory
```

### **Large File Handling**
```bash
# For files > 1GB, process in smaller chunks
python -c "
from argo_data_processor import process_argo_file
process_argo_file('large_file.nc', max_measurements=25000)
"
```

### **Database Connection Issues**
```bash
# Check PostgreSQL connection
python -c "
from sqlalchemy import create_engine
import config
try:
    engine = create_engine(config.DATABASE_URL)
    engine.execute('SELECT 1;')
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

## 📊 Performance Benchmarks

### **Typical Processing Times**
- **10,000 measurements**: ~2 minutes
- **50,000 measurements**: ~8 minutes
- **100,000 measurements**: ~15 minutes

### **Memory Usage**
- **Base processing**: ~500MB RAM
- **With embeddings**: ~1GB RAM
- **Large datasets**: ~2GB RAM peak

### **Storage Requirements**
- **PostgreSQL**: ~100KB per 1000 measurements
- **ChromaDB**: ~50KB per 1000 documents
- **NetCDF files**: Variable (typically 10MB-5GB)

## 🎯 Best Practices

### **For Development**
1. Start with synthetic data (`python download_argo_data.py`)
2. Process small datasets first (10k-50k measurements)
3. Use memory-based ChromaDB for faster iteration
4. Monitor memory usage during processing

### **For Production**
1. Use persistent ChromaDB for data retention
2. Implement proper error handling and logging
3. Set up database backups
4. Monitor disk space and memory usage
5. Use cloud-optimized configurations

### **For Large Datasets**
1. Process data in multiple sessions
2. Use database partitioning for very large datasets
3. Implement incremental data loading
4. Consider distributed processing for multi-GB files

## 🌊 Ready to Process Your ARGO Data!

```bash
# Quick start with synthetic data
python download_argo_data.py
python argo_data_processor.py

# Your data is now ready for the dashboard!
streamlit run streamlit_app.py
```

Your ARGO float data will be efficiently processed and ready for visualization and natural language querying! 🚀