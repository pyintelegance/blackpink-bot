import json
import os

def load_sent(path: str) -> set:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("sent_ids", []))
    except Exception:
        return set()

def save_sent(path: str, sent_ids: set):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"sent_ids": sorted(list(sent_ids))}, f, ensure_ascii=False, indent=2)

def filter_new(videos: list[dict], sent_ids: set) -> list[dict]:
    """Возвращает только те видео, которых ещё не отправляли."""
    new = []
    for v in videos:
        vid = v.get("video_id")
        if vid and vid not in sent_ids:
            new.append(v)
    return new
