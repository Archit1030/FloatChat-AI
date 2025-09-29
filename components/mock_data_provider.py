"""
Mock Data Provider for Streamlit Frontend
Provides in-memory mock ARGO float data without backend dependencies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockDataProvider:
    """Provides mock ARGO float data for frontend demonstration"""

    def __init__(self):
        self.floats_df = None
        self.profiles_df = None
        self.measurements_df = None
        self._initialized = False

    def initialize_data(self) -> None:
        """Initialize mock data in memory"""
        if self._initialized:
            return

        logger.info("Generating mock ARGO float data...")

        # Generate mock data
        self.floats_df, self.profiles_df, self.measurements_df = self._generate_mock_data()

        self._initialized = True
        logger.info(f"Generated {len(self.floats_df)} floats, {len(self.profiles_df)} profiles, {len(self.measurements_df)} measurements")

    def _generate_mock_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate realistic mock ARGO float data"""

        # Create 5 floats in Indian Ocean region
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
            },
            {
                'float_id': 'ARGO_0004',
                'wmo_id': 5900004,
                'deployment_date': datetime(2023, 7, 5).date(),
                'deployment_lat': 5.3,
                'deployment_lon': 85.7,
                'status': 'ACTIVE',
                'last_contact': datetime(2024, 9, 1).date()
            },
            {
                'float_id': 'ARGO_0005',
                'wmo_id': 5900005,
                'deployment_date': datetime(2023, 9, 12).date(),
                'deployment_lat': -2.1,
                'deployment_lon': 67.8,
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

            # Create 12 profiles per float (monthly for a year)
            for cycle in range(1, 13):
                profile_date = float_info['deployment_date'] + timedelta(days=cycle*30)
                # Slight drift in position
                lat_offset = np.random.normal(0, 0.8)
                lon_offset = np.random.normal(0, 0.8)

                profile = {
                    'profile_id': profile_id_counter,
                    'float_id': float_id,
                    'cycle_number': cycle,
                    'profile_date': profile_date,
                    'profile_lat': base_lat + lat_offset,
                    'profile_lon': base_lon + lon_offset,
                    'n_levels': 25  # 25 depth levels
                }
                profiles.append(profile)

                # Generate measurements for this profile
                depths = np.linspace(5, 1500, 25)  # 5m to 1500m

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
                        'id': len(measurements) + 1,  # Unique measurement ID
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

    def get_floats(self) -> pd.DataFrame:
        """Get all float information"""
        self.initialize_data()
        return self.floats_df.copy()

    def get_profiles(self, float_id: Optional[str] = None) -> pd.DataFrame:
        """Get profiles, optionally filtered by float_id"""
        self.initialize_data()
        if float_id:
            return self.profiles_df[self.profiles_df['float_id'] == float_id].copy()
        return self.profiles_df.copy()

    def get_measurements(self, profile_ids: Optional[List[int]] = None, float_id: Optional[str] = None) -> pd.DataFrame:
        """Get measurements, optionally filtered by profile_ids or float_id"""
        self.initialize_data()
        df = self.measurements_df.copy()

        if profile_ids:
            df = df[df['profile_id'].isin(profile_ids)]
        if float_id:
            df = df[df['float_id'] == float_id]

        return df

    def get_float_info(self, float_id: str) -> Dict[str, Any]:
        """Get comprehensive float information"""
        self.initialize_data()

        float_info = self.floats_df[self.floats_df['float_id'] == float_id]
        if float_info.empty:
            return {"error": "Float not found"}

        profiles = self.get_profiles(float_id)
        measurements = self.get_measurements(float_id=float_id)

        return {
            "float_info": float_info.iloc[0].to_dict(),
            "profile_summary": {
                "total_profiles": len(profiles),
                "date_range": f"{profiles['profile_date'].min()} to {profiles['profile_date'].max()}" if not profiles.empty else "No profiles",
                "avg_lat": profiles['profile_lat'].mean() if not profiles.empty else None,
                "avg_lon": profiles['profile_lon'].mean() if not profiles.empty else None
            },
            "measurement_summary": {
                "total_measurements": len(measurements),
                "avg_temperature": measurements['temperature'].mean() if not measurements.empty else None,
                "avg_salinity": measurements['salinity'].mean() if not measurements.empty else None,
                "depth_range": f"{measurements['depth'].min()}m to {measurements['depth'].max()}m" if not measurements.empty else "No measurements"
            }
        }

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        self.initialize_data()

        return {
            'active_floats': len(self.floats_df),
            'total_profiles': len(self.profiles_df),
            'total_measurements': len(self.measurements_df),
            'data_quality': 98.5,  # Mock quality score
            'date_range': f"{self.measurements_df['time'].min()} to {self.measurements_df['time'].max()}",
            'regions': ['Arabian Sea', 'Bay of Bengal', 'Indian Ocean', 'Equatorial Indian Ocean']
        }

    def query_measurements(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Query measurements with filters"""
        self.initialize_data()
        df = self.measurements_df.copy()

        if not filters:
            return df

        # Apply date filters
        if 'start_date' in filters and 'end_date' in filters:
            df = df[(df['time'] >= filters['start_date']) & (df['time'] <= filters['end_date'])]

        # Apply geographic filters
        if 'lat_min' in filters:
            df = df[df['lat'] >= filters['lat_min']]
        if 'lat_max' in filters:
            df = df[df['lat'] <= filters['lat_max']]
        if 'lon_min' in filters:
            df = df[df['lon'] >= filters['lon_min']]
        if 'lon_max' in filters:
            df = df[df['lon'] <= filters['lon_max']]

        # Apply depth filters
        if 'depth_min' in filters:
            df = df[df['depth'] >= filters['depth_min']]
        if 'depth_max' in filters:
            df = df[df['depth'] <= filters['depth_max']]

        # Apply parameter filters
        if 'temp_min' in filters:
            df = df[df['temperature'] >= filters['temp_min']]
        if 'temp_max' in filters:
            df = df[df['temperature'] <= filters['temp_max']]

        if 'sal_min' in filters:
            df = df[df['salinity'] >= filters['sal_min']]
        if 'sal_max' in filters:
            df = df[df['salinity'] <= filters['sal_max']]

        return df

    def get_sample_queries(self) -> Dict[str, Any]:
        """Get sample queries for user guidance"""
        return {
            "analytical_queries": {
                "Basic Analysis": [
                    "What is the average temperature at different depths?",
                    "Show me salinity profiles by region",
                    "Compare temperature trends over time"
                ]
            },
            "semantic_queries": {
                "Current Data": [
                    "Show me temperature measurements near the equator",
                    "Tell me about salinity profiles in deep water",
                    "What ARGO floats are active in the Indian Ocean?"
                ]
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """Mock health check"""
        return {
            "status": "healthy",
            "database": "mock",
            "chromadb": "mock",
            "message": "Mock data provider is operational"
        }
