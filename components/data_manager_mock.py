"""
Mock Data Manager Component
Handles data filtering and operations using mock data provider
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from datetime import datetime, timedelta, date
from components.mock_data_provider import MockDataProvider

logger = logging.getLogger(__name__)

class MockDataManager:
    """Manages data filtering and operations using mock data"""

    def __init__(self, mock_provider: Optional[MockDataProvider] = None):
        self.mock_provider = mock_provider or st.session_state.get('mock_data_provider')

        # Initialize filter state in session state
        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = self._get_default_filters()

    def get_filtered_data(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Get filtered measurement data"""
        if not self.mock_provider:
            return pd.DataFrame()

        # Get all measurements
        data = self.mock_provider.get_measurements()

        if filters:
            data = self.apply_filters(data, filters)

        return data

    def apply_filters(self, data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to dataset"""

        if data.empty:
            return data

        filtered_data = data.copy()

        try:
            # Apply temporal filters
            if filters.get("date_range"):
                start_date, end_date = filters["date_range"]
                filtered_data['time'] = pd.to_datetime(filtered_data['time'])
                filtered_data = filtered_data[
                    (filtered_data['time'].dt.date >= start_date) &
                    (filtered_data['time'].dt.date <= end_date)
                ]

            # Apply geographic filters
            region_bounds = filters.get("region_bounds")
            if region_bounds and not region_bounds.get('center_lat'):
                # Bounding box
                filtered_data = filtered_data[
                    (filtered_data['lat'] >= region_bounds['south']) &
                    (filtered_data['lat'] <= region_bounds['north']) &
                    (filtered_data['lon'] >= region_bounds['west']) &
                    (filtered_data['lon'] <= region_bounds['east'])
                ]

            # Apply depth filters
            if filters.get("depth_range"):
                depth_min, depth_max = filters["depth_range"]
                filtered_data = filtered_data[
                    (filtered_data['depth'] >= depth_min) &
                    (filtered_data['depth'] <= depth_max)
                ]

            # Apply temperature filters
            if filters.get("enable_temp_filter") and filters.get("temp_range"):
                temp_min, temp_max = filters["temp_range"]
                filtered_data = filtered_data[
                    (filtered_data['temperature'] >= temp_min) &
                    (filtered_data['temperature'] <= temp_max) &
                    filtered_data['temperature'].notna()
                ]

            # Apply salinity filters
            if filters.get("enable_sal_filter") and filters.get("sal_range"):
                sal_min, sal_max = filters["sal_range"]
                filtered_data = filtered_data[
                    (filtered_data['salinity'] >= sal_min) &
                    (filtered_data['salinity'] <= sal_max) &
                    filtered_data['salinity'].notna()
                ]

            # Apply float filters
            if filters.get("float_ids_list"):
                filtered_data = filtered_data[
                    filtered_data['float_id'].isin(filters["float_ids_list"])
                ]

            logger.info(f"Applied filters: {len(data)} -> {len(filtered_data)} records")

            return filtered_data

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            st.error(f"Error applying filters: {str(e)}")
            return data

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        if not self.mock_provider:
            return {}

        return self.mock_provider.get_system_statistics()

    def export_data(self, data: pd.DataFrame, format: str = 'csv') -> str:
        """Export data in specified format"""
        if data.empty:
            return ""

        if format.lower() == 'csv':
            return data.to_csv(index=False)
        else:
            # For now, just return CSV
            return data.to_csv(index=False)

    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filter configuration"""
        return {
            "date_mode": "Date Range",
            "date_range": (datetime.now().date() - timedelta(days=365), datetime.now().date()),
            "region_mode": "Predefined Regions",
            "predefined_region": "All Regions",
            "depth_mode": "Range",
            "depth_range": (0, 1000),
            "quality_levels": ["Excellent", "Good"],
            "float_selection_mode": "All Floats"
        }
