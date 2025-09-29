# FloatChat-AI Render Deployment TODO

## Approved Plan: Deploy on Render Free Tier with Qwen LLM via Hugging Face API

### Information Gathered
- Flat project structure under FloatChat-AI/
- Frontend: app.py (Streamlit)
- Backend: main.py (FastAPI with RAG/NL2SQL)
- Data: tempsal.nc loaded to Postgres via data_postgresql.py, ingested to Chroma via data_chroma_floats.py
- Config: config.py with local settings; needs env var support
- Requirements: Single requirements.txt; split for services
- LLM: Switch from Ollama to Qwen via Hugging Face Inference API (free tier)
- Vector Store: Use in-memory ChromaDB for ephemeral FS
- Adapt render.yaml for flat structure

### Steps to Complete
- [x] Create render.yaml with services for frontend, backend, postgres
- [x] Split requirements.txt into frontend_requirements.txt and backend_requirements.txt
- [x] Edit config.py: Add env var support for DATABASE_URL, HUGGINGFACE_API_KEY, VECTOR_STORE, BACKEND_URL, LLM_PROVIDER
- [x] Edit main.py: Integrate Hugging Face for Qwen LLM and sentence-transformers for embeddings; use in-memory Chroma if VECTOR_STORE=memory
- [x] Edit app.py: Use BACKEND_URL env var for API calls
- [x] Edit data_postgresql.py: Use config.DATABASE_URL (env-aware)
- [x] Edit data_chroma_floats.py: Use in-memory Chroma if VECTOR_STORE=memory
- [x] User: Push code to GitHub (merged updates into main and pushed)
- [ ] User: Create Render account, deploy services (frontend, backend, postgres)
- [ ] User: Set env vars (DATABASE_URL from postgres, HUGGINGFACE_API_KEY, BACKEND_URL, VECTOR_STORE=memory, LLM_PROVIDER=huggingface)
- [ ] User: Post-deploy: SSH into backend, run data_postgresql.py then data_chroma_floats.py
- [ ] User: Test frontend URL and backend /docs
- [ ] User: Verify health checks and demo functionality

### Dependent Files
- render.yaml (new)
- frontend_requirements.txt (new)
- backend_requirements.txt (new)
- config.py (edit)
- main.py (edit)
- app.py (edit)
- data_postgresql.py (edit)
- data_chroma_floats.py (edit)

### Followup Steps
- Installations: None (all via pip in render.yaml)
- Testing: Critical-path (key query flows, UI load, data load success)
- Monitoring: Render dashboard for logs/errors
