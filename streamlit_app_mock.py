"""
ARGO Float Data Visualization Dashboard
Government-grade Streamlit application for oceanographic data exploration
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ARGO Float Data Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "ARGO Float Data Visualization Dashboard - Government Edition"
    }
)

# Import custom components
try:
    from components.api_client import APIClient, APIException
    from components.data_transformer import DataTransformer
    from utils.dashboard_utils import init_session_state, validate_data_quality
    from dashboard_config import dashboard_config

    # Components to be created in later tasks
    from components.layout_manager import DashboardLayout
    from components.chat_interface import ChatInterface
    from components.map_visualization import InteractiveMap
    from components.profile_visualizer import ProfileVisualizer
    from components.data_manager import DataManager
    from components.statistics_manager import StatisticsManager
    from components.mock_data_provider import MockDataProvider
except ImportError as e:
    # Some components not yet available - will be created in later tasks
    logger.warning(f"Some components not yet available: {e}")
    APIClient = None
    DataTransformer = None
    init_session_state = None
    validate_data_quality = None
    dashboard_config = None
    MockDataProvider = None

def main():
    """Main application entry point"""

    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.api_client = None
        st.session_state.mock_data_provider = None
        st.session_state.chat_history = []
        st.session_state.selected_floats = []
        st.session_state.filter_state = {}

    # Initialize mock data provider for standalone mode
    if MockDataProvider and st.session_state.mock_data_provider is None:
        st.session_state.mock_data_provider = MockDataProvider()
        logger.info("Mock data provider initialized")

    # Initialize layout manager
    try:
        from components.layout_manager import DashboardLayout
        layout = DashboardLayout()

        # Apply custom styling
        layout.apply_custom_styling()

        # Render header
        layout.render_header()

        # Render sidebar and get navigation state
        sidebar_state = layout.render_sidebar()

        # Render main content
        layout.render_main_content(
            active_tab=sidebar_state["selected_tab"],
            filters=sidebar_state["filters"]
        )

        # Render footer
        layout.render_footer()

    except ImportError:
        # Fallback to simple layout if layout manager not available
        render_fallback_layout()

def render_overview_tab():
    """Render the overview dashboard tab"""
    st.header("📊 System Overview")

    # Get real data from mock provider
    if st.session_state.get('mock_data_provider'):
        mock_provider = st.session_state.mock_data_provider
        stats = mock_provider.get_system_statistics()

        # Create metrics with real data
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Floats", stats['active_floats'])
        with col2:
            st.metric("Total Profiles", stats['total_profiles'])
        with col3:
            st.metric("Measurements", f"{stats['total_measurements']:,}")
        with col4:
            st.metric("Data Quality", f"{stats['data_quality']}%")
    else:
        # Fallback placeholder metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Active Floats", "5")
        with col2:
            st.metric("Total Profiles", "60")
        with col3:
            st.metric("Measurements", "7,500")
        with col4:
            st.metric("Data Quality", "98.5%")

    st.markdown("---")

    # Overview visualizations
    st.subheader("Recent Activity")

    if st.session_state.get('mock_data_provider'):
        mock_provider = st.session_state.mock_data_provider
        measurements_df = mock_provider.get_measurements()

        # Group by date and count measurements
        measurements_df['date'] = pd.to_datetime(measurements_df['time']).dt.date
        daily_counts = measurements_df.groupby('date').size().reset_index(name='count')

        fig = px.line(daily_counts, x='date', y='count',
                      title="Daily Measurement Count")
        st.plotly_chart(fig, use_container_width=True)

        # Temperature distribution
        st.subheader("Temperature Distribution")
        fig_temp = px.histogram(measurements_df, x='temperature',
                               title="Temperature Distribution Across All Measurements",
                               nbins=50)
        st.plotly_chart(fig_temp, use_container_width=True)

        # Float locations
        st.subheader("Float Locations")
        floats_df = mock_provider.get_floats()
        fig_map = px.scatter_geo(floats_df,
                                lat='deployment_lat',
                                lon='deployment_lon',
                                hover_name='float_id',
                                title="ARGO Float Deployment Locations")
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        # Sample data for demonstration
        sample_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
            'Measurements': [100 + i*5 + (i%7)*10 for i in range(30)]
        })

        fig = px.line(sample_data, x='Date', y='Measurements',
                      title="Daily Measurement Count (Sample Data)")
        st.plotly_chart(fig, use_container_width=True)

def render_map_tab():
    """Render the interactive map tab"""
    st.header("🗺️ Interactive Float Map")

    if st.session_state.get('mock_data_provider'):
        mock_provider = st.session_state.mock_data_provider
        measurements_df = mock_provider.get_measurements()

        # Create interactive map with measurements
        st.subheader("Float Measurement Locations")

        # Sample a subset for performance
        sample_size = min(1000, len(measurements_df))
        sample_df = measurements_df.sample(sample_size)

        fig = px.scatter_mapbox(
            sample_df,
            lat='lat',
            lon='lon',
            color='temperature',
            size='depth',
            hover_data=['float_id', 'depth', 'temperature', 'salinity'],
            title=f"ARGO Float Measurements (Sample of {sample_size} points)",
            mapbox_style="open-street-map",
            zoom=3
        )
        st.plotly_chart(fig, use_container_width=True)

        # Float trajectories
        st.subheader("Float Trajectories")
        floats_df = mock_provider.get_floats()

        # Get profiles for trajectory visualization
        profiles_df = mock_provider.get_profiles()

        fig_traj = px.line_geo(
            profiles_df,
            lat='profile_lat',
            lon='profile_lon',
            color='float_id',
            hover_data=['float_id', 'cycle_number', 'profile_date'],
            title="ARGO Float Trajectories"
        )
        st.plotly_chart(fig_traj, use_container_width=True)
    else:
        st.info("🚧 Interactive map with ARGO float locations will be implemented in Task 4")

        # Placeholder map
        st.markdown("**Features to be implemented:**")
        st.markdown("- Float location markers with clustering")
        st.markdown("- Trajectory visualization with temporal coloring")
        st.markdown("- Geographic region selection")
        st.markdown("- Real-time filtering integration")

def render_profile_tab():
    """Render the profile analysis tab"""
    st.header("📈 Profile Analysis")

    if st.session_state.get('mock_data_provider'):
        mock_provider = st.session_state.mock_data_provider

        # Float selection
        floats_df = mock_provider.get_floats()
        float_options = floats_df['float_id'].tolist()
        selected_float = st.selectbox("Select Float", float_options)

        if selected_float:
            # Get profiles for selected float
            profiles_df = mock_provider.get_profiles(selected_float)
            profile_options = profiles_df['profile_id'].tolist()
            selected_profile = st.selectbox("Select Profile", profile_options)

            if selected_profile:
                # Get measurements for selected profile
                measurements_df = mock_provider.get_measurements([selected_profile])

                if not measurements_df.empty:
                    # Temperature profile
                    st.subheader("Temperature Profile")
                    fig_temp = px.line(measurements_df, x='temperature', y='depth',
                                     title=f"Temperature Profile - {selected_float} (Profile {selected_profile})")
                    fig_temp.update_yaxes(autorange="reversed")  # Depth increases downward
                    st.plotly_chart(fig_temp, use_container_width=True)

                    # Salinity profile
                    st.subheader("Salinity Profile")
                    fig_sal = px.line(measurements_df, x='salinity', y='depth',
                                    title=f"Salinity Profile - {selected_float} (Profile {selected_profile})")
                    fig_sal.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig_sal, use_container_width=True)

                    # T-S Diagram
                    st.subheader("T-S Diagram")
                    fig_ts = px.scatter(measurements_df, x='salinity', y='temperature',
                                      color='depth',
                                      title=f"Temperature-Salinity Diagram - {selected_float} (Profile {selected_profile})")
                    st.plotly_chart(fig_ts, use_container_width=True)

                    # BGC parameters
                    st.subheader("BGC Parameters")
                    col1, col2 = st.columns(2)

                    with col1:
                        fig_oxygen = px.line(measurements_df, x='oxygen', y='depth',
                                           title="Oxygen Profile")
                        fig_oxygen.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_oxygen, use_container_width=True)

                    with col2:
                        fig_chloro = px.line(measurements_df, x='chlorophyll', y='depth',
                                           title="Chlorophyll Profile")
                        fig_chloro.update_yaxes(autorange="reversed")
                        st.plotly_chart(fig_chloro, use_container_width=True)
                else:
                    st.warning("No measurements found for selected profile")
    else:
        st.info("🚧 Temperature-salinity-depth profiles will be implemented in Task 5")

        # Placeholder content
        st.markdown("**Features to be implemented:**")
        st.markdown("- Temperature-salinity-depth profile plots")
        st.markdown("- Multi-profile comparison overlays")
        st.markdown("- BGC parameter visualization")
        st.markdown("- Statistical analysis integration")

def render_chat_tab():
    """Render the chat interface tab"""
    try:
        from components.chat_interface import ChatInterface

        # Initialize chat interface with API client
        chat_interface = ChatInterface(api_client=st.session_state.get('api_client'))

        # Render the chat container
        chat_interface.render_chat_container()

    except ImportError:
        st.header("💬 Natural Language Query Interface")
        st.error("❌ Chat interface component not available")

        # Fallback interface with mock responses
        st.markdown("**Example queries you can ask:**")
        st.markdown("- 'Show me salinity profiles near the equator in March 2023'")
        st.markdown("- 'Compare BGC parameters in the Arabian Sea for the last 6 months'")
        st.markdown("- 'What are the nearest ARGO floats to this location?'")

        user_input = st.text_input("Enter your query:")
        if user_input:
            # Mock response based on query content
            if "salinity" in user_input.lower():
                st.info("📊 Based on mock data: Average salinity in the Indian Ocean ranges from 34.5-35.5 PSU, with higher values in deeper waters.")
            elif "temperature" in user_input.lower():
                st.info("🌡️ Based on mock data: Surface temperatures range from 25-30°C, decreasing to 4°C at 1000m depth.")
            elif "float" in user_input.lower():
                st.info("🎯 Based on mock data: 5 active ARGO floats deployed across the Indian Ocean region.")
            else:
                st.info("🚧 Chat interface will be available once all components are properly installed.")

    except Exception as e:
        st.error(f"Error loading chat interface: {e}")
        logger.error(f"Chat interface error: {e}")

def render_fallback_layout():
    """Fallback layout when layout manager is not available"""
    st.markdown("""
    <style>
    h1 {
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)
    st.title("🌊 ARGO Float Data Dashboard")
    st.markdown("**Government Oceanographic Data Visualization System**")

    # Simple sidebar
    with st.sidebar:
        st.header("Navigation")
        tab_selection = st.selectbox(
            "Select Dashboard Section",
            ["Overview", "Interactive Map", "Profile Analysis", "Chat Interface", "Data Export"]
        )

        st.header("System Status")
        if st.session_state.get('mock_data_provider'):
            st.success("✅ Mock Data Provider Active")
        elif st.session_state.get('api_client'):
            try:
                health_data = st.session_state.api_client.health_check()
                if health_data.get("status") == "healthy":
                    st.success("✅ Backend Connected")
                else:
                    st.error("❌ Backend Disconnected")
            except Exception as e:
                st.error("❌ Connection Failed")
        else:
            st.warning("⚠️ No Data Source Available")

    # Simple content based on tab
    if tab_selection == "Overview":
        render_overview_tab()
    elif tab_selection == "Interactive Map":
        render_map_tab()
    elif tab_selection == "Profile Analysis":
        render_profile_tab()
    elif tab_selection == "Chat Interface":
        render_chat_tab()
    elif tab_selection == "Data Export":
        render_export_tab()

def render_export_tab():
    """Render the data export tab"""
    st.header("📥 Data Export")

    if st.session_state.get('mock_data_provider'):
        mock_provider = st.session_state.mock_data_provider

        st.markdown("**Export Options:**")

        export_type = st.selectbox(
            "Select Data to Export",
            ["Float Information", "Profile Data", "Measurement Data"]
        )

        if export_type == "Float Information":
            floats_df = mock_provider.get_floats()
            st.dataframe(floats_df)
            csv = floats_df.to_csv(index=False)
            st.download_button("Download Float Data (CSV)", csv, "argo_floats.csv", "text/csv")

        elif export_type == "Profile Data":
            profiles_df = mock_provider.get_profiles()
            st.dataframe(profiles_df.head(50))  # Show first 50 for performance
            csv = profiles_df.to_csv(index=False)
            st.download_button("Download Profile Data (CSV)", csv, "argo_profiles.csv", "text/csv")

        elif export_type == "Measurement Data":
            measurements_df = mock_provider.get_measurements()
            st.dataframe(measurements_df.head(100))  # Show first 100 for performance
            csv = measurements_df.to_csv(index=False)
            st.download_button("Download Measurement Data (CSV)", csv, "argo_measurements.csv", "text/csv")
    else:
        st.info("🚧 Export functionality will be implemented in Task 8")

        # Placeholder export options
        st.markdown("**Export formats to be supported:**")
        st.markdown("- Visualizations: PNG, PDF, SVG")
        st.markdown("- Data: ASCII, NetCDF, CSV")
        st.markdown("- Reports: PDF with metadata")

if __name__ == "__main__":
    main()
