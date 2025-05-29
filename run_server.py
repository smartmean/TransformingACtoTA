import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Activity Diagram to UPPAAL Converter Server...")
    print("📁 Frontend available at: http://localhost:8000")
    print("🔗 API endpoint: http://localhost:8000/convert-xml")
    print("⚡ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        "Main_Beyone:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 