"""
Server startup script สำหรับ OOP-designed UPPAAL Converter
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting OOP-designed Activity Diagram to UPPAAL Converter Server...")
    print("📁 Frontend available at: http://localhost:8000")
    print("🔗 API endpoint: http://localhost:8000/convert-xml")
    print("⚡ Press Ctrl+C to stop the server")
    print("🔧 Using improved OOP architecture")
    print("-" * 50)
    
    uvicorn.run(
        "Main_Beyone_OOP:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["*.py"],
        reload_excludes=[
            "ฺBackup/*",
            "Backup/*", 
            "Main_B*.py",
            "Main.py",
            "Main_Beyone.py",
            "Main_Beyone copy.py",
            "main_B.py",
            "find_join_node.py",
            "Result/*",
            "Example_XML/*",
            "__pycache__/*"
        ]
    ) 