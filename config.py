import os
from dotenv import load_dotenv

load_dotenv()

_base = os.path.dirname(os.path.abspath(__file__))

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# ADMIN_ID: берём из ENV, если 0 — fallback на ID Жахангира (773870189) + last_chat.txt
# Это делает деплой на Render рабочим без ручной настройки ENV (фикс 07.09.2026)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
if ADMIN_ID == 0:
    # пробуем last_chat.txt (авто-сохранение при /start)
    try:
        _p = os.path.join(_base, "data", "last_chat.txt")
        with open(_p, "r", encoding="utf-8") as f:
            ADMIN_ID = int(f.readline().strip() or 0)
    except Exception:
        pass
if ADMIN_ID == 0:
    ADMIN_ID = 773870189  # Jahongir @jahongir_lab — хардкод fallback для Render
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "900"))  # 15 минут по умолчанию
# DATA_FILE абсолютный — чтобы работало из любого cwd (автозапуск/Render)
DATA_FILE = os.getenv("DATA_FILE", os.path.join(_base, "data", "sent.json"))
# если в ENV относительный путь — делаем абсолютным
if not os.path.isabs(DATA_FILE):
    DATA_FILE = os.path.join(_base, DATA_FILE)
