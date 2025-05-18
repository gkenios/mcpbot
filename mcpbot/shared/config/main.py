import os
from dotenv import load_dotenv


load_dotenv()

ENV = os.getenv("ENV", "dev")
LOCAL = os.getenv("LOCAL", "true").lower() != "false"
PORT = os.getenv("PORT", 8000)

COMPANY = "Devoteam"
CONFIG_FILE = "mcpbot/config-local.yml" if LOCAL else "mcpbot/config-azure.yml"

CORS_ORIGINS = ["*"]
