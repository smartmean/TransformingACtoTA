"""
Configuration settings for the XML to UPPAAL Converter API
"""

import os
from typing import List

class Settings:
    """Application settings"""
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    
    # API Configuration
    API_TITLE: str = "XML to UPPAAL Converter"
    API_DESCRIPTION: str = "API สำหรับแปลง XML Activity Diagram เป็น UPPAAL format"
    API_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = ENV == "development"  # Auto-reload only in development
    LOG_LEVEL: str = "info"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]  # ใน production ควรระบุ domain ที่อนุญาต
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]
    
    # File Configuration
    UPLOAD_DIR: str = "uploads"
    RESULT_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "shared", "Result")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # XML Configuration
    SUPPORTED_XML_EXTENSIONS: List[str] = [".xml"]
    
    @classmethod
    def create_upload_dir(cls) -> None:
        """Create upload directory if it doesn't exist"""
        try:
            if not os.path.exists(cls.UPLOAD_DIR):
                os.makedirs(cls.UPLOAD_DIR)
        except Exception as e:
            print(f"Warning: Could not create upload directory: {e}")
    
    @classmethod
    def create_result_dir(cls) -> None:
        """Create result directory if it doesn't exist"""
        try:
            if not os.path.exists(cls.RESULT_DIR):
                os.makedirs(cls.RESULT_DIR)
        except Exception as e:
            print(f"Warning: Could not create result directory: {e}")

# Create directories on import
Settings.create_upload_dir()
Settings.create_result_dir() 