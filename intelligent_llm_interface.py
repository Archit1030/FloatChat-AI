"""
Intelligent LLM Interface with RAG Pipeline and SQL Query Generation
Provides specific answers by querying real ARGO data from PostgreSQL
"""

import logging
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import create_engine, text
import config_cloud as config
import re
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class IntelligentLLMInterface:
    """Intelligent conversational AI with RAG pipeline and SQL generation"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.db_engine = None
        self.initialized = False
        
    def initialize(self, mock_floats=None, mock_measurements=None):
        """Initialize the intelligent LLM interface"""
        
        try:
            logger.info("🧠 Initializing Intelligent LLM Interface...")
            
            # Initialize database connection
            logger.info("🗄️ Connecting to PostgreSQL...")
            self.db_engine = create_engine(config.DATABASE_URL)
            
            # Initialize embedding model
            logger.info("📊 Loading embedding model...")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            logger.info("🔍 Initializing ChromaDB...")
            self._initialize_chromadb()
            
            self.initialized = True
            logger.info("✅ Intelligent LLM Interface ready!")
            
        except Exception as e:
            logger.error(f"❌ Intelligent LLM initialization failed: {e}")
            self.initialized = False
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with proper embedding function"""
        
        try:
            # Use memory client for faster performance
            self.chroma_client = chromadb.EphemeralClient()
            
            # Create collection with proper embedding function
            from chromadb.utils import embedding_functions
            
            class SentenceTransformerEF(embedding_functions.EmbeddingFunction):
                def __init__(self, model):
                    self.model = model
                
                def __call__(self, input):
                    return self.model.encode(input).tolist()
            
            ef = SentenceTransformerEF(self.embedding_model)
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="argo_measurements",
                embedding_function=ef
            )
            
            # Populate with real data from database
            self._populate_chromadb_from_database()
            
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
            self.collection = None
    
    def _populate_chromadb_from_database(self):
        """Populate ChromaDB with real data from PostgreSQL"""
        
        logger.info("📝 Populating ChromaDB with real ARGO data...")
        
        try:
            # Get sample of real measurements with metadata
            query = """
            SELECT 
                m.id, m.float_id, m.time, m.lat, m.lon, m.depth,
                m.temperature, m.salinity, m.oxygen, m.ph, m.chlorophyll,
                f.wmo_id, f.deployment_date,
                p.cycle_number, p.profile_date
            FROM measurements m
            JOIN floats f ON m.float_id = f.float_id
            JOIN profiles p ON m.profile_id = p.profile_id
            ORDER BY m.time, m.float_id, m.depth
            LIMIT 500;
            """
            
            df = pd.read_sql_query(query, self.db_engine)
            
            if df.empty:
                logger.warning("⚠️ No data found in database")
                return
            
            documents = []
            metadatas = []
            ids = []
            
            for _, row in df.iterrows():
                # Create rich, contextual documents for better semantic search
                temp_str = f"{row['temperature']:.2f}°C" if pd.notna(row['temperature']) else "not measured"
                sal_str = f"{row['salinity']:.2f} PSU" if pd.notna(row['salinity']) else "not measured"
                
                # Add date context
                date_str = row['time'].strftime('%Y-%m-%d') if pd.notna(row['time']) else "unknown date"
                year = row['time'].year if pd.notna(row['time']) else None
                month = row['time'].strftime('%B') if pd.notna(row['time']) else None
                
                # Add BGC information if available
                bgc_info = ""
                if pd.notna(row['oxygen']):
                    bgc_info += f" Dissolved oxygen was {row['oxygen']:.2f} ml/L."
                if pd.notna(row['ph']):
                    bgc_info += f" pH was {row['ph']:.2f}."
                if pd.notna(row['chlorophyll']) and row['chlorophyll'] > 0.01:
                    bgc_info += f" Chlorophyll concentration was {row['chlorophyll']:.3f} mg/m³."
                
                # Create comprehensive document
                doc = (
                    f"On {date_str} in {year} during {month}, ARGO float {row['float_id']} "
                    f"(WMO ID: {row['wmo_id']}) recorded oceanographic measurements "
                    f"at latitude {row['lat']:.3f}° and longitude {row['lon']:.3f}° in the Indian Ocean. "
                    f"At a depth of {row['depth']:.1f} meters, the water temperature was {temp_str} "
                    f"and the salinity was {sal_str}.{bgc_info} "
                    f"This was measurement cycle {row['cycle_number']} for this float, "
                    f"which was deployed on {row['deployment_date']}."
                )
                
                # Rich metadata for filtering and SQL generation
                metadata = {
                    'measurement_id': int(row['id']),
                    'float_id': str(row['float_id']),
                    'wmo_id': int(row['wmo_id']) if pd.notna(row['wmo_id']) else None,
                    'year': int(year) if year else None,
                    'month': int(row['time'].month) if pd.notna(row['time']) else None,
                    'date': date_str,
                    'depth': float(row['depth']),
                    'temperature': float(row['temperature']) if pd.notna(row['temperature']) else None,
                    'salinity': float(row['salinity']) if pd.notna(row['salinity']) else None,
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'cycle_number': int(row['cycle_number']) if pd.notna(row['cycle_number']) else None,
                    'has_bgc': bool(pd.notna(row['oxygen']) or pd.notna(row['ph']) or pd.notna(row['chlorophyll']))
                }
                
                documents.append(doc)
                metadatas.append(metadata)
                ids.append(f"measurement_{row['id']}")
            
            # Add to collection
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"✅ Added {len(documents)} real measurements to ChromaDB")
        
        except Exception as e:
            logger.error(f"❌ Error populating ChromaDB: {e}")
    
    def query_with_context(self, user_query: str) -> Dict:
        """Process user query with intelligent RAG pipeline"""
        
        if not self.initialized:
            return self._fallback_response(user_query)
        
        try:
            logger.info(f"🔍 Processing query: {user_query}")
            
            # Step 1: Extract query intent and parameters
            query_intent = self._analyze_query_intent(user_query)
            logger.info(f"📋 Query intent: {query_intent}")
            
            # Step 2: Retrieve relevant context from ChromaDB
            context_docs, context_metadata = self._retrieve_relevant_context(user_query, query_intent)
            
            # Step 3: Generate and execute SQL query for specific data
            sql_results = self._generate_and_execute_sql(user_query, query_intent, context_metadata)
            
            # Step 4: Generate intelligent response
            response = self._generate_intelligent_response(user_query, query_intent, context_docs, sql_results)
            
            return {
                "answer": response,
                "context_documents": context_docs,
                "retrieved_metadata": context_metadata,
                "sql_results": sql_results.get('data', []) if sql_results else [],
                "query_intent": query_intent
            }
            
        except Exception as e:
            logger.error(f"❌ Query processing error: {e}")
            return self._fallback_response(user_query)
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user query to extract intent and parameters"""
        
        query_lower = query.lower()
        intent = {
            'type': 'general',
            'parameters': {},
            'temporal': {},
            'spatial': {},
            'measurement_type': []
        }
        
        # Extract temporal information
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        if years:
            intent['temporal']['years'] = [int(year) for year in years]
        
        months = re.findall(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', query_lower)
        if months:
            month_map = {
                'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
            }
            intent['temporal']['months'] = [month_map.get(month, None) for month in months if month in month_map]
        
        # Extract measurement types
        if any(word in query_lower for word in ['temperature', 'temp', 'warm', 'cold', 'hot']):
            intent['measurement_type'].append('temperature')
        if any(word in query_lower for word in ['salinity', 'salt', 'sal']):
            intent['measurement_type'].append('salinity')
        if any(word in query_lower for word in ['depth', 'deep', 'shallow', 'surface']):
            intent['measurement_type'].append('depth')
        if any(word in query_lower for word in ['oxygen', 'o2']):
            intent['measurement_type'].append('oxygen')
        if any(word in query_lower for word in ['ph', 'acidity']):
            intent['measurement_type'].append('ph')
        if any(word in query_lower for word in ['chlorophyll', 'chla']):
            intent['measurement_type'].append('chlorophyll')
        
        # Extract spatial information
        if any(word in query_lower for word in ['indian ocean', 'arabian sea', 'bay of bengal']):
            intent['spatial']['region'] = 'indian_ocean'
        
        # Determine query type
        if any(word in query_lower for word in ['average', 'mean', 'avg']):
            intent['type'] = 'average'
        elif any(word in query_lower for word in ['maximum', 'max', 'highest', 'warmest']):
            intent['type'] = 'maximum'
        elif any(word in query_lower for word in ['minimum', 'min', 'lowest', 'coldest']):
            intent['type'] = 'minimum'
        elif any(word in query_lower for word in ['range', 'between', 'from', 'to']):
            intent['type'] = 'range'
        elif any(word in query_lower for word in ['count', 'how many', 'number of']):
            intent['type'] = 'count'
        elif any(word in query_lower for word in ['trend', 'change', 'over time']):
            intent['type'] = 'trend'
        elif any(word in query_lower for word in ['compare', 'comparison', 'difference']):
            intent['type'] = 'comparison'
        
        return intent
    
    def _retrieve_relevant_context(self, query: str, intent: Dict) -> Tuple[List[str], List[Dict]]:
        """Retrieve relevant context from ChromaDB based on query and intent"""
        
        if not self.collection:
            return [], []
        
        try:
            # Create enhanced query for better semantic search
            enhanced_query = query
            
            # Add temporal context to search
            if intent['temporal'].get('years'):
                enhanced_query += f" in {' '.join(map(str, intent['temporal']['years']))}"
            if intent['temporal'].get('months'):
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                months = [month_names[m] for m in intent['temporal']['months'] if 1 <= m <= 12]
                enhanced_query += f" during {' '.join(months)}"
            
            # Add measurement type context
            if intent['measurement_type']:
                enhanced_query += f" {' '.join(intent['measurement_type'])} measurements"
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[enhanced_query],
                n_results=5,
                where=self._build_chromadb_filter(intent)
            )
            
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            logger.info(f"📊 Retrieved {len(documents)} relevant documents from ChromaDB")
            return documents, metadatas
            
        except Exception as e:
            logger.error(f"❌ ChromaDB query error: {e}")
            return [], []
    
    def _build_chromadb_filter(self, intent: Dict) -> Optional[Dict]:
        """Build ChromaDB filter based on query intent"""
        
        filters = {}
        
        # Add temporal filters
        if intent['temporal'].get('years'):
            if len(intent['temporal']['years']) == 1:
                filters['year'] = intent['temporal']['years'][0]
            else:
                filters['year'] = {"$in": intent['temporal']['years']}
        
        if intent['temporal'].get('months'):
            if len(intent['temporal']['months']) == 1:
                filters['month'] = intent['temporal']['months'][0]
            else:
                filters['month'] = {"$in": intent['temporal']['months']}
        
        return filters if filters else None
    
    def _generate_and_execute_sql(self, query: str, intent: Dict, context_metadata: List[Dict]) -> Optional[Dict]:
        """Generate and execute SQL query based on user intent"""
        
        try:
            # Build SQL query based on intent
            sql_query = self._build_sql_query(intent, context_metadata)
            
            if not sql_query:
                return None
            
            logger.info(f"🔍 Executing SQL: {sql_query[:100]}...")
            
            # Execute query
            df = pd.read_sql_query(sql_query, self.db_engine)
            
            if df.empty:
                return {"query": sql_query, "data": [], "message": "No data found"}
            
            # Convert to JSON-serializable format
            result_data = []
            for _, row in df.iterrows():
                row_dict = {}
                for col, val in row.items():
                    if pd.isna(val):
                        row_dict[str(col)] = None
                    elif hasattr(val, 'dtype') and 'int' in str(val.dtype):
                        row_dict[str(col)] = int(val)
                    elif hasattr(val, 'dtype') and 'float' in str(val.dtype):
                        row_dict[str(col)] = float(val)
                    else:
                        row_dict[str(col)] = str(val)
                result_data.append(row_dict)
            
            logger.info(f"✅ SQL query returned {len(result_data)} results")
            
            return {
                "query": sql_query,
                "data": result_data,
                "row_count": len(result_data)
            }
            
        except Exception as e:
            logger.error(f"❌ SQL execution error: {e}")
            return None
    
    def _build_sql_query(self, intent: Dict, context_metadata: List[Dict]) -> Optional[str]:
        """Build SQL query based on intent and context"""
        
        # Base query components
        select_clause = ""
        from_clause = """
        FROM measurements m
        JOIN floats f ON m.float_id = f.float_id
        JOIN profiles p ON m.profile_id = p.profile_id
        """
        where_conditions = ["m.temperature IS NOT NULL", "m.salinity IS NOT NULL"]
        group_by = ""
        order_by = ""
        limit_clause = "LIMIT 100"
        
        # Build SELECT based on query type and measurement type
        if intent['type'] == 'average':
            if 'temperature' in intent['measurement_type']:
                select_clause = "SELECT AVG(m.temperature) as avg_temperature, COUNT(*) as measurement_count"
            elif 'salinity' in intent['measurement_type']:
                select_clause = "SELECT AVG(m.salinity) as avg_salinity, COUNT(*) as measurement_count"
            else:
                select_clause = "SELECT AVG(m.temperature) as avg_temperature, AVG(m.salinity) as avg_salinity, COUNT(*) as measurement_count"
        
        elif intent['type'] == 'maximum':
            if 'temperature' in intent['measurement_type']:
                select_clause = "SELECT MAX(m.temperature) as max_temperature, m.time, m.lat, m.lon, m.depth, m.float_id"
            elif 'salinity' in intent['measurement_type']:
                select_clause = "SELECT MAX(m.salinity) as max_salinity, m.time, m.lat, m.lon, m.depth, m.float_id"
            else:
                select_clause = "SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id"
                order_by = "ORDER BY m.temperature DESC"
        
        elif intent['type'] == 'minimum':
            if 'temperature' in intent['measurement_type']:
                select_clause = "SELECT MIN(m.temperature) as min_temperature, m.time, m.lat, m.lon, m.depth, m.float_id"
            elif 'salinity' in intent['measurement_type']:
                select_clause = "SELECT MIN(m.salinity) as min_salinity, m.time, m.lat, m.lon, m.depth, m.float_id"
            else:
                select_clause = "SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id"
                order_by = "ORDER BY m.temperature ASC"
        
        elif intent['type'] == 'count':
            select_clause = "SELECT COUNT(*) as total_measurements, COUNT(DISTINCT m.float_id) as total_floats"
        
        elif intent['type'] == 'trend':
            select_clause = """
            SELECT 
                EXTRACT(YEAR FROM m.time) as year,
                EXTRACT(MONTH FROM m.time) as month,
                AVG(m.temperature) as avg_temperature,
                AVG(m.salinity) as avg_salinity,
                COUNT(*) as measurement_count
            """
            group_by = "GROUP BY EXTRACT(YEAR FROM m.time), EXTRACT(MONTH FROM m.time)"
            order_by = "ORDER BY year, month"
        
        else:  # general query
            select_clause = "SELECT m.temperature, m.salinity, m.time, m.lat, m.lon, m.depth, m.float_id, f.wmo_id"
            order_by = "ORDER BY m.time DESC"
        
        # Add temporal filters
        if intent['temporal'].get('years'):
            year_filter = " OR ".join([f"EXTRACT(YEAR FROM m.time) = {year}" for year in intent['temporal']['years']])
            where_conditions.append(f"({year_filter})")
        
        if intent['temporal'].get('months'):
            month_filter = " OR ".join([f"EXTRACT(MONTH FROM m.time) = {month}" for month in intent['temporal']['months']])
            where_conditions.append(f"({month_filter})")
        
        # Build final query
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query_parts = [select_clause, from_clause, where_clause, group_by, order_by, limit_clause]
        sql_query = " ".join([part for part in query_parts if part.strip()])
        
        return sql_query
    
    def _generate_intelligent_response(self, query: str, intent: Dict, context_docs: List[str], sql_results: Optional[Dict]) -> str:
        """Generate intelligent response based on query, context, and SQL results"""
        
        # If we have SQL results, use them for specific answers
        if sql_results and sql_results.get('data'):
            return self._generate_data_driven_response(query, intent, sql_results)
        
        # If we have context but no SQL results, use context
        if context_docs:
            return self._generate_context_based_response(query, intent, context_docs)
        
        # Fallback response
        return self._generate_fallback_response(query, intent)
    
    def _generate_data_driven_response(self, query: str, intent: Dict, sql_results: Dict) -> str:
        """Generate response based on actual SQL query results"""
        
        data = sql_results['data']
        
        if intent['type'] == 'average':
            if len(data) > 0:
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
                    response += f"🌡️ **Average Temperature**: {row['avg_temperature']:.2f}°C\n"
                if 'avg_salinity' in row and row['avg_salinity']:
                    response += f"🧂 **Average Salinity**: {row['avg_salinity']:.2f} PSU\n"
                if 'measurement_count' in row:
                    response += f"📊 **Based on**: {row['measurement_count']:,} measurements\n"
                
                response += "\nThis data comes from ARGO floats deployed across the Indian Ocean region, providing accurate oceanographic measurements."
                return response
        
        elif intent['type'] in ['maximum', 'minimum']:
            if len(data) > 0:
                row = data[0]
                extreme_type = "highest" if intent['type'] == 'maximum' else "lowest"
                
                response = f"The {extreme_type} "
                
                if 'temperature' in intent['measurement_type'] or ('max_temperature' in row or 'min_temperature' in row):
                    temp_val = row.get('max_temperature') or row.get('min_temperature') or row.get('temperature')
                    if temp_val:
                        response += f"temperature I found was **{temp_val:.2f}°C**"
                elif 'salinity' in intent['measurement_type'] or ('max_salinity' in row or 'min_salinity' in row):
                    sal_val = row.get('max_salinity') or row.get('min_salinity') or row.get('salinity')
                    if sal_val:
                        response += f"salinity I found was **{sal_val:.2f} PSU**"
                
                # Add location and time context
                if 'time' in row and row['time']:
                    response += f", recorded on {row['time']}"
                if 'lat' in row and 'lon' in row:
                    response += f" at location {row['lat']:.2f}°N, {row['lon']:.2f}°E"
                if 'depth' in row and row['depth']:
                    response += f" at {row['depth']:.0f}m depth"
                if 'float_id' in row:
                    response += f" by ARGO float {row['float_id']}"
                
                response += "."
                return response
        
        elif intent['type'] == 'count':
            if len(data) > 0:
                row = data[0]
                response = "Based on your query, I found:\n\n"
                
                if 'total_measurements' in row:
                    response += f"📊 **Total Measurements**: {row['total_measurements']:,}\n"
                if 'total_floats' in row:
                    response += f"🌊 **ARGO Floats**: {row['total_floats']:,}\n"
                
                # Add temporal context
                if intent['temporal'].get('years'):
                    years = intent['temporal']['years']
                    if len(years) == 1:
                        response += f"📅 **Year**: {years[0]}\n"
                    else:
                        response += f"📅 **Years**: {min(years)}-{max(years)}\n"
                
                response += "\nThis data represents real oceanographic measurements from the ARGO global ocean observing system."
                return response
        
        elif intent['type'] == 'trend':
            if len(data) > 1:
                response = "Here's the temporal trend I found:\n\n"
                
                for i, row in enumerate(data[:12]):  # Show up to 12 months
                    if 'year' in row and 'month' in row:
                        month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        month_name = month_names[int(row['month'])] if 1 <= int(row['month']) <= 12 else str(row['month'])
                        
                        response += f"**{month_name} {int(row['year'])}**: "
                        
                        if 'avg_temperature' in row and row['avg_temperature']:
                            response += f"Temp {row['avg_temperature']:.1f}°C"
                        if 'avg_salinity' in row and row['avg_salinity']:
                            response += f", Salinity {row['avg_salinity']:.1f} PSU"
                        if 'measurement_count' in row:
                            response += f" ({row['measurement_count']} measurements)"
                        
                        response += "\n"
                
                response += "\nThis shows the temporal variation in oceanographic conditions measured by ARGO floats."
                return response
        
        else:  # general query with specific results
            if len(data) > 0:
                response = f"I found {len(data)} specific measurements matching your query:\n\n"
                
                for i, row in enumerate(data[:5]):  # Show first 5 results
                    response += f"**Measurement {i+1}**:\n"
                    
                    if 'temperature' in row and row['temperature']:
                        response += f"  🌡️ Temperature: {row['temperature']:.2f}°C\n"
                    if 'salinity' in row and row['salinity']:
                        response += f"  🧂 Salinity: {row['salinity']:.2f} PSU\n"
                    if 'time' in row and row['time']:
                        response += f"  📅 Date: {row['time']}\n"
                    if 'depth' in row and row['depth']:
                        response += f"  📏 Depth: {row['depth']:.0f}m\n"
                    if 'float_id' in row:
                        response += f"  🌊 Float: {row['float_id']}\n"
                    
                    response += "\n"
                
                if len(data) > 5:
                    response += f"... and {len(data) - 5} more measurements.\n\n"
                
                response += "This data comes from real ARGO float measurements in the Indian Ocean."
                return response
        
        return "I found some data but couldn't format it properly. Please try rephrasing your question."
    
    def _generate_context_based_response(self, query: str, intent: Dict, context_docs: List[str]) -> str:
        """Generate response based on ChromaDB context when no SQL results available"""
        
        response = "Based on the ARGO float data I have access to:\n\n"
        
        # Extract information from context documents
        temps = []
        sals = []
        years = []
        
        for doc in context_docs[:3]:
            # Extract temperature values
            temp_matches = re.findall(r'temperature was ([\d.]+)°C', doc)
            temps.extend([float(t) for t in temp_matches])
            
            # Extract salinity values
            sal_matches = re.findall(r'salinity was ([\d.]+) PSU', doc)
            sals.extend([float(s) for s in sal_matches])
            
            # Extract years
            year_matches = re.findall(r'in (\d{4})', doc)
            years.extend([int(y) for y in year_matches])
        
        if temps:
            response += f"🌡️ Temperature measurements range from {min(temps):.1f}°C to {max(temps):.1f}°C\n"
        if sals:
            response += f"🧂 Salinity measurements range from {min(sals):.1f} to {max(sals):.1f} PSU\n"
        if years:
            response += f"📅 Data spans from {min(years)} to {max(years)}\n"
        
        response += f"\nThis information comes from {len(context_docs)} relevant ARGO float measurements I found in the database."
        
        return response
    
    def _generate_fallback_response(self, query: str, intent: Dict) -> str:
        """Generate fallback response when no specific data is found"""
        
        response = "I understand you're asking about "
        
        if intent['measurement_type']:
            response += f"{', '.join(intent['measurement_type'])} "
        
        if intent['temporal'].get('years'):
            years = intent['temporal']['years']
            if len(years) == 1:
                response += f"from {years[0]} "
            else:
                response += f"from {min(years)} to {max(years)} "
        
        response += "in the ARGO float dataset. "
        
        response += "While I don't have the exact data you're looking for, I can help you explore the available oceanographic measurements. "
        response += "The dataset contains temperature, salinity, and depth measurements from ARGO floats in the Indian Ocean region. "
        response += "Try asking about specific parameters like 'average temperature in 2010' or 'salinity measurements from January 2011'."
        
        return response
    
    def _fallback_response(self, query: str) -> Dict:
        """Simple fallback when system is not initialized"""
        
        return {
            "answer": "I'm having trouble accessing the ARGO float database right now. Please try again in a moment, or check if the system is properly initialized.",
            "context_documents": ["System error"],
            "retrieved_metadata": [{"query_type": "system_error"}]
        }

# Global instance
intelligent_llm = IntelligentLLMInterface()