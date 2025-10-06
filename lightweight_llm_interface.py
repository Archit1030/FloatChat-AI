"""
Lightweight LLM Interface for Cloud Deployment
Uses HuggingFace API instead of local models for better cloud performance
"""

import logging
import requests
import chromadb
from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import config_cloud as config
import os

logger = logging.getLogger(__name__)

class LightweightLLMInterface:
    """Lightweight conversational AI using HuggingFace API"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.mock_data = None
        self.initialized = False
        self.hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
    def initialize(self, mock_floats=None, mock_measurements=None):
        """Initialize the lightweight LLM interface"""
        
        try:
            logger.info("🤖 Initializing Lightweight LLM Interface...")
            
            # Store mock data
            self.mock_floats = mock_floats
            self.mock_measurements = mock_measurements
            
            # Initialize embedding model
            logger.info("📊 Loading embedding model...")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            logger.info("🗄️ Initializing ChromaDB...")
            self._initialize_chromadb()
            
            self.initialized = True
            logger.info("✅ Lightweight LLM Interface ready!")
            
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            self.initialized = False
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with mock data"""
        
        try:
            # Use memory client for cloud deployment
            self.chroma_client = chromadb.EphemeralClient()
            
            # Create collection with proper embedding function
            from chromadb.utils import embedding_functions
            
            # Create a custom embedding function
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
            
            # Add mock data to ChromaDB
            if self.mock_measurements is not None and len(self.mock_measurements) > 0:
                self._populate_chromadb()
            
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
            self.collection = None
    
    def _populate_chromadb(self):
        """Populate ChromaDB with mock oceanographic data"""
        
        logger.info("📝 Populating ChromaDB with oceanographic data...")
        
        documents = []
        metadatas = []
        ids = []
        
        # Sample a subset for performance (limit to 100 documents for cloud)
        sample_size = min(100, len(self.mock_measurements))
        sample_data = self.mock_measurements.sample(sample_size) if len(self.mock_measurements) > sample_size else self.mock_measurements
        
        for idx, row in sample_data.iterrows():
            # Create rich, contextual documents
            temp_str = f"{row['temperature']:.2f}°C" if pd.notna(row['temperature']) else "not available"
            sal_str = f"{row['salinity']:.2f} PSU" if pd.notna(row['salinity']) else "not available"
            
            doc = (
                f"On {row['time']}, ARGO float {row['float_id']} recorded oceanographic measurements "
                f"at latitude {row['lat']:.3f}° and longitude {row['lon']:.3f}°. "
                f"At a depth of {row['depth']:.1f} meters, the water temperature was {temp_str} "
                f"and the salinity was {sal_str}. "
                f"This measurement is part of the global ocean monitoring network in the Indian Ocean region."
            )
            
            metadata = {
                'float_id': str(row['float_id']),
                'depth': float(row['depth']),
                'temperature': float(row['temperature']) if pd.notna(row['temperature']) else None,
                'salinity': float(row['salinity']) if pd.notna(row['salinity']) else None,
                'lat': float(row['lat']),
                'lon': float(row['lon']),
                'date': str(row['time'])[:10]
            }
            
            documents.append(doc)
            metadatas.append(metadata)
            ids.append(f"measurement_{idx}")
        
        # Add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to ChromaDB")
    
    def query_with_context(self, user_query: str) -> Dict:
        """Process user query with ChromaDB context"""
        
        if not self.initialized:
            return self._fallback_response(user_query)
        
        try:
            # Step 1: Retrieve relevant context from ChromaDB
            context_docs, context_metadata = self._retrieve_context(user_query)
            
            # Step 2: Check if query is about oceanographic data
            if not self._is_oceanographic_query(user_query):
                return {
                    "answer": "I'm an AI assistant specialized in ARGO float oceanographic data. I can help you explore ocean temperature, salinity, depth measurements, and float locations in the Indian Ocean region. What would you like to know about ocean data?",
                    "context_documents": ["Scope clarification"],
                    "retrieved_metadata": [{"query_type": "out_of_scope"}]
                }
            
            # Step 3: Generate contextual response
            if self.hf_api_key and context_docs:
                response = self._generate_hf_response(user_query, context_docs)
            else:
                response = self._generate_contextual_response(user_query, context_docs, context_metadata)
            
            return {
                "answer": response,
                "context_documents": context_docs,
                "retrieved_metadata": context_metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Query processing error: {e}")
            return self._fallback_response(user_query)
    
    def _retrieve_context(self, query: str) -> Tuple[List[str], List[Dict]]:
        """Retrieve relevant context from ChromaDB"""
        
        if not self.collection:
            return [], []
        
        try:
            # Query ChromaDB for relevant documents
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            return documents, metadatas
            
        except Exception as e:
            logger.error(f"❌ ChromaDB query error: {e}")
            return [], []
    
    def _is_oceanographic_query(self, query: str) -> bool:
        """Check if query is related to oceanographic data"""
        
        ocean_keywords = [
            'temperature', 'salinity', 'depth', 'ocean', 'sea', 'water',
            'argo', 'float', 'measurement', 'profile', 'marine', 'oceanographic',
            'chlorophyll', 'oxygen', 'ph', 'pressure', 'latitude', 'longitude',
            'indian ocean', 'arabian sea', 'bay of bengal'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in ocean_keywords)
    
    def _generate_hf_response(self, query: str, context_docs: List[str]) -> str:
        """Generate response using HuggingFace API"""
        
        try:
            # Create context string
            context = "\n".join(context_docs[:2])
            
            # Create prompt
            prompt = f"""You are an expert oceanographer analyzing ARGO float data. Answer the user's question based on the provided oceanographic measurements.

Context from ARGO float measurements:
{context}

User Question: {query}

Provide a helpful, accurate response based only on the data provided. Be conversational and include specific measurements when available."""

            # Call HuggingFace API
            headers = {"Authorization": f"Bearer {self.hf_api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{config.LLM_MODEL}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
            
            # Fallback if API fails
            return self._generate_contextual_response(query, context_docs, [])
            
        except Exception as e:
            logger.error(f"❌ HuggingFace API error: {e}")
            return self._generate_contextual_response(query, context_docs, [])
    
    def _generate_contextual_response(self, query: str, context_docs: List[str], context_metadata: List[Dict]) -> str:
        """Generate contextual response using retrieved data"""
        
        query_lower = query.lower()
        
        # Extract data from context metadata
        temps = [m.get('temperature') for m in context_metadata if m.get('temperature') is not None]
        sals = [m.get('salinity') for m in context_metadata if m.get('salinity') is not None]
        depths = [m.get('depth') for m in context_metadata if m.get('depth') is not None]
        
        # Greeting responses
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return "Hello! I'm your ARGO float oceanographic data assistant. I can help you explore ocean temperature, salinity, depth measurements, and float locations in the Indian Ocean region. My dataset covers **January 10-20, 2010** with 122,027 real measurements. What would you like to know about the ocean data?"
        
        # Temperature queries
        elif 'temperature' in query_lower:
            if temps:
                avg_temp = np.mean(temps)
                min_temp = min(temps)
                max_temp = max(temps)
                return f"Based on the ARGO float measurements I found, the ocean temperature ranges from {min_temp:.1f}°C to {max_temp:.1f}°C, with an average of {avg_temp:.1f}°C. These measurements come from various depths in the Indian Ocean, showing the typical temperature variation you'd expect in marine environments. The warmer temperatures are typically found near the surface, while cooler temperatures occur at greater depths."
            else:
                return "I found some ARGO float data, but the specific temperature measurements aren't available in the context I retrieved. Could you try asking about temperature at a specific location or depth range in the Indian Ocean?"
        
        # Salinity queries
        elif 'salinity' in query_lower:
            if sals:
                avg_sal = np.mean(sals)
                min_sal = min(sals)
                max_sal = max(sals)
                return f"The salinity measurements from ARGO floats show values ranging from {min_sal:.2f} to {max_sal:.2f} PSU (Practical Salinity Units), with an average of {avg_sal:.2f} PSU. This is typical for Indian Ocean water, which generally has salinity around 35 PSU. The slight variations you see are due to different depths and locations within the ocean basin."
            else:
                return "I have ARGO float data available, but I don't see specific salinity measurements in the current context. Try asking about salinity in a particular part of the Indian Ocean region."
        
        # Location-specific queries (like Mumbai)
        elif any(word in query_lower for word in ['mumbai', 'bombay', 'coastal', 'shore']):
            return "I have ARGO float data from the Indian Ocean region, but these floats operate in deep, open ocean waters rather than near coastal cities like Mumbai. ARGO floats typically stay in waters deeper than 2000 meters and far from shore. For coastal temperature data near Mumbai, you'd need different monitoring systems like coastal buoys or satellite data."
        
        # Float information queries
        elif 'float' in query_lower or 'argo' in query_lower:
            float_ids = list(set([m.get('float_id') for m in context_metadata if m.get('float_id')]))
            if float_ids:
                return f"I found data from {len(float_ids)} ARGO float(s) in the Indian Ocean: {', '.join(float_ids[:3])}{'...' if len(float_ids) > 3 else ''}. ARGO floats are autonomous instruments that drift with ocean currents, diving to collect temperature and salinity profiles every 10 days. They're crucial for understanding ocean climate and weather patterns."
            else:
                return "ARGO floats are autonomous oceanographic instruments that collect temperature and salinity profiles throughout the world's oceans. They're part of a global network of about 4,000 floats monitoring ocean conditions. I have data from several floats operating in the Indian Ocean region."
        
        # Depth queries
        elif 'depth' in query_lower:
            if depths:
                max_depth = max(depths)
                min_depth = min(depths)
                return f"The ARGO float measurements I found span depths from {min_depth:.0f}m to {max_depth:.0f}m. ARGO floats typically profile the ocean from the surface down to about 2000 meters, collecting valuable data about how ocean properties change with depth. This vertical profiling helps scientists understand ocean circulation and climate patterns."
            else:
                return "ARGO floats generally measure ocean properties from surface to about 2000m depth. They dive down collecting data, then surface to transmit their measurements via satellite before diving again for the next profile cycle."
        
        # General or unclear queries
        else:
            if context_docs:
                return f"I found some relevant ARGO float data from the Indian Ocean region. The measurements show oceanographic conditions from various locations and depths. Could you be more specific about what aspect of the ocean data you're interested in - temperature, salinity, depth profiles, or float locations?"
            else:
                return "I'm here to help you explore ARGO float oceanographic data from the Indian Ocean! I can tell you about ocean temperature, salinity, depth measurements, and float locations. What specific aspect of ocean data would you like to know about?"
    
    def _fallback_response(self, query: str) -> Dict:
        """Simple fallback response when LLM is not available"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['hello', 'hi', 'hey']):
            answer = "Hello! I'm your ARGO float data assistant. I can help you explore oceanographic measurements including temperature, salinity, depth profiles, and float locations in the Indian Ocean region. My dataset covers January 10-20, 2010 with 122,027 real measurements. What would you like to know about ocean data?"
        elif 'temperature' in query_lower:
            answer = "I can help you with ocean temperature data from ARGO floats. These instruments measure temperature profiles from surface to deep waters in the Indian Ocean. Would you like to know about temperature at specific depths or locations?"
        elif 'salinity' in query_lower:
            answer = "ARGO floats measure ocean salinity, which typically ranges around 35 PSU (Practical Salinity Units) in Indian Ocean waters. I can provide more specific salinity information if you tell me about a particular region or depth."
        else:
            answer = "I'm specialized in ARGO float oceanographic data from the Indian Ocean region. I can help you explore ocean temperature, salinity, depth measurements, and float locations. What specific ocean data are you interested in?"
        
        return {
            "answer": answer,
            "context_documents": ["Fallback response"],
            "retrieved_metadata": [{"query_type": "fallback"}]
        }

# Global instance
lightweight_llm = LightweightLLMInterface()