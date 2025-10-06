#!/bin/bash
# Railway Deployment Script

echo "🚀 Preparing Railway deployment..."

# Ensure we're using the backend requirements
echo "📦 Backend requirements file:"
cat requirements_backend.txt

echo ""
echo "🔧 Railway configuration:"
cat railway.json

echo ""
echo "⚙️ Nixpacks configuration:"
cat nixpacks.toml

echo ""
echo "✅ Ready for Railway deployment!"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git add . && git commit -m 'Fix Railway deployment' && git push"
echo "2. Deploy on Railway.app from GitHub repo"
echo "3. Add PostgreSQL database in Railway dashboard"
echo "4. Set environment variables: CHROMA_PATH=/tmp/chroma_db, VECTOR_STORE=persistent"