"""
Enhanced LLM Interface for ARGO Float Dashboard
Provides conversational AI with ChromaDB integration and Qwen model
"""

import logging
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import config_cloud as config
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedLLMInterface:
    """Enhanced conversational AI for oceanographic data queries"""
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.mock_data = None
        self.initialized = False
        
    def initialize(self, mock_floats=None, mock_measurements=None):
        """Initialize the LLM and ChromaDB components"""
        
        try:
            logger.info("🤖 Initializing Enhanced LLM Interface...")
            
            # Store mock data for fallback
            self.mock_floats = mock_floats
            self.mock_measurements = mock_measurements
            
            # Initialize embedding model for ChromaDB
            logger.info("📊 Loading embedding model...")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            logger.info("🗄️ Initializing ChromaDB...")
            self._initialize_chromadb()
            
            # Initialize Qwen model
            logger.info("🧠 Loading Qwen model...")
            self._initialize_qwen_model()
            
            self.initialized = True
            logger.info("✅ Enhanced LLM Interface ready!")
            
        except Exception as e:
            logger.error(f"❌ LLM initialization failed: {e}")
            logger.info("🔄 Falling back to simple responses")
            self.initialized = False
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB with mock data"""
        
        try:
            # Use memory client for faster performance
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
            
            # Add mock data to ChromaDB if available
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
        
        # Sample a subset for performance (limit to 200 documents)
        sample_size = min(200, len(self.mock_measurements))
        sample_data = self.mock_measurements.sample(sample_size) if len(self.mock_measurements) > sample_size else self.mock_measurements
        
        for idx, row in sample_data.iterrows():
            # Create rich, contextual documents
            temp_str = f"{row['temperature']:.2f}°C" if pd.notna(row['temperature']) else "not available"
            sal_str = f"{row['salinity']:.2f} PSU" if pd.notna(row['salinity']) else "not available"
            
            # Add BGC information if available
            bgc_info = ""
            if 'oxygen' in row and pd.notna(row['oxygen']):
                bgc_info += f" The dissolved oxygen was {row['oxygen']:.2f} ml/L."
            if 'ph' in row and pd.notna(row['ph']):
                bgc_info += f" The pH was {row['ph']:.2f}."
            if 'chlorophyll' in row and pd.notna(row['chlorophyll']) and row['chlorophyll'] > 0.01:
                bgc_info += f" The chlorophyll concentration was {row['chlorophyll']:.3f} mg/m³."
            
            doc = (
                f"On {row['time']}, ARGO float {row['float_id']} recorded oceanographic measurements "
                f"at latitude {row['lat']:.3f}° and longitude {row['lon']:.3f}°. "
                f"At a depth of {row['depth']:.1f} meters, the water temperature was {temp_str} "
                f"and the salinity was {sal_str}.{bgc_info} "
                f"This measurement is part of the global ocean monitoring network."
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
    
    def _initialize_qwen_model(self):
        """Initialize Qwen model for conversational AI"""
        
        try:
            # Use a more powerful Qwen model
            model_name = "Qwen/Qwen2.5-3B-Instruct"  # 3B model for better performance
            
            logger.info(f"Loading {model_name}...")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            
            # Use CPU for compatibility, GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None
            )
            
            # Create pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1,
                max_new_tokens=300,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("✅ Qwen model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Qwen model loading failed: {e}")
            logger.info("🔄 Will use fallback responses")
            self.pipeline = None
    
    def query_with_context(self, user_query: str) -> Dict:
        """Process user query with ChromaDB context and Qwen model"""
        
        if not self.initialized:
            return self._fallback_response(user_query)
        
        try:
            # Step 1: Retrieve relevant context from ChromaDB
            context_docs, context_metadata = self._retrieve_context(user_query)
            
            # Step 2: Check if query is about oceanographic data
            if not self._is_oceanographic_query(user_query):
                return {
                    "answer": "I'm an AI assistant specialized in ARGO float oceanographic data. I can help you explore ocean temperature, salinity, depth measurements, and float locations. What would you like to know about ocean data?",
                    "context_documents": ["Scope clarification"],
                    "retrieved_metadata": [{"query_type": "out_of_scope"}]
                }
            
            # Step 3: Generate response using Qwen with context
            if self.pipeline and context_docs:
                response = self._generate_qwen_response(user_query, context_docs)
            else:
                response = self._generate_contextual_fallback(user_query, context_docs, context_metadata)
            
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
                n_results=3  # Get top 3 most relevant documents
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
    
    def _generate_qwen_response(self, query: str, context_docs: List[str]) -> str:
        """Generate response using Qwen model with context"""
        
        # Create context string
        context = "\n".join(context_docs[:2])  # Use top 2 documents
        
        # Create prompt for Qwen
        prompt = f"""You are an expert oceanographer and AI assistant specializing in ARGO float data analysis. You provide accurate, helpful responses about ocean measurements and data.

Context from ARGO float measurements:
{context}
User Qu
estion: {query}

Instructions:
- Answer based ONLY on the provided ARGO float data context
- Be conversational and helpful, like talking to a colleague
- If the context doesn't contain relevant information, say so honestly
- Include specific numbers and measurements when available
- Don't make up facts or data not in the context
- Keep responses concise but informative

Response:"""

        try:
            # Generate response
            outputs = self.pipeline(
                prompt,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            generated_text = outputs[0]['generated_text']
            
            # Extract only the response part (after "Response:")
            if "Response:" in generated_text:
                response = generated_text.split("Response:")[-1].strip()
            else:
                response = generated_text[len(prompt):].strip()
            
            # Clean up the response
            response = self._clean_response(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Qwen generation error: {e}")
            return self._generate_contextual_fallback(query, context_docs, [])
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the model response"""
        
        # Remove any unwanted tokens or repetitions
        response = response.strip()
        
        # Remove common model artifacts
        artifacts = ["<|endoftext|>", "<|im_end|>", "<|im_start|>"]
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        # Ensure response ends properly
        if response and not response.endswith(('.', '!', '?')):
            response += "."
        
        return response.strip()
    
    def _generate_contextual_fallback(self, query: str, context_docs: List[str], context_metadata: List[Dict]) -> str:
        """Generate contextual response without full LLM"""
        
        query_lower = query.lower()
        
        # Extract data from context metadata
        temps = [m.get('temperature') for m in context_metadata if m.get('temperature') is not None]
        sals = [m.get('salinity') for m in context_metadata if m.get('salinity') is not None]
        depths = [m.get('depth') for m in context_metadata if m.get('depth') is not None]
        
        # Temperature queries
        if 'temperature' in query_lower:
            if temps:
                avg_temp = np.mean(temps)
                min_temp = min(temps)
                max_temp = max(temps)
                return f"Based on the ARGO float measurements I found, the temperature ranges from {min_temp:.1f}°C to {max_temp:.1f}°C, with an average of {avg_temp:.1f}°C. These measurements come from various depths in the ocean, showing the typical temperature variation you'd expect in marine environments."
            else:
                return "I found some ARGO float data, but the specific temperature measurements aren't available in the context I retrieved. Could you try asking about a specific location or depth range?"
        
        # Salinity queries
        elif 'salinity' in query_lower:
            if sals:
                avg_sal = np.mean(sals)
                min_sal = min(sals)
                max_sal = max(sals)
                return f"The salinity measurements from ARGO floats show values ranging from {min_sal:.2f} to {max_sal:.2f} PSU (Practical Salinity Units), with an average of {avg_sal:.2f} PSU. This is typical for ocean water, which generally has salinity around 35 PSU."
            else:
                return "I have ARGO float data available, but I don't see specific salinity measurements in the current context. Try asking about salinity in a particular ocean region."
        
        # Depth queries
        elif 'depth' in query_lower:
            if depths:
                max_depth = max(depths)
                min_depth = min(depths)
                return f"The ARGO float measurements I found span depths from {min_depth:.0f}m to {max_depth:.0f}m. ARGO floats typically profile the ocean from the surface down to about 2000 meters, collecting valuable data about ocean properties at different depths."
            else:
                return "I have ARGO float data, but specific depth information isn't available in the current context. ARGO floats generally measure ocean properties from surface to about 2000m depth."
        
        # Float information queries
        elif 'float' in query_lower or 'argo' in query_lower:
            float_ids = list(set([m.get('float_id') for m in context_metadata if m.get('float_id')]))
            if float_ids:
                return f"I found data from {len(float_ids)} ARGO float(s): {', '.join(float_ids[:3])}{'...' if len(float_ids) > 3 else ''}. ARGO floats are autonomous instruments that drift with ocean currents, diving to collect temperature and salinity profiles every 10 days."
            else:
                return "ARGO floats are autonomous oceanographic instruments that collect temperature and salinity profiles. They're part of a global network monitoring ocean conditions. I have data from several floats in the Indian Ocean region."
        
        # Location queries
        elif any(word in query_lower for word in ['mumbai', 'location', 'where', 'latitude', 'longitude']):
            if context_metadata:
                lats = [m.get('lat') for m in context_metadata if m.get('lat') is not None]
                lons = [m.get('lon') for m in context_metadata if m.get('lon') is not None]
                if lats and lons:
                    return f"The ARGO float measurements I found are from locations around {np.mean(lats):.1f}°N, {np.mean(lons):.1f}°E in the Indian Ocean region. However, I don't have specific data for Mumbai's coastal waters - ARGO floats operate in the open ocean, typically far from shore."
            return "I have ARGO float data from the Indian Ocean region, but these floats operate in deep, open ocean waters rather than near coastal cities like Mumbai. For coastal temperature data, you'd need different monitoring systems."
        
        # General queries
        else:
            if context_docs:
                return f"I found some relevant ARGO float data for your query. The measurements show oceanographic conditions from various locations and depths in the Indian Ocean. Could you be more specific about what aspect of the ocean data you're interested in - temperature, salinity, depth, or float locations?"
            else:
                return "I'm here to help you explore ARGO float oceanographic data! I can tell you about ocean temperature, salinity, depth measurements, and float locations in the Indian Ocean region. What specific aspect of ocean data would you like to know about?"
    
    def _fallback_response(self, query: str) -> Dict:
        """Simple fallback response when LLM is not available"""
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['hello', 'hi', 'hey']):
            answer = "Hello! I'm your ARGO float data assistant. I can help you explore oceanographic measurements including temperature, salinity, depth profiles, and float locations. What would you like to know about ocean data?"
        elif 'temperature' in query_lower:
            answer = "I can help you with ocean temperature data from ARGO floats. These instruments measure temperature profiles from surface to deep waters. Would you like to know about temperature at specific depths or locations?"
        elif 'salinity' in query_lower:
            answer = "ARGO floats measure ocean salinity, which typically ranges around 35 PSU (Practical Salinity Units) in open ocean waters. I can provide more specific salinity information if you tell me about a particular region or depth."
        else:
            answer = "I'm specialized in ARGO float oceanographic data. I can help you explore ocean temperature, salinity, depth measurements, and float locations. What specific ocean data are you interested in?"
        
        return {
            "answer": answer,
            "context_documents": ["Fallback response"],
            "retrieved_metadata": [{"query_type": "fallback"}]
        }

# Global instance
enhanced_llm = EnhancedLLMInterface()