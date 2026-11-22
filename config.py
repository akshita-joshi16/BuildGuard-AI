
"""Central configuration for BuildGuard AI."""

from pathlib import Path

# Main project directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Project folders
MODEL_DIR = PROJECT_ROOT / "models"
DATABASE_DIR = PROJECT_ROOT / "database"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

IMAGE_OUTPUT_DIR = OUTPUT_DIR / "images"
VIDEO_OUTPUT_DIR = OUTPUT_DIR / "videos"
REPORT_OUTPUT_DIR = OUTPUT_DIR / "reports"

# AI model settings
MODEL_NAME = "best (1).pt"
MODEL_PATH = MODEL_DIR / MODEL_NAME
CONFIDENCE_THRESHOLD = 0.25

# Video analysis settings
VIDEO_FRAME_INTERVAL_SECONDS = 1
VIDEO_MAX_FRAMES = 120

# Application settings
APP_NAME = "BuildGuard AI"
APP_DESCRIPTION = "AI-Powered Construction Site Safety Monitoring"
