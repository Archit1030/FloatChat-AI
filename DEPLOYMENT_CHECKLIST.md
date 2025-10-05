# 🚀 ARGO Float Dashboard - Deployment Checklist

Follow this step-by-step checklist to deploy your full-stack ARGO Float Dashboard with zero cost!

## ✅ **Phase 1: Backend Deployment (Railway.app)**

### **Step 1.1: Create Railway Account**
- [ ] Go to https://railway.app
- [ ] Sign up with your GitHub account
- [ ] Verify your email address

### **Step 1.2: Deploy Backend**
- [ ] Click "New Project" in Railway dashboard
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose your `FloatChat-AI` repository
- [ ] Railway will automatically detect the configuration from `railway.json`

### **Step 1.3: Add PostgreSQL Database**
- [ ] In Railway project dashboard, click "New"
- [ ] Select "Database" → "PostgreSQL"
- [ ] Railway will automatically create `DATABASE_URL` environment variable

### **Step 1.4: Configure Environment Variables**
Add these environment variables in Railway dashboard:

**Required Variables:**
```env
HUGGINGFACE_API_KEY=your_huggingface_token_here
LLM_PROVIDER=huggingface
VECTOR_STORE=memory
```

**Optional Variables (for optimization):**
```env
LLM_MODEL=microsoft/DialoGPT-medium
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_FLOATS=500
MAX_DOCUMENTS=10000
BATCH_SIZE=5000
```

### **Step 1.5: Get Your Backend URL**
- [ ] After deployment, copy your Railway app URL (e.g., `https://floatchat-ai-production.railway.app`)
- [ ] Test the URL by visiting `https://your-url.railway.app/health`
- [ ] You should see: `{"status":"healthy","database":"connected","vector_store":"connected"}`

## ✅ **Phase 2: Update GitHub Actions**

### **Step 2.1: Update Backend Wake-up URL**
- [ ] Edit `.github/workflows/wake-backend.yml`
- [ ] Replace `https://your-app-name.railway.app` with your actual Railway URL
- [ ] Commit and push the changes

### **Step 2.2: Test GitHub Actions**
- [ ] Go to your GitHub repository → Actions tab
- [ ] Click on "Wake Backend API" workflow
- [ ] Click "Run workflow" to test manually
- [ ] Verify it successfully pings your Railway backend

## ✅ **Phase 3: Update Frontend**

### **Step 3.1: Update Streamlit Configuration**
Create a `.streamlit/secrets.toml` file with your backend URL:

```toml
BACKEND_URL = "https://your-railway-url.railway.app"
```

### **Step 3.2: Update Hybrid App**
- [ ] Edit `streamlit_app_hybrid.py`
- [ ] Update the `BACKEND_URL` variable with your Railway URL
- [ ] Commit and push changes

### **Step 3.3: Test Frontend Connection**
- [ ] Run `streamlit run streamlit_app_hybrid.py` locally
- [ ] Check sidebar - should show "✅ Backend API Connected"
- [ ] Test a query in the Chat Interface tab

## ✅ **Phase 4: Data Processing (Optional)**

### **Step 4.1: Process ARGO Data**
If you want real data instead of mock data:

```bash
# Create synthetic test data
python download_argo_data.py

# Process data locally
python argo_data_processor.py

# Test the complete pipeline
python test_data_processing.py
```

### **Step 4.2: Upload Data to Railway**
- [ ] Your processed data will be in local PostgreSQL
- [ ] For production, you'd migrate this to Railway's PostgreSQL
- [ ] For now, the backend uses mock data which works great!

## ✅ **Phase 5: Final Testing**

### **Step 5.1: Test All Endpoints**
Visit your Railway backend URL and test:
- [ ] `https://your-url.railway.app/` - Should show API info
- [ ] `https://your-url.railway.app/health` - Should show healthy status
- [ ] `https://your-url.railway.app/docs` - Should show API documentation
- [ ] `https://your-url.railway.app/floats` - Should return mock float data
- [ ] `https://your-url.railway.app/statistics` - Should return system stats

### **Step 5.2: Test Frontend Integration**
- [ ] Your Streamlit app at `https://flowchat-ai.streamlit.app`
- [ ] Should show "✅ Backend API Connected" in sidebar
- [ ] Overview tab should show real statistics from backend
- [ ] Chat interface should work with natural language queries
- [ ] Map and profile tabs should display data from backend

### **Step 5.3: Test Keep-Alive System**
- [ ] Both GitHub Actions should run automatically
- [ ] Frontend stays awake (pinged every 10 hours)
- [ ] Backend stays awake (pinged every 25 minutes)
- [ ] Check Actions tab for successful runs

## 🎯 **Success Criteria**

Your deployment is successful when:
- ✅ Railway backend is live and responding to health checks
- ✅ Streamlit frontend connects to backend (shows connected status)
- ✅ Natural language queries work in chat interface
- ✅ Data visualizations load from backend API
- ✅ GitHub Actions keep both apps awake automatically
- ✅ Zero manual intervention required for 24/7 operation

## 🆘 **Troubleshooting**

### **Backend Issues:**
```bash
# Check Railway logs in dashboard
# Test health endpoint: curl https://your-url.railway.app/health
# Verify environment variables are set correctly
```

### **Frontend Issues:**
```bash
# Check Streamlit logs for connection errors
# Verify BACKEND_URL is correct in secrets.toml
# Test API endpoints manually in browser
```

### **GitHub Actions Issues:**
```bash
# Check Actions tab for error logs
# Verify URLs are correct in workflow files
# Test manual workflow runs
```

## 🎉 **You're Done!**

Once all checkboxes are complete, you'll have:
- 🌊 **Full-stack ARGO Float Dashboard** running 24/7
- 💰 **Zero cost** - within free tier limits
- 🤖 **Automated keep-alive** - no manual intervention needed
- 🔍 **AI-powered queries** - natural language data exploration
- 📊 **Professional visualizations** - government-grade interface
- 🚀 **Production-ready** - scalable and reliable

Your oceanographic data visualization platform is now live and ready for researchers worldwide! 🌊🚀