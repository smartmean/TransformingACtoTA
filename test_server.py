#!/usr/bin/env python3
"""
Simple test script to start the Pure OOP server
"""
import sys
import traceback

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        import fastapi
        print("✓ FastAPI imported")
        
        import uvicorn
        print("✓ Uvicorn imported")
        
        from Main_Pure_OOP import app
        print("✓ Main_Pure_OOP app imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def start_server():
    """Start the server"""
    try:
        import uvicorn
        from Main_Pure_OOP import app
        
        print("🚀 Starting Pure OOP Activity Diagram to Timed Automata Converter Server...")
        print("📁 Frontend available at: http://localhost:8001")
        print("🔗 API endpoint: http://localhost:8001/convert-xml")
        print("⚡ Press Ctrl+C to stop the server")
        print("-" * 50)
        
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        
    except Exception as e:
        print(f"❌ Server start error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print("-" * 50)
    
    if test_imports():
        print("All imports successful! Starting server...")
        start_server()
    else:
        print("Import test failed. Please check your dependencies.") 