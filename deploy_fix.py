#!/usr/bin/env python3
"""
Quick deployment fix for Railway
Commits and pushes the fixes for the healthcheck failure
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {cmd}")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {cmd}")
        print(f"   Error: {e.stderr.strip()}")
        return False

def main():
    print("🚀 Deploying Railway fixes...")
    
    # Add all changes
    if not run_command("git add ."):
        sys.exit(1)
    
    # Commit changes
    commit_msg = "Fix Railway deployment: Add missing dependencies and robust error handling"
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("ℹ️ No changes to commit or commit failed")
    
    # Push to main branch
    if not run_command("git push origin main"):
        sys.exit(1)
    
    print("\n🎉 Deployment fixes pushed to Railway!")
    print("\n📋 What was fixed:")
    print("   ✅ Added chromadb to requirements-production.txt")
    print("   ✅ Made imports more robust with proper error handling")
    print("   ✅ Simplified Dockerfile startup command")
    print("   ✅ Added fallback configuration for missing environment variables")
    print("\n⏳ Railway will automatically redeploy. Check your dashboard in 2-3 minutes.")
    print("🔗 Your app should be available at: https://your-app.railway.app/health")

if __name__ == "__main__":
    main()