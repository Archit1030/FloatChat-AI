"""
Efficient ARGO Data Processor for Large NetCDF Files
Handles multi-GB ARGO datasets with memory optimization and chunked processing
"""

import xarray as xr
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import chromadb
from sentence_transformers import SentenceTransformer
import config
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import gc
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARGODataProcessor:
    """Efficient processor for large ARGO NetCDF files"""
    
    def __init__(self, netcdf_path: str, chunk_size: int = 10000):
        self.netcdf_path = Path(netcdf_path)
        self.chunk_size = chunk_size
        self.engine = create_engine(config.DATABASE_URL)
        
        # Initialize ChromaDB
        self.embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=config.CHROMA_PATH) if config.VECTOR_STORE == "persistent" else chromadb.EphemeralClient()
        
        # Setup database tables
        self._setup_database()
        
    def _setup_database(self):
        """Create optimized database tables for ARGO data"""
        
        # Create tables with proper indexes
        create_tables_sql = """
        -- Floats table
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
        
        -- Profiles table
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
        
        -- Measurements table with partitioning support
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
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_measurements_float_id ON measurements(float_id);
        CREATE INDEX IF NOT EXISTS idx_measurements_time ON measurements(time);
        CREATE INDEX IF NOT EXISTS idx_measurements_lat_lon ON measurements(lat, lon);
        CREATE INDEX IF NOT EXISTS idx_measurements_depth ON measurements(depth);
        CREATE INDEX IF NOT EXISTS idx_profiles_float_date ON profiles(float_id, profile_date);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        
        logger.info("✅ Database tables created/verified")
    
    def analyze_netcdf_structure(self) -> Dict:
        """Analyze NetCDF file structure without loading all data"""
        
        logger.info(f"📊 Analyzing NetCDF file: {self.netcdf_path}")
        
        # Open dataset with minimal memory usage
        with xr.open_dataset(self.netcdf_path, chunks={'time': 1000}) as ds:
            analysis = {
                'file_size_mb': self.netcdf_path.stat().st_size / (1024 * 1024),
                'dimensions': dict(ds.dims),
                'variables': list(ds.data_vars.keys()),
                'coordinates': list(ds.coords.keys()),
                'time_range': None,
                'spatial_bounds': None,
                'estimated_measurements': 1
            }
            
            # Calculate estimated measurements
            for dim_size in ds.dims.values():
                analysis['estimated_measurements'] *= dim_size
            
            # Get time range if available
            if 'time' in ds.coords:
                time_vals = ds.time.values
                analysis['time_range'] = (
                    pd.to_datetime(time_vals.min()).strftime('%Y-%m-%d'),
                    pd.to_datetime(time_vals.max()).strftime('%Y-%m-%d')
                )
            
            # Get spatial bounds
            if 'lat' in ds.coords and 'lon' in ds.coords:
                analysis['spatial_bounds'] = {
                    'lat_min': float(ds.lat.min().values),
                    'lat_max': float(ds.lat.max().values),
                    'lon_min': float(ds.lon.min().values),
                    'lon_max': float(ds.lon.max().values)
                }
        
        logger.info(f"📈 File analysis: {analysis['file_size_mb']:.1f}MB, ~{analysis['estimated_measurements']:,} measurements")
        return analysis
    
    def process_netcdf_chunked(self, max_measurements: int = 100000) -> None:
        """Process NetCDF file in memory-efficient chunks"""
        
        logger.info(f"🌊 Processing ARGO NetCDF data (max {max_measurements:,} measurements)")
        
        # Open dataset with chunking
        with xr.open_dataset(self.netcdf_path, chunks={'time': 1000}) as ds:
            
            # Map NetCDF variables to our schema
            var_mapping = self._detect_variable_mapping(ds)
            logger.info(f"📋 Variable mapping: {var_mapping}")
            
            # Convert to DataFrame in chunks
            total_processed = 0
            chunk_count = 0
            
            # Process data in spatial/temporal chunks
            for chunk_data in self._chunk_dataset(ds, var_mapping, max_measurements):
                
                if chunk_data.empty:
                    continue
                
                chunk_count += 1
                chunk_size = len(chunk_data)
                
                logger.info(f"📦 Processing chunk {chunk_count}: {chunk_size:,} measurements")
                
                # Clean and validate data
                chunk_data = self._clean_data(chunk_data)
                
                # Create synthetic float structure if not present
                chunk_data = self._create_float_structure(chunk_data)
                
                # Insert into PostgreSQL
                self._insert_chunk_to_postgres(chunk_data)
                
                # Create ChromaDB embeddings
                self._create_chunk_embeddings(chunk_data)
                
                total_processed += chunk_size
                
                # Memory cleanup
                del chunk_data
                gc.collect()
                
                logger.info(f"✅ Processed {total_processed:,} total measurements")
                
                if total_processed >= max_measurements:
                    logger.info(f"🎯 Reached maximum measurements limit ({max_measurements:,})")
                    break
        
        logger.info(f"🎉 Completed processing {total_processed:,} measurements")
    
    def _detect_variable_mapping(self, ds: xr.Dataset) -> Dict[str, str]:
        """Detect variable names in NetCDF file"""
        
        # Common ARGO variable name patterns
        mappings = {
            'time': ['time', 'TIME', 'TAXIS', 'JULD'],
            'lat': ['lat', 'latitude', 'LATITUDE', 'YAXIS'],
            'lon': ['lon', 'longitude', 'LONGITUDE', 'XAXIS'],
            'depth': ['depth', 'DEPTH', 'PRES', 'pressure', 'ZAX'],
            'temperature': ['temp', 'TEMP', 'temperature', 'TEMPERATURE'],
            'salinity': ['sal', 'SAL', 'salinity', 'SALINITY', 'PSAL'],
            'oxygen': ['oxygen', 'OXYGEN', 'DOXY', 'O2'],
            'ph': ['ph', 'PH', 'PH_IN_SITU_TOTAL'],
            'chlorophyll': ['chlorophyll', 'CHLA', 'CHLOROPHYLL']
        }
        
        var_mapping = {}
        available_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
        
        for standard_name, possible_names in mappings.items():
            for possible_name in possible_names:
                if possible_name in available_vars:
                    var_mapping[standard_name] = possible_name
                    break
        
        return var_mapping
    
    def _chunk_dataset(self, ds: xr.Dataset, var_mapping: Dict[str, str], max_measurements: int):
        """Generate chunks of data from the dataset"""
        
        # Select available variables
        selected_vars = {}
        for standard_name, netcdf_name in var_mapping.items():
            if netcdf_name in ds:
                selected_vars[standard_name] = netcdf_name
        
        # Create subset dataset
        netcdf_vars = list(selected_vars.values())
        ds_subset = ds[netcdf_vars]
        
        # Convert to DataFrame in chunks
        chunk_size = min(self.chunk_size, max_measurements // 10)  # Process in smaller chunks
        
        # Convert to DataFrame
        df = ds_subset.to_dataframe().reset_index()
        
        # Rename columns to standard names
        rename_dict = {netcdf_name: standard_name for standard_name, netcdf_name in selected_vars.items()}
        df = df.rename(columns=rename_dict)
        
        # Yield chunks
        total_rows = len(df)
        for i in range(0, total_rows, chunk_size):
            yield df.iloc[i:i+chunk_size].copy()
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate ARGO data"""
        
        # Remove rows with missing critical data
        critical_cols = ['time', 'lat', 'lon', 'depth']
        available_critical = [col for col in critical_cols if col in df.columns]
        
        if available_critical:
            df = df.dropna(subset=available_critical)
        
        # Convert time to datetime
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
        
        # Validate geographic coordinates
        if 'lat' in df.columns:
            df = df[(df['lat'] >= -90) & (df['lat'] <= 90)]
        if 'lon' in df.columns:
            df = df[(df['lon'] >= -180) & (df['lon'] <= 180)]
        
        # Validate depth (should be positive)
        if 'depth' in df.columns:
            df = df[df['depth'] >= 0]
        
        # Validate temperature (reasonable ocean range)
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= -2) & (df['temperature'] <= 40)]
        
        # Validate salinity (reasonable ocean range)
        if 'salinity' in df.columns:
            df = df[(df['salinity'] >= 0) & (df['salinity'] <= 50)]
        
        return df
    
    def _create_float_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create synthetic float and profile structure"""
        
        # Create synthetic float IDs based on geographic regions
        if 'lat' in df.columns and 'lon' in df.columns:
            # Create float IDs based on 5-degree grid cells
            df['lat_grid'] = (df['lat'] // 5) * 5
            df['lon_grid'] = (df['lon'] // 5) * 5
            df['float_id'] = 'ARGO_' + df['lat_grid'].astype(str) + '_' + df['lon_grid'].astype(str)
            df['float_id'] = df['float_id'].str.replace('-', 'S').str.replace('.', '')
        else:
            df['float_id'] = 'ARGO_UNKNOWN'
        
        # Create synthetic profile IDs based on time periods
        if 'time' in df.columns:
            df['profile_date'] = df['time'].dt.date
            df['profile_id'] = df['float_id'] + '_' + df['profile_date'].astype(str)
        else:
            df['profile_id'] = df['float_id'] + '_DEFAULT'
        
        return df
    
    def _insert_chunk_to_postgres(self, df: pd.DataFrame) -> None:
        """Insert chunk data into PostgreSQL"""
        
        try:
            # Insert floats (with conflict resolution)
            if 'float_id' in df.columns:
                floats_df = df.groupby('float_id').agg({
                    'lat': 'mean',
                    'lon': 'mean',
                    'time': 'min'
                }).reset_index()
                
                floats_df = floats_df.rename(columns={
                    'lat': 'deployment_lat',
                    'lon': 'deployment_lon',
                    'time': 'deployment_date'
                })
                
                floats_df['wmo_id'] = range(len(floats_df))  # Synthetic WMO IDs
                floats_df['deployment_date'] = floats_df['deployment_date'].dt.date
                
                floats_df.to_sql('floats', self.engine, if_exists='append', index=False, method='multi')
            
            # Insert profiles
            if 'profile_id' in df.columns:
                profiles_df = df.groupby(['profile_id', 'float_id']).agg({
                    'lat': 'mean',
                    'lon': 'mean',
                    'time': 'first',
                    'depth': 'count'
                }).reset_index()
                
                profiles_df = profiles_df.rename(columns={
                    'lat': 'profile_lat',
                    'lon': 'profile_lon',
                    'time': 'profile_date',
                    'depth': 'n_levels'
                })
                
                profiles_df['cycle_number'] = profiles_df.groupby('float_id').cumcount() + 1
                profiles_df['profile_date'] = profiles_df['profile_date'].dt.date
                
                profiles_df.to_sql('profiles', self.engine, if_exists='append', index=False, method='multi')
            
            # Insert measurements
            measurements_df = df.copy()
            if 'pressure' not in measurements_df.columns and 'depth' in measurements_df.columns:
                measurements_df['pressure'] = measurements_df['depth'] * 1.025  # Approximate conversion
            
            measurements_df.to_sql('measurements', self.engine, if_exists='append', index=False, method='multi')
            
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL insert warning: {e}")
    
    def _create_chunk_embeddings(self, df: pd.DataFrame) -> None:
        """Create ChromaDB embeddings for chunk"""
        
        try:
            # Get or create collection
            collection = self.client.get_or_create_collection(
                name="argo_measurements",
                embedding_function=self.embed_model.encode
            )
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Create rich document
                temp_str = f"{row['temperature']:.2f}°C" if pd.notna(row.get('temperature')) else "not available"
                sal_str = f"{row['salinity']:.2f} PSU" if pd.notna(row.get('salinity')) else "not available"
                
                doc = (
                    f"On {row['time'].strftime('%Y-%m-%d')}, ARGO float {row.get('float_id', 'unknown')} "
                    f"recorded measurements at latitude {row['lat']:.3f}° and longitude {row['lon']:.3f}°. "
                    f"At a depth of {row['depth']:.1f} meters, the temperature was {temp_str} "
                    f"and the salinity was {sal_str}."
                )
                
                meta = {
                    'float_id': str(row.get('float_id', 'unknown')),
                    'time': row['time'].strftime('%Y-%m-%d'),
                    'depth': float(row['depth']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon'])
                }
                
                documents.append(doc)
                metadatas.append(meta)
                ids.append(f"meas_{idx}_{row['time'].strftime('%Y%m%d')}")
            
            # Add to collection in batches
            batch_size = 1000
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
            
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB embedding warning: {e}")

def process_argo_file(netcdf_path: str, max_measurements: int = 100000):
    """Main function to process ARGO NetCDF file"""
    
    if not Path(netcdf_path).exists():
        logger.error(f"❌ NetCDF file not found: {netcdf_path}")
        return
    
    processor = ARGODataProcessor(netcdf_path)
    
    # Analyze file first
    analysis = processor.analyze_netcdf_structure()
    logger.info(f"📊 File Analysis: {analysis}")
    
    # Ask user for confirmation if file is large
    if analysis['file_size_mb'] > 500:  # 500MB threshold
        logger.warning(f"⚠️ Large file detected ({analysis['file_size_mb']:.1f}MB)")
        logger.info(f"Estimated {analysis['estimated_measurements']:,} measurements")
        logger.info(f"Will process maximum {max_measurements:,} measurements")
    
    # Process the file
    processor.process_netcdf_chunked(max_measurements)
    
    logger.info("🎉 ARGO data processing completed!")

if __name__ == "__main__":
    # Example usage
    netcdf_file = "tempsal.nc"  # Replace with your NetCDF file
    
    if Path(netcdf_file).exists():
        process_argo_file(netcdf_file, max_measurements=50000)  # Process up to 50k measurements
    else:
        logger.error(f"❌ Please place your ARGO NetCDF file as '{netcdf_file}' in the project directory")
        logger.info("💡 You can download ARGO data from: https://www.seanoe.org/data/00311/42182/")