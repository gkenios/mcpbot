import os
from dotenv import load_dotenv


load_dotenv()

ENV = os.getenv("ENV", "dev")
LOCAL = os.getenv("LOCAL", "true").lower() != "false"
PORT = os.getenv("PORT", 8000)

COMPANY = "Devoteam"
CONFIG_FILE = "mcpbot/config-local.yml" if LOCAL else "mcpbot/config-azure.yml"

CORS_ORIGINS = ["*"]

if not LOCAL:
    if ENV == "dev":
        HOST_URL = "https://dev.devoteam.nl/mcpbot"
    elif ENV == "prod":
        HOST_URL = "https://prod.devoteam.nl/mcpbot"
else:
    HOST_URL = "http://localhost:8000"
