"""One-shot cron for GitHub Actions — fetches YouTube RSS and sends new videos via Bot API.
Persist sent.json via git commit (done in workflow).
"""
import os, json, requests
from datetime import datetime
import config
from fetcher import fetch_all
from storage import load_sent, save_sent, filter_new

BOT_TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
DATA_FILE = config.DATA_FILE

def send_video(v, chat_id):
    kind = "🩷 Shorts" if v["is_short"] else "🎬 Видео"
    title = v["title"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    channel = v["channel_label"]
    date = v["published_str"] or ""
    text = f"{kind} | <b>{channel}</b>\n<b>{title}</b>\n{date}\n{v['link']}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto" if v.get("thumbnail") else f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        if v.get("thumbnail"):
            r = requests.post(url, data={"chat_id": chat_id, "photo": v["thumbnail"], "caption": text, "parse_mode": "HTML"}, timeout=15)
            if r.status_code != 200:
                raise Exception(r.text[:500])
        else:
            r = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False}, timeout=15)
            if r.status_code != 200:
                raise Exception(r.text[:500])
        print(f"sent {v['video_id']} to {chat_id}")
    except Exception as e:
        print(f"send failed {v['video_id']}: {e}")
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
        except Exception as e2:
            print(f"fallback also failed: {e2}")

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return
    if not ADMIN_ID:
        print("ADMIN_ID missing")
        return
    sent_ids = load_sent(DATA_FILE)
    print(f"loaded sent_ids={len(sent_ids)}")
    videos = fetch_all(15)
    print(f"fetched {len(videos)} videos")
    new_videos = filter_new(videos, sent_ids)
    print(f"new_videos={len(new_videos)}")
    if not new_videos:
        # still save any new ids that appeared? keep in sync
        for v in videos:
            sent_ids.add(v["video_id"])
        save_sent(DATA_FILE, sent_ids)
        print("no new, updated sent.json")
        return
    # initial run: if sent empty, send 3 demo only
    if len(sent_ids) == 0 and len(new_videos) >= 3:
        demo = new_videos[:3]
        demo.sort(key=lambda x: x["published"] or datetime.min)
        for v in demo:
            send_video(v, ADMIN_ID)
        for v in videos:
            sent_ids.add(v["video_id"])
        save_sent(DATA_FILE, sent_ids)
        print(f"initial demo sent {len(demo)}")
        return
    new_videos.sort(key=lambda x: x["published"] or datetime.min)
    for v in new_videos:
        send_video(v, ADMIN_ID)
        sent_ids.add(v["video_id"])
        import time; time.sleep(1.2)
    save_sent(DATA_FILE, sent_ids)
    print(f"sent {len(new_videos)} new")

if __name__ == "__main__":
    main()
