import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "900"))  # 15 минут по умолчанию
DATA_FILE = os.getenv("DATA_FILE", "data/sent.json")
