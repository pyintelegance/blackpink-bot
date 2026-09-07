"""
BLACKPINK Telegram Bot — кидает все новые видео и шортсы группы и участниц.

Команды:
 /start   — приветствие + подписка
 /check   — проверить сейчас (вручную)
 /latest  — показать 5 последних видео
 /status  — сколько отслеживается каналов и когда последняя проверка
"""

import asyncio
import logging
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, BotCommand

import config
from channels import CHANNELS
from fetcher import fetch_all
from storage import load_sent, save_sent, filter_new

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("blackpink-bot")

# Health server для Render Web Service (free план требует порт)
def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                import json as _json
                # диагностический JSON для проверки Render без дашборда
                payload = {
                    "status": "alive",
                    "admin_id": getattr(config, "ADMIN_ID", 0),
                    "sent_count": len(sent_ids),
                    "last_check": last_check.isoformat() if last_check else None,
                    "check_interval": getattr(config, "CHECK_INTERVAL", 0),
                }
                body = _json.dumps(payload, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"blackpink-bot alive")
        def log_message(self, format, *args):
            return
    try:
        srv = HTTPServer(("0.0.0.0", port), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        log.info(f"Health server on {port}")
    except Exception as e:
        log.warning(f"health server failed: {e}")

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

sent_ids = set()
last_check: datetime | None = None
is_checking = False

def format_message(v: dict) -> str:
    kind = "🩷 Shorts" if v["is_short"] else "🎬 Видео"
    # Экранируем немного для HTML
    title = v["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    channel = v["channel_label"]
    date = v["published_str"] or ""
    return (
        f"{kind} | <b>{channel}</b>\n"
        f"<b>{title}</b>\n"
        f"{date}\n"
        f"{v['link']}"
    )

async def send_video(v: dict, chat_id: int):
    text = format_message(v)
    try:
        # Пытаемся отправить как фото с подписью (красивее)
        if v.get("thumbnail"):
            await bot.send_photo(chat_id=chat_id, photo=v["thumbnail"], caption=text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=False)
    except Exception as e:
        # fallback: просто текст
        log.warning(f"send_photo failed {v['video_id']}: {e}, fallback to text")
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        except Exception as e2:
            log.error(f"send_message also failed: {e2}")

async def check_and_notify(chat_id: int | None = None, initial: bool = False) -> int:
    """Проверяет RSS, находит новые видео, отправляет в Telegram. Возвращает кол-во новых."""
    global sent_ids, last_check, is_checking
    if is_checking:
        return 0
    is_checking = True
    try:
        target = chat_id or config.ADMIN_ID
        if not target:
            log.warning("ADMIN_ID не задан — некуда отправлять")
            return 0

        videos = await asyncio.to_thread(fetch_all, 15)
        new_videos = filter_new(videos, sent_ids)

        if initial:
            # При первом запуске — НЕ спамим старыми видео, просто запоминаем их как отправленные
            # Но если база пустая — отправим 3 самых свежих как демо
            if not sent_ids and new_videos:
                demo = new_videos[:3]
                for v in reversed(demo):  # от старых к новым
                    await send_video(v, target)
                    await asyncio.sleep(1)
                for v in videos:
                    sent_ids.add(v["video_id"])
                save_sent(config.DATA_FILE, sent_ids)
                last_check = datetime.now()
                return len(demo)
            elif not sent_ids:
                for v in videos:
                    sent_ids.add(v["video_id"])
                save_sent(config.DATA_FILE, sent_ids)
                last_check = datetime.now()
                return 0
            elif not new_videos:
                # база есть, новых нет — просто обновляем время
                for v in videos:
                    sent_ids.add(v["video_id"])
                save_sent(config.DATA_FILE, sent_ids)
                last_check = datetime.now()
                return 0
            # если база есть И есть новые видео — НЕ глотаем, идём дальше к обычной отправке

        if not new_videos:
            last_check = datetime.now()
            return 0

        # Сортируем от старых к новым, чтобы приходили по порядку
        new_videos.sort(key=lambda x: x["published"] or datetime.min)

        for v in new_videos:
            await send_video(v, target)
            sent_ids.add(v["video_id"])
            await asyncio.sleep(1.2)  # анти-спам пауза

        save_sent(config.DATA_FILE, sent_ids)
        last_check = datetime.now()
        log.info(f"Отправлено {len(new_videos)} новых видео")
        return len(new_videos)
    finally:
        is_checking = False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Авто-фиксация ADMIN_ID при первом запуске (если 0) — сохраняем твой ID
    if config.ADMIN_ID == 0:
        try:
            with open("data/last_chat.txt", "w", encoding="utf-8") as f:
                f.write(f"{message.from_user.id}\n{message.chat.id}\n{message.from_user.username or ''}\n")
            # также сразу обновляем .env для следующего рестарта
            import re
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    env = f.read()
                env = re.sub(r"ADMIN_ID=.*", f"ADMIN_ID={message.from_user.id}", env)
                with open(".env", "w", encoding="utf-8") as f:
                    f.write(env)
                config.ADMIN_ID = message.from_user.id
                log.info(f"AUTO ADMIN_ID set to {message.from_user.id}")
            except Exception as e:
                log.warning(f"auto .env update failed: {e}")
        except Exception as e:
            log.warning(f"save last_chat failed: {e}")

    # Разрешаем только владельцу (если ADMIN_ID задан), иначе — любому
    if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ Этот бот приватный. Доступ только для владельца.")
        return
    await message.answer(
        "🩷 <b>BLACKPINK Bot</b> на связи!\n\n"
        "Я отслеживаю 5 каналов:\n"
        "• BLACKPINK (группа)\n"
        "• JISOO • JENNIE • ROSÉ • LISA\n\n"
        "Кидаю сюда <b>все новые видео и шортсы</b> — автоматом.\n\n"
        "Команды:\n"
        "/check — проверить сейчас\n"
        "/latest — 5 последних видео\n"
        "/status — статус бота",
        parse_mode="HTML"
    )
    # Сразу чекаем
    await message.answer("🔍 Проверяю сейчас...")
    count = await check_and_notify(chat_id=message.chat.id)
    if count == 0:
        await message.answer("✅ Новых видео пока нет. Я на страже — как только выйдет, сразу кину!")
    else:
        await message.answer(f"✅ Нашёл и отправил {count} новых!")

@dp.message(Command("check"))
async def cmd_check(message: Message):
    if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
        return
    await message.answer("🔍 Проверяю YouTube...")
    count = await check_and_notify(chat_id=message.chat.id)
    if count == 0:
        await message.answer("✅ Новых видео нет — всё уже у тебя.")
    else:
        await message.answer(f"🔥 Отправил {count} новых!")

@dp.message(Command("latest"))
async def cmd_latest(message: Message):
    if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
        return
    videos = await asyncio.to_thread(fetch_all, 5)
    if not videos:
        await message.answer("Пока пусто.")
        return
    for v in videos[:5]:
        await send_video(v, message.chat.id)
        await asyncio.sleep(0.8)

@dp.message(Command("status"))
async def cmd_status(message: Message):
    if config.ADMIN_ID and message.from_user.id != config.ADMIN_ID:
        return
    lc = last_check.strftime("%Y-%m-%d %H:%M:%S") if last_check else "ещё не проверяли"
    await message.answer(
        f"📊 <b>Статус</b>\n"
        f"Каналов: {len(CHANNELS)}\n"
        f"Отправлено всего: {len(sent_ids)}\n"
        f"Последняя проверка: {lc}\n"
        f"Интервал: {config.CHECK_INTERVAL // 60} мин",
        parse_mode="HTML"
    )

async def background_loop():
    await asyncio.sleep(5)  # дать боту стартануть
    # Первая инициализация — запоминаем существующие как отправленные + шлём 3 демо если первый запуск
    await check_and_notify(initial=True)
    while True:
        await asyncio.sleep(config.CHECK_INTERVAL)
        try:
            await check_and_notify()
        except Exception as e:
            log.error(f"background check error: {e}")

async def main():
    global sent_ids
    start_health_server()
    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN не задан! Заполни .env (скопируй из .env.example)")
        return
    if not config.ADMIN_ID:
        print("⚠️ ADMIN_ID не задан — бот будет отвечать всем. Рекомендую указать свой Telegram ID.")

    # Кнопка Меню рядом со скрепкой — команды бота (твой фидбэк 06.09.2026)
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🩷 Запустить бота"),
            BotCommand(command="check", description="🔍 Проверить сейчас"),
            BotCommand(command="latest", description="🎬 5 последних видео"),
            BotCommand(command="status", description="📊 Статус бота"),
        ])
        log.info("Menu commands set ✓")
    except Exception as e:
        log.warning(f"set_my_commands failed: {e}")

    sent_ids = load_sent(config.DATA_FILE)
    log.info(f"Загружено sent_ids: {len(sent_ids)}, интервал {config.CHECK_INTERVAL}s")

    asyncio.create_task(background_loop())
    log.info("Бот запущен. Жду команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
