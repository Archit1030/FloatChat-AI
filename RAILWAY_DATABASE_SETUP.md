# 🗄️ Railway PostgreSQL Setup Guide

## Step 1: Add PostgreSQL to Railway

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Open your project**: `FloatChat-AI`
3. **Add Database**:
   - Click **"New"** → **"Database"** → **"PostgreSQL"**
   - Railway will automatically provision a PostgreSQL instance
   - The `DATABASE_URL` environment variable will be set automatically

## Step 2: Get Database Connection URL

1. **In Railway Dashboard**:
   - Click on your **PostgreSQL service**
   - Go to **"Connect"** tab
   - Copy the **"Database URL"** (starts with `postgresql://`)

2. **Set Environment Variable** (for migration):
   ```bash
   # Windows PowerShell
   $env:RAILWAY_DATABASE_URL="postgresql://username:password@host:port/database"
   
   # Or create a .env file with:
   RAILWAY_DATABASE_URL=postgresql://username:password@host:port/database
   ```

## Step 3: Run Migration Script

```bash
# Make sure you're in the project directory
cd FloatChat-AI

# Run the migration
python migrate_to_railway.py
```

## Step 4: Verify Migration

The script will:
- ✅ Check your local ARGO data
- ✅ Connect to Railway PostgreSQL
- ✅ Create necessary tables
- ✅ Migrate all data (floats, profiles, measurements)
- ✅ Verify the migration

## Step 5: Test Railway API

After migration, test your Railway API:

```powershell
# Test with real data
Invoke-RestMethod -Uri "https://web-production-bbaf.up.railway.app/statistics" -Method Get

# Should now show real data counts instead of "no processed data"
```

## 🔧 Troubleshooting

### If migration fails:

1. **Check local data**:
   ```bash
   python -c "import config; print('Local DB:', config.DATABASE_URL)"
   ```

2. **Check Railway connection**:
   ```bash
   echo $env:RAILWAY_DATABASE_URL
   ```

3. **Verify local tables exist**:
   - Make sure you've run `python argo_data_processor.py` locally first
   - Check that floats, profiles, and measurements tables have data

### If Railway DATABASE_URL not set:

1. **Railway Dashboard** → **Your Service** → **Variables**
2. **Check if `DATABASE_URL` exists**
3. **If not, reconnect the PostgreSQL service**

## 📊 Expected Results

After successful migration:
- **Floats**: ~1,000 ARGO float records
- **Profiles**: ~10,000 profile records  
- **Measurements**: ~122,000+ measurement records
- **Date Range**: January 10-20, 2010
- **API Response**: Real oceanographic data instead of "no processed data"

## 🎯 Next Steps

1. ✅ Complete database migration
2. ✅ Test Railway API with real data
3. ✅ Update Streamlit app to use Railway backend
4. ✅ Deploy complete system

---

**Note**: The migration preserves all your processed ARGO data including temperature, salinity, depth measurements, and metadata.