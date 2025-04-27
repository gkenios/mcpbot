import os


COMPANY = "Devoteam"

ENV = os.getenv("ENV", "dev")
LOCAL = os.getenv("LOCAL", "true").lower() != "false"
PORT = os.getenv("PORT", 8080)

if LOCAL:
    from dotenv import load_dotenv

    load_dotenv()
    CONFIG_FILE = "mcpbot/config-local.yml"
else:
    CONFIG_FILE = "mcpbot/config-azure.yml"
