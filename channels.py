# Источники — те же что в kpopsite/app/seed.py
# Каждый канал проверяется через YouTube RSS: https://www.youtube.com/feeds/videos.xml?channel_id=ID
# Без YouTube API ключа, без лимитов.

CHANNELS = [
    {
        "id": "UCOmHUn--16B90oW2L6FRR3A",
        "name": "BLACKPINK",
        "label": "BLACKPINK (группа)",
        "type": "group",
    },
    {
        "id": "UCRE-097LGtx_Zo7LrHvkycA",
        "name": "JISOO",
        "label": "JISOO",
        "type": "member",
        "group": "BLACKPINK",
    },
    {
        "id": "UCNYi_zGmR519r5gYdOKLTjQ",
        "name": "JENNIE",
        "label": "JENNIE",
        "type": "member",
        "group": "BLACKPINK",
    },
    {
        "id": "UCBo1hnzxV9rz3WVsv__Rn1g",
        "name": "ROSÉ",
        "label": "ROSÉ",
        "type": "member",
        "group": "BLACKPINK",
    },
    {
        "id": "UC6-BgjsBa5R3PZQ_kZ8hKPg",
        "name": "LISA",
        "label": "LISA",
        "type": "member",
        "group": "BLACKPINK",
    },
]

def rss_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
