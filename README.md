# BLACKPINK Telegram Bot — все видео и шортсы

Кидает в твой Telegram все новые видео и Shorts с 5 каналов:
- BLACKPINK (группа) — UCOmHUn--16B90oW2L6FRR3A
- JISOO, JENNIE, ROSÉ, LISA (соло-каналы)

Без YouTube API ключа — через RSS (`youtube.com/feeds/videos.xml`), без лимитов.

## Быстрый старт (3 шага)

1. Создай бота у @BotFather → получи `BOT_TOKEN`
2. Узнай свой `ADMIN_ID` → напиши @userinfobot в Telegram, он пришлёт твой ID
3. Запуск:

```bash
cd blackpink-bot
copy .env.example .env
# заполни BOT_TOKEN и ADMIN_ID в .env
pip install -r requirements.txt
python bot.py
```

## Команды бота

- `/start` — приветствие, подписка
- `/check` — проверить вручную прямо сейчас
- `/latest` — 5 последних видео (карусель)
- `/status` — сколько отправлено, когда последняя проверка

## Как работает

- Каждые 15 минут (CHECK_INTERVAL=900 сек) чекает RSS всех 5 каналов
- Сравнивает с `data/sent.json` — отправляет только новые `video_id`
- При первом запуске: запоминает всё существующее как "уже отправлено" + кидает 3 самых свежих как демо
- Шортсы определяются по `/shorts/` в ссылке и помечаются 🩷 Shorts

## Настройки (.env)

- `CHECK_INTERVAL` — интервал в секундах (600 = 10 мин, 1800 = 30 мин)
- `DATA_FILE` — куда писать отправленные ID

## Деплой 24/7

Для постоянной работы — залей на сервер/VPS или Render/Railway и держи `python bot.py` живым.

Локально на ноуте — просто держи окно открытым или запускай через `pythonw bot.py`.
