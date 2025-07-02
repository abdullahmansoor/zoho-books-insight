# zoho_app/utils/env.py
import os
from pathlib import Path
from dotenv import load_dotenv

def load_project_env():
    """Load .env from the top-level project root."""
    root = Path(__file__).resolve().parents[3]  # go up to project root
    env_path = root / ".env"
    print(f"Loading environment variables from: {env_path}")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        raise FileNotFoundError(f"No .env file found at {env_path}")
