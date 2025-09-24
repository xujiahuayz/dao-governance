"""Settings and configuration."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
KAIKO_API_KEY = os.environ.get("KAIKO_API_KEY")
TALLY_API_KEY = os.environ.get("TALLY_API_KEY")
SNAPSHOT_API_KEY = os.environ.get("SNAPSHOT_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = os.environ.get("HEADERS")
