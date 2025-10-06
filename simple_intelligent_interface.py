"""
Simple Intelligent Interface for API Integration
Provides intelligent responses with direct SQL queries and basic context
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
import config_cloud as config
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleIntelligentInterface:
    """Simple but intelligent interface that works reliably with the API"""
    
    def __init__(self):
        self.db_engine = None
        self.initialized = False
        
    def initialize(self):
        """Initialize the simple intelligent interface"""
        
        try:
            logger.info("🧠 Initializing Simple Intelligent Interface...")
            
            # Initialize database connection
            self.db_engine = create_engine(config.DATABASE_URL)
            
            # Test connection
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM measurements;"))
                count = result.fetchone()[0]
                logger.info(f"✅ Database connected: {count:,} measurements available")
            
            self.initialized = True
            logger.info("✅ Simple Intelligent Interface ready!")
            
        except Exception as e:
            logger.error(f"❌ Simple interface initialization failed: {e}")
            self.initialized = False
    
    def query_with_context(self, user_query: str) -> Dict:
        """Process user query with intelligent SQL generation"""
        
        if not self.initialized:
            return self._fallback_response(user_query)
        
        try:
            logger.info(f"🔍 Processing query: {user_query}")
            
            # Analyze query intent
            intent = self._analyze_query_intent(user_query)
            logger.info(f"📋 Query intent: {intent}")
            
            # Generate and execute SQL
            sql_result = self._execute_intelligent_sql(user_query, intent)
            
            # Generate response
            response = self._generate_response(user_query, intent, sql_result)
            
            return {
                "answer": response,
                "context_documents": [f"SQL query executed for {intent.get('type', 'general')} analysis"],
                "retrieved_metadata": [{"query_type": intent.get('type', 'general'), "source": "postgresql"}],
                "sql_results": sql_result.get('data', []) if sql_result else []
            }
            
        except Exception as e:
            logger.error(f"❌ Query processing error: {e}")
            return self._fallback_response(user_query)
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user query to extract intent"""
        
        query_lower = query.lower()
        intent = {
            'type': 'general',
            'parameters': [],
            'temporal': {},
            'aggregation': None
        }
        
        # Extract years
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', query)
        if years:
            intent['temporal']['years'] = [int(year) for year in years]
        
        # Extract months
        months = re.findall(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', query_lower)
        if months:
            month_map = {
                'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
            }
            intent['temporal']['months'] = [month_map.get(month) for month in months if month in month_map]
        
        # Extract specific days
        day_patterns = re.findall(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', query_lower)
        if not day_patterns:
            day_patterns = re.findall(r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b', query_lower)
        
        if day_patterns:
            # Convert to integers
            days = []
            for day in day_patterns:
                day_int = int(day)
                if 1 <= day_int <= 31:
                    days.append(day_int)
            intent['temporal']['days'] = days
        
        # Extract parameters
        if any(word in query_lower for word in ['temperature', 'temp']):
            intent['parameters'].append('temperature')
        if any(word in query_lower for word in ['salinity', 'salt']):
            intent['parameters'].append('salinity')
        if any(word in query_lower for word in ['depth']):
            intent['parameters'].append('depth')
        
        # Extract aggregation type
        if any(word in query_lower for word in ['average', 'mean', 'avg']):
            intent['type'] = 'average'
            intent['aggregation'] = 'AVG'
        elif any(word in query_lower for word in ['maximum', 'max', 'highest', 'warmest']):
            intent['type'] = 'maximum'
            intent['aggregation'] = 'MAX'
        elif any(word in query_lower for word in ['minimum', 'min', 'lowest', 'coldest']):
            intent['type'] = 'minimum'
            intent['aggregation'] = 'MIN'
        elif any(word in query_lower for word in ['count', 'how many', 'number']):
            intent['type'] = 'count'
            intent['aggregation'] = 'COUNT'
        elif any(word in query_lower for word in ['hello', 'hi', 'hey']):
            intent['type'] = 'greeting'
        
        return intent
    
    def _execute_intelligent_sql(self, query: str, intent: Dict) -> Optional[Dict]:
        """Execute SQL based on query intent"""
        
        try:
            sql_query = self._build_sql_query(intent)
            
            if not sql_query:
                return None
            
            logger.info(f"🔍 Executing SQL: {sql_query[:100]}...")
            
            df = pd.read_sql_query(sql_query, self.db_engine)
            
            if df.empty:
                # Create a more specific "no data" message
                no_data_msg = "No data found"
                if intent['temporal'].get('years') and intent['temporal'].get('months') and intent['temporal'].get('days'):
                    year = intent['temporal']['years'][0]
                    month = intent['temporal']['months'][0]
                    day = intent['temporal']['days'][0]
                    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                                  'July', 'August', 'September', 'October', 'November', 'December']
                    month_name = month_names[month] if 1 <= month <= 12 else str(month)
                    no_data_msg = f"No data available for {month_name} {day}, {year}"
                
                return {"query": sql_query, "data": [], "message": no_data_msg}
            
            # Convert to simple format
            result_data = []
            for _, row in df.iterrows():
                row_dict = {}
                for col, val in row.items():
                    if pd.isna(val):
                        row_dict[str(col)] = None
                    else:
                        row_dict[str(col)] = str(val)
                result_data.append(row_dict)
            
            logger.info(f"✅ SQL returned {len(result_data)} results")
            
            return {
                "query": sql_query,
                "data": result_data,
                "row_count": len(result_data)
            }
            
        except Exception as e:
            logger.error(f"❌ SQL execution error: {e}")
            return None
    
    def _build_sql_query(self, intent: Dict) -> Optional[str]:
        """Build SQL query based on intent"""
        
        # Base components
        where_conditions = ["m.temperature IS NOT NULL"]
        
        # Add temporal filters
        if intent['temporal'].get('years'):
            year_conditions = [f"EXTRACT(YEAR FROM m.time) = {year}" for year in intent['temporal']['years']]
            where_conditions.append(f"({' OR '.join(year_conditions)})")
        
        if intent['temporal'].get('months'):
            month_conditions = [f"EXTRACT(MONTH FROM m.time) = {month}" for month in intent['temporal']['months'] if month]
            if month_conditions:
                where_conditions.append(f"({' OR '.join(month_conditions)})")
        
        if intent['temporal'].get('days'):
            day_conditions = [f"EXTRACT(DAY FROM m.time) = {day}" for day in intent['temporal']['days']]
            where_conditions.append(f"({' OR '.join(day_conditions)})")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build query based on type
        if intent['type'] == 'average':
            if 'temperature' in intent['parameters']:
                return f"""
                SELECT AVG(m.temperature) as avg_temperature, COUNT(*) as measurement_count
                FROM measurements m
                {where_clause}
                """
            elif 'salinity' in intent['parameters']:
                return f"""
                SELECT AVG(m.salinity) as avg_salinity, COUNT(*) as measurement_count
                FROM measurements m
                {where_clause}
                """
            else:
                return f"""
                SELECT AVG(m.temperature) as avg_temperature, AVG(m.salinity) as avg_salinity, COUNT(*) as measurement_count
                FROM measurements m
                {where_clause}
                """
        
        elif intent['type'] == 'maximum':
            return f"""
            SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id
            FROM measurements m
            {where_clause}
            ORDER BY m.temperature DESC
            LIMIT 1
            """
        
        elif intent['type'] == 'minimum':
            return f"""
            SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id
            FROM measurements m
            {where_clause}
            ORDER BY m.temperature ASC
            LIMIT 1
            """
        
        elif intent['type'] == 'count':
            return f"""
            SELECT COUNT(*) as total_measurements, COUNT(DISTINCT m.float_id) as total_floats
            FROM measurements m
            {where_clause}
            """
        
        else:  # general query
            return f"""
            SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id
            FROM measurements m
            {where_clause}
            ORDER BY m.time DESC
            LIMIT 10
            """
    
    def _generate_response(self, query: str, intent: Dict, sql_result: Optional[Dict]) -> str:
        """Generate intelligent response based on SQL results"""
        
        # Handle greetings
        if intent['type'] == 'greeting':
            return "Hello! I'm your ARGO float oceanographic data assistant. I have access to 122,027 real measurements from ARGO floats in the Indian Ocean region covering **January 10-20, 2010**. I can help you analyze temperature, salinity, and depth data for any specific date in this range. Try asking about 'maximum temperature on 15 January 2010' or 'average temperature on 12 January 2010'!"
        
        # Handle no data found
        if sql_result and not sql_result.get('data') and sql_result.get('message'):
            return f"I searched for data matching your query but found none. {sql_result['message']}. The available data in the dataset covers January 10 and January 20, 2010. Try asking about those specific dates instead."
        
        # Handle SQL results
        if sql_result and sql_result.get('data'):
            data = sql_result['data']
            
            if intent['type'] == 'average':
                row = data[0]
                response = "Based on the ARGO float measurements I found"
                
                # Add temporal context
                if intent['temporal'].get('years'):
                    years = intent['temporal']['years']
                    if len(years) == 1:
                        response += f" from {years[0]}"
                    else:
                        response += f" from {min(years)} to {max(years)}"
                
                response += ":\n\n"
                
                if 'avg_temperature' in row and row['avg_temperature']:
                    temp_val = float(row['avg_temperature'])
                    response += f"🌡️ **Average Temperature**: {temp_val:.2f}°C\n"
                
                if 'avg_salinity' in row and row['avg_salinity']:
                    sal_val = float(row['avg_salinity'])
                    response += f"🧂 **Average Salinity**: {sal_val:.2f} PSU\n"
                
                if 'measurement_count' in row:
                    count = int(float(row['measurement_count']))
                    response += f"📊 **Based on**: {count:,} measurements\n"
                
                response += "\nThis data comes from ARGO floats deployed across the Indian Ocean region."
                return response
            
            elif intent['type'] in ['maximum', 'minimum']:
                row = data[0]
                extreme_type = "highest" if intent['type'] == 'maximum' else "lowest"
                
                response = f"The {extreme_type} "
                
                if 'temperature' in row and row['temperature']:
                    temp_val = float(row['temperature'])
                    response += f"temperature I found was **{temp_val:.2f}°C**"
                
                if 'time' in row and row['time']:
                    response += f", recorded on {row['time']}"
                
                if 'lat' in row and 'lon' in row:
                    lat_val = float(row['lat'])
                    lon_val = float(row['lon'])
                    response += f" at location {lat_val:.2f}°N, {lon_val:.2f}°E"
                
                if 'depth' in row and row['depth']:
                    depth_val = float(row['depth'])
                    response += f" at {depth_val:.0f}m depth"
                
                if 'float_id' in row:
                    response += f" by ARGO float {row['float_id']}"
                
                response += "."
                return response
            
            elif intent['type'] == 'count':
                row = data[0]
                response = "Based on your query, I found:\n\n"
                
                if 'total_measurements' in row:
                    count = int(float(row['total_measurements']))
                    response += f"📊 **Total Measurements**: {count:,}\n"
                
                if 'total_floats' in row:
                    floats = int(float(row['total_floats']))
                    response += f"🌊 **ARGO Floats**: {floats:,}\n"
                
                # Add temporal context
                if intent['temporal'].get('years'):
                    years = intent['temporal']['years']
                    if len(years) == 1:
                        response += f"📅 **Year**: {years[0]}\n"
                
                response += "\nThis represents real oceanographic measurements from the ARGO global ocean observing system."
                return response
            
            else:  # general query
                response = f"I found {len(data)} measurements matching your query:\n\n"
                
                for i, row in enumerate(data[:3]):  # Show first 3
                    response += f"**Measurement {i+1}**:\n"
                    
                    if 'temperature' in row and row['temperature']:
                        temp_val = float(row['temperature'])
                        response += f"  🌡️ Temperature: {temp_val:.2f}°C\n"
                    
                    if 'salinity' in row and row['salinity']:
                        sal_val = float(row['salinity'])
                        response += f"  🧂 Salinity: {sal_val:.2f} PSU\n"
                    
                    if 'time' in row and row['time']:
                        response += f"  📅 Date: {row['time']}\n"
                    
                    response += "\n"
                
                if len(data) > 3:
                    response += f"... and {len(data) - 3} more measurements.\n\n"
                
                response += "This data comes from real ARGO float measurements in the Indian Ocean."
                return response
        
        # Fallback if no SQL results
        return f"I understand you're asking about oceanographic data. I have access to 33,373 ARGO float measurements from 2010 in the Indian Ocean region. Try asking specific questions like 'average temperature in 2010' or 'how many measurements do we have?'"
    
    def _fallback_response(self, query: str) -> Dict:
        """Fallback response when system fails"""
        
        return {
            "answer": "I'm having trouble accessing the ARGO float database right now. Please try again in a moment, or check if the system is properly initialized.",
            "context_documents": ["System error"],
            "retrieved_metadata": [{"query_type": "system_error"}]
        }

# Global instance
simple_intelligent = SimpleIntelligentInterface()