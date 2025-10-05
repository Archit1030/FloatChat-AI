"""
ARGO Float Data Visualization Dashboard - Hybrid Version
Supports both backend API and mock data with automatic fallback
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Tuple
import logging
import json

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

# Configuration
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://your-app-name.railway.app")  # Update this after deployment
FALLBACK_TO_MOCK = True
API_TIMEOUT = 10

class HybridDataProvider:
    """Data provider that tries backend API first, falls back to mock data"""
    
    def __init__(self):
        self.backend_available = False
        self.mock_provider = None
        self._check_backend()
    
    def _check_backend(self):
        """Check if backend API is available"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=API_TIMEOUT)
            if response.status_code == 200:
                self.backend_available = True
                logger.info("✅ Backend API is available")
            else:
                logger.warning(f"⚠️ Backend API returned {response.status_code}")
                self.backend_available = False
        except Exception as e:
            logger.warning(f"⚠️ Backend API not available: {e}")
            self.backend_available = False
        
        # Initialize mock provider if needed
        if not self.backend_available and FALLBACK_TO_MOCK:
            try:
                from components.mock_data_provider import MockDataProvider
                self.mock_provider = MockDataProvider()
                logger.info("✅ Mock data provider initialized as fallback")
            except ImportError:
                logger.error("❌ Mock data provider not available")
    
    def get_statistics(self) -> Dict:
        """Get system statistics from backend or mock data"""
        if self.backend_available:
            try:
                response = requests.get(f"{BACKEND_URL}/statistics", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Backend statistics error: {e}")
        
        # Fallback to mock data
        if self.mock_provider:
            return self.mock_provider.get_system_statistics()
        
        # Ultimate fallback
        return {
            "active_floats": 5,
            "total_measurements": 7500,
            "avg_temperature": 18.5,
            "avg_salinity": 35.1,
            "data_quality": 98.5
        }
    
    def get_floats(self) -> List[Dict]:
        """Get float information"""
        if self.backend_available:
            try:
                response = requests.get(f"{BACKEND_URL}/floats", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Backend floats error: {e}")
        
        # Fallback to mock data
        if self.mock_provider:
            return self.mock_provider.get_floats().to_dict(orient="records")
        
        return []
    
    def get_measurements(self, limit: int = 1000) -> List[Dict]:
        """Get measurement data"""
        if self.backend_available:
            try:
                response = requests.get(f"{BACKEND_URL}/measurements?limit={limit}", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Backend measurements error: {e}")
        
        # Fallback to mock data
        if self.mock_provider:
            return self.mock_provider.get_measurements().head(limit).to_dict(orient="records")
        
        return []
    
    def query_data(self, query_text: str) -> Dict:
        """Query data using natural language"""
        if self.backend_available:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/query",
                    json={"query_text": query_text},
                    timeout=API_TIMEOUT
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Backend query error: {e}")
        
        # Simple fallback response
        return {
            "answer": f"I understand you're asking about: '{query_text}'. The backend API is currently unavailable, but I can help you explore the available mock oceanographic data through the dashboard tabs.",
            "context_documents": ["Mock data fallback"],
            "retrieved_metadata": [{"source": "fallback", "status": "backend_unavailable"}]
        }

def main():
    """Main application entry point"""
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.data_provider = HybridDataProvider()
        st.session_state.chat_history = []
    
    # Apply custom styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e8b57 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white !important;
        margin: 0;
        text-align: center;
    }
    .status-indicator {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .status-healthy { background-color: #d4edda; color: #155724; }
    .status-warning { background-color: #fff3cd; color: #856404; }
    .status-error { background-color: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌊 ARGO Float Data Dashboard</h1>
        <p style="color: white; text-align: center; margin: 0;">Government Oceanographic Data Visualization System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🧭 Navigation")
        tab_selection = st.selectbox(
            "Select Dashboard Section",
            ["Overview", "Interactive Map", "Profile Analysis", "Chat Interface", "Data Export"]
        )
        
        st.header("🔌 System Status")
        data_provider = st.session_state.data_provider
        
        if data_provider.backend_available:
            st.markdown('<div class="status-indicator status-healthy">✅ Backend API Connected</div>', unsafe_allow_html=True)
            st.success(f"API: {BACKEND_URL}")
        elif data_provider.mock_provider:
            st.markdown('<div class="status-indicator status-warning">⚠️ Using Mock Data</div>', unsafe_allow_html=True)
            st.info("Backend unavailable, using fallback data")
        else:
            st.markdown('<div class="status-indicator status-error">❌ No Data Source</div>', unsafe_allow_html=True)
            st.error("Both backend and mock data unavailable")
        
        # Refresh button
        if st.button("🔄 Refresh Connection"):
            st.session_state.data_provider = HybridDataProvider()
            st.experimental_rerun()
    
    # Main content based on tab selection
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

def render_overview_tab():
    """Render the overview dashboard tab"""
    st.header("📊 System Overview")
    
    data_provider = st.session_state.data_provider
    stats = data_provider.get_statistics()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Floats", stats.get('active_floats', 'N/A'))
    with col2:
        st.metric("Total Measurements", f"{stats.get('total_measurements', 0):,}")
    with col3:
        st.metric("Avg Temperature", f"{stats.get('avg_temperature', 0):.1f}°C")
    with col4:
        st.metric("Data Quality", f"{stats.get('data_quality', 0):.1f}%")
    
    st.markdown("---")
    
    # Data visualization
    st.subheader("📈 Data Overview")
    
    measurements = data_provider.get_measurements(limit=500)
    if measurements:
        df = pd.DataFrame(measurements)
        
        # Temperature distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig_temp = px.histogram(df, x='temperature', nbins=30,
                                  title="Temperature Distribution")
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            fig_depth = px.scatter(df, x='temperature', y='depth',
                                 title="Temperature vs Depth")
            fig_depth.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_depth, use_container_width=True)
    else:
        st.info("No measurement data available")

def render_map_tab():
    """Render the interactive map tab"""
    st.header("🗺️ Interactive Float Map")
    
    data_provider = st.session_state.data_provider
    floats = data_provider.get_floats()
    
    if floats:
        df_floats = pd.DataFrame(floats)
        
        # Float locations map
        fig_map = px.scatter_geo(
            df_floats,
            lat='deployment_lat',
            lon='deployment_lon',
            hover_name='float_id',
            title="ARGO Float Deployment Locations",
            projection="natural earth"
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Measurements map
        measurements = data_provider.get_measurements(limit=1000)
        if measurements:
            df_measurements = pd.DataFrame(measurements)
            
            fig_measurements = px.scatter_mapbox(
                df_measurements.sample(min(500, len(df_measurements))),
                lat='lat',
                lon='lon',
                color='temperature',
                size='depth',
                hover_data=['float_id', 'temperature', 'salinity'],
                title="Measurement Locations (Sample)",
                mapbox_style="open-street-map",
                zoom=3
            )
            st.plotly_chart(fig_measurements, use_container_width=True)
    else:
        st.info("No float data available")

def render_profile_tab():
    """Render the profile analysis tab"""
    st.header("📈 Profile Analysis")
    
    data_provider = st.session_state.data_provider
    measurements = data_provider.get_measurements(limit=2000)
    
    if measurements:
        df = pd.DataFrame(measurements)
        
        # Float selection
        float_ids = df['float_id'].unique()
        selected_float = st.selectbox("Select Float", float_ids)
        
        if selected_float:
            float_data = df[df['float_id'] == selected_float]
            
            # Profile visualization
            col1, col2 = st.columns(2)
            
            with col1:
                fig_temp = px.line(float_data, x='temperature', y='depth',
                                 title=f"Temperature Profile - {selected_float}")
                fig_temp.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with col2:
                fig_sal = px.line(float_data, x='salinity', y='depth',
                                title=f"Salinity Profile - {selected_float}")
                fig_sal.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_sal, use_container_width=True)
            
            # T-S Diagram
            fig_ts = px.scatter(float_data, x='salinity', y='temperature',
                              color='depth',
                              title=f"T-S Diagram - {selected_float}")
            st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No measurement data available for profile analysis")

def render_chat_tab():
    """Render the chat interface tab"""
    st.header("💬 Natural Language Query Interface")
    
    data_provider = st.session_state.data_provider
    
    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about oceanographic data..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your query..."):
                response = data_provider.query_data(prompt)
                answer = response.get("answer", "I couldn't process your query.")
                st.write(answer)
                
                # Add to history
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

def render_export_tab():
    """Render the data export tab"""
    st.header("📥 Data Export")
    
    data_provider = st.session_state.data_provider
    
    export_type = st.selectbox(
        "Select Data to Export",
        ["Float Information", "Measurement Data", "Statistics"]
    )
    
    if st.button("Generate Export"):
        if export_type == "Float Information":
            floats = data_provider.get_floats()
            if floats:
                df = pd.DataFrame(floats)
                csv = df.to_csv(index=False)
                st.download_button("Download Float Data", csv, "argo_floats.csv", "text/csv")
                st.dataframe(df)
        
        elif export_type == "Measurement Data":
            measurements = data_provider.get_measurements(limit=5000)
            if measurements:
                df = pd.DataFrame(measurements)
                csv = df.to_csv(index=False)
                st.download_button("Download Measurements", csv, "argo_measurements.csv", "text/csv")
                st.dataframe(df.head(100))
        
        elif export_type == "Statistics":
            stats = data_provider.get_statistics()
            stats_df = pd.DataFrame([stats])
            csv = stats_df.to_csv(index=False)
            st.download_button("Download Statistics", csv, "argo_statistics.csv", "text/csv")
            st.json(stats)

if __name__ == "__main__":
    main()