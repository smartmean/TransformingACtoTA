"""
Server startup script สำหรับ Pure OOP Activity Diagram to Timed Automata Converter
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Pure OOP Activity Diagram to Timed Automata Converter Server...")
    print("📁 Frontend available at: http://localhost:8001")
    print("🔗 API endpoint: http://localhost:8001/convert-xml")
    print("⚡ Press Ctrl+C to stop the server")
    print("🔧 Using Pure OOP architecture with infrastructure components")
    print("-" * 50)
    
    uvicorn.run("Main_Pure_OOP:app", host="0.0.0.0", port=8001, reload=True) 