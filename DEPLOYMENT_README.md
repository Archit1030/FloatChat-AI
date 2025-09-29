# ARGO Float Data Dashboard - Streamlit Deployment

This is a standalone Streamlit application that demonstrates ARGO float data visualization using mock data.

## Features

- **System Overview**: Real-time statistics and data summaries
- **Interactive Maps**: Float locations and trajectories with measurement data
- **Profile Analysis**: Temperature-salinity-depth profiles and BGC parameters
- **Data Export**: Download capabilities for float data, profiles, and measurements
- **Mock Data**: Fully functional with realistic ARGO float data (no backend required)

## Deployment

### Streamlit Cloud

1. Fork or clone this repository
2. Ensure your repository does NOT contain a `packages.txt` file (delete it if present, as it causes deployment errors)
3. Go to [share.streamlit.io](https://share.streamlit.io)
4. Connect your GitHub account
5. Select this repository
6. Set the main file path to: `streamlit_app_mock.py`
7. Click Deploy
8. If deployment fails due to PostgreSQL dependencies, the app will use `frontend_requirements.txt` automatically

### Local Development

```bash
# Install dependencies
pip install -r frontend_requirements.txt

# Run the app
streamlit run streamlit_app_mock.py
```

## Files Structure

- `streamlit_app_mock.py`: Main application with mock data integration
- `components/mock_data_provider.py`: Generates realistic ARGO float data
- `components/data_manager_mock.py`: Handles data filtering and operations
- `frontend_requirements.txt`: Python dependencies

## Mock Data

The application uses realistic mock data including:
- 5 ARGO floats deployed across the Indian Ocean
- 12 monthly profiles per float (1 year of data)
- 25 depth levels per profile (5m to 1500m)
- Physical parameters: temperature, salinity, oxygen, pH, chlorophyll

## Data Sources

All data is generated programmatically and includes:
- Realistic oceanographic profiles
- Geographic distribution across Indian Ocean regions
- Temporal patterns (seasonal variations)
- Quality-controlled parameter ranges

## Navigation

- **Overview**: System statistics and data visualizations
- **Interactive Map**: Float locations and measurement scatter plots
- **Profile Analysis**: Detailed T-S-depth profiles and BGC parameters
- **Data Export**: CSV download functionality

## Technical Details

- Built with Streamlit 1.28.1
- Data visualization using Plotly
- Pandas for data manipulation
- No external API dependencies (fully standalone)
