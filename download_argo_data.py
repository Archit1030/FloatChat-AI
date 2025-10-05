"""
ARGO Data Download Helper
Downloads sample ARGO data for testing and development
"""

import requests
import os
from pathlib import Path
import logging
from typing import Optional
import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARGODataDownloader:
    """Helper to download ARGO data for testing"""
    
    def __init__(self):
        self.data_sources = {
            'sample_indian_ocean': {
                'url': 'https://www.seanoe.org/data/00311/42182/data/42182.nc',
                'description': 'Sample Indian Ocean ARGO data',
                'size_mb': 50,
                'filename': 'indian_ocean_sample.nc'
            },
            'global_sample': {
                'url': 'https://data-argo.ifremer.fr/geo/indian_ocean/2023/01/R5903248_001.nc',
                'description': 'Single float sample data',
                'size_mb': 5,
                'filename': 'single_float_sample.nc'
            }
        }
    
    def download_sample_data(self, dataset_key: str = 'global_sample', force_download: bool = False) -> Optional[str]:
        """Download sample ARGO data"""
        
        if dataset_key not in self.data_sources:
            logger.error(f"❌ Unknown dataset: {dataset_key}")
            logger.info(f"Available datasets: {list(self.data_sources.keys())}")
            return None
        
        dataset_info = self.data_sources[dataset_key]
        filename = dataset_info['filename']
        
        # Check if file already exists
        if Path(filename).exists() and not force_download:
            logger.info(f"✅ File already exists: {filename}")
            return filename
        
        logger.info(f"📥 Downloading {dataset_info['description']} (~{dataset_info['size_mb']}MB)")
        logger.info(f"URL: {dataset_info['url']}")
        
        try:
            response = requests.get(dataset_info['url'], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Progress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            logger.info(f"✅ Downloaded: {filename}")
            return filename
            
        except requests.RequestException as e:
            logger.error(f"❌ Download failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None
    
    def create_synthetic_data(self, filename: str = 'synthetic_argo.nc', num_floats: int = 3, num_profiles: int = 12) -> str:
        """Create synthetic ARGO data for testing"""
        
        logger.info(f"🧪 Creating synthetic ARGO data: {filename}")
        
        import numpy as np
        import pandas as pd
        
        # Create synthetic data
        np.random.seed(42)  # For reproducible data
        
        # Time dimension (monthly profiles for a year)
        times = pd.date_range('2023-01-01', periods=num_profiles, freq='30D')
        
        # Depth levels (standard ARGO depths)
        depths = np.array([5, 10, 20, 30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000])
        
        # Float locations in Indian Ocean
        float_lats = np.array([10.5, -5.8, 15.2])[:num_floats]
        float_lons = np.array([75.2, 80.1, 70.5])[:num_floats]
        
        # Create coordinate arrays
        n_measurements = num_floats * num_profiles * len(depths)
        
        # Initialize arrays
        time_array = np.repeat(times, num_floats * len(depths))
        lat_array = np.tile(np.repeat(float_lats, len(depths)), num_profiles)
        lon_array = np.tile(np.repeat(float_lons, len(depths)), num_profiles)
        depth_array = np.tile(depths, num_floats * num_profiles)
        
        # Add some drift to positions
        lat_drift = np.random.normal(0, 0.5, n_measurements)
        lon_drift = np.random.normal(0, 0.5, n_measurements)
        lat_array = lat_array + lat_drift
        lon_array = lon_array + lon_drift
        
        # Generate realistic temperature profiles
        temp_array = np.zeros(n_measurements)
        for i, depth in enumerate(depth_array):
            if depth < 100:
                temp_array[i] = 28 - (depth/100)*8 + np.random.normal(0, 0.5)
            elif depth < 500:
                temp_array[i] = 20 - (depth-100)/400*10 + np.random.normal(0, 0.3)
            else:
                temp_array[i] = 4 + np.random.normal(0, 0.2)
        
        # Generate realistic salinity profiles
        sal_array = 35.0 + np.random.normal(0, 0.1, n_measurements)
        sal_array[depth_array > 200] += 0.2  # Saltier deep water
        
        # Create xarray dataset
        ds = xr.Dataset({
            'TEMP': (['obs'], temp_array),
            'SAL': (['obs'], sal_array),
            'PRES': (['obs'], depth_array * 1.025),  # Pressure approximation
        }, coords={
            'TIME': (['obs'], time_array),
            'LATITUDE': (['obs'], lat_array),
            'LONGITUDE': (['obs'], lon_array),
            'DEPTH': (['obs'], depth_array),
        })
        
        # Add attributes
        ds.attrs['title'] = 'Synthetic ARGO Float Data'
        ds.attrs['institution'] = 'Test Data Generator'
        ds.attrs['source'] = 'Synthetic data for development'
        
        # Save to NetCDF
        ds.to_netcdf(filename)
        logger.info(f"✅ Created synthetic data: {filename} ({n_measurements:,} measurements)")
        
        return filename
    
    def validate_netcdf_file(self, filename: str) -> bool:
        """Validate NetCDF file structure"""
        
        try:
            with xr.open_dataset(filename) as ds:
                logger.info(f"📊 Validating: {filename}")
                logger.info(f"Dimensions: {dict(ds.dims)}")
                logger.info(f"Variables: {list(ds.data_vars.keys())}")
                logger.info(f"Coordinates: {list(ds.coords.keys())}")
                
                # Check for required variables
                required_vars = ['TEMP', 'SAL']  # Minimum required
                missing_vars = [var for var in required_vars if var not in ds.data_vars and var not in ds.coords]
                
                if missing_vars:
                    logger.warning(f"⚠️ Missing variables: {missing_vars}")
                else:
                    logger.info("✅ All required variables present")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False

def main():
    """Main function for data download/creation"""
    
    downloader = ARGODataDownloader()
    
    # Check if we have any NetCDF files
    netcdf_files = list(Path('.').glob('*.nc'))
    
    if netcdf_files:
        logger.info(f"📁 Found existing NetCDF files: {[f.name for f in netcdf_files]}")
        
        # Validate existing files
        for nc_file in netcdf_files:
            downloader.validate_netcdf_file(str(nc_file))
    else:
        logger.info("📥 No NetCDF files found. Creating synthetic data...")
        
        # Create synthetic data for testing
        synthetic_file = downloader.create_synthetic_data(
            filename='tempsal.nc',  # Use the expected filename
            num_floats=5,
            num_profiles=12
        )
        
        # Validate the created file
        downloader.validate_netcdf_file(synthetic_file)
        
        logger.info(f"🎉 Ready to process data with: python argo_data_processor.py")

if __name__ == "__main__":
    main()