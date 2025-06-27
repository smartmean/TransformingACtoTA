from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes.api import router
from .config import Settings
import uvicorn
import os

# Create FastAPI app instance
app = FastAPI(
    title=Settings.API_TITLE,
    description=Settings.API_DESCRIPTION,
    version=Settings.API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.ALLOWED_ORIGINS,
    allow_credentials=Settings.ALLOW_CREDENTIALS,
    allow_methods=Settings.ALLOW_METHODS,
    allow_headers=Settings.ALLOW_HEADERS,
)

# Serve static files from frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Include routes
app.include_router(router)

def start_server():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting FastAPI server...")
        print(f"📱 Open your browser and go to: http://{Settings.HOST}:{Settings.PORT}/")
        print(f"📚 API Documentation: http://{Settings.HOST}:{Settings.PORT}/docs")
        print(f"🔄 Auto-reload: {'Enabled' if Settings.RELOAD else 'Disabled'}")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # รันเซิร์ฟเวอร์
        uvicorn.run(
            "backend.app.main:app",
            host=Settings.HOST,
            port=Settings.PORT,
            reload=Settings.RELOAD,
            log_level=Settings.LOG_LEVEL,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_server() 