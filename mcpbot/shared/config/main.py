import os
from dotenv import load_dotenv


load_dotenv(override=True)

ENV = os.getenv("ENV", "dev")
LOCAL = os.getenv("LOCAL", "true").lower() != "false"
PORT = os.getenv("PORT", 8000)
HOST_URL = os.environ["HOST_URL"] if not LOCAL else "http://localhost:8000"

CONFIG_FILE = "mcpbot/config-local.yml" if LOCAL else "mcpbot/config-azure.yml"
COMPANY = "Devoteam"

CORS_ORIGINS = ["*"]
