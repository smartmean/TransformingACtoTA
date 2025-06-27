#!/usr/bin/env python3
"""
Run script for XML to UPPAAL Converter
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.main import start_server

if __name__ == "__main__":
    start_server() 