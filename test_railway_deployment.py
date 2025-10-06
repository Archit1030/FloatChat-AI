#!/usr/bin/env python3
"""
Test Railway deployment locally before pushing
"""

import os
import sys
import subprocess

def test_deployment():
    """Test the deployment configuration"""
    
    print("🧪 Testing Railway deployment configuration...")
    
    # Check required files
    required_files = [
        'main_real_data.py',
        'requirements.txt',
        'railway.json',
        'nixpacks.toml'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Test requirements installation
    print("\n📦 Testing requirements installation...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--dry-run', '-r', 'requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Requirements can be installed")
        else:
            print(f"❌ Requirements installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False
    
    # Test main app import
    print("\n🐍 Testing main app import...")
    try:
        import main_real_data
        print("✅ main_real_data.py imports successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Ready for Railway deployment.")
    return True

if __name__ == "__main__":
    if test_deployment():
        print("\n🚀 Next steps:")
        print("1. git add . && git commit -m 'Fix Railway deployment' && git push")
        print("2. Deploy on Railway.app")
        print("3. Add PostgreSQL database")
        print("4. Set environment variables")
    else:
        print("\n❌ Fix the issues above before deploying")
        sys.exit(1)