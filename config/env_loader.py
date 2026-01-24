"""
Load environment variables from .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
