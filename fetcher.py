import feedparser
from datetime import datetime
from channels import CHANNELS, rss_url

def parse_entry(entry) -> dict:
    link = entry.link
    # video_id из link
    video_id = None
    if "v=" in link:
        video_id = link.split("v=")[-1].split("&")[0]
    elif "/shorts/" in link:
        video_id = link.split("/shorts/")[-1].split("?")[0].split("/")[0]
    else:
        video_id = link.split("/")[-1]

    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            published = datetime(*entry.published_parsed[:6])
        except Exception:
            published = None

    thumbnail = ""
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        thumbnail = entry.media_thumbnail[0].get("url", "")
    # fallback — yt thumbnail
    if not thumbnail and video_id:
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    is_short = "/shorts/" in link

    return {
        "video_id": video_id,
        "title": entry.title,
        "link": link,
        "url": link,
        "published": published,
        "published_str": published.strftime("%Y-%m-%d %H:%M") if published else "",
        "thumbnail": thumbnail,
        "is_short": is_short,
        "description": entry.get("summary", "")[:500],
    }

def fetch_channel(channel: dict, limit: int = 20) -> list[dict]:
    feed = feedparser.parse(rss_url(channel["id"]))
    items = []
    for entry in feed.entries[:limit]:
        data = parse_entry(entry)
        data["channel"] = channel["name"]
        data["channel_label"] = channel["label"]
        data["channel_id"] = channel["id"]
        data["channel_type"] = channel["type"]
        items.append(data)
    return items

def fetch_all(limit_per_channel: int = 15) -> list[dict]:
    all_items = []
    for ch in CHANNELS:
        try:
            items = fetch_channel(ch, limit=limit_per_channel)
            all_items.extend(items)
        except Exception as e:
            print(f"[fetcher] {ch['name']} error: {e}")
    # сортируем по дате (новые первыми), если даты нет — в конец
    all_items.sort(key=lambda x: x["published"] or datetime.min, reverse=True)
    return all_items

if __name__ == "__main__":
    videos = fetch_all()
    print(f"Найдено видео: {len(videos)}")
    for v in videos[:10]:
        tag = "SHORT" if v["is_short"] else "VIDEO"
        print(f"[{tag}] {v['channel_label']}: {v['title']} | {v['link']} | {v['published_str']}")
