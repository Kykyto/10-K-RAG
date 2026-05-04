import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))