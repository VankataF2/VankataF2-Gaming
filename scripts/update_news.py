import json
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

import feedparser
import requests

FEED_URL = os.getenv("HYPEX_RSS_URL", "https://nitter.net/HYPEX/rss")
OUTPUT = "news.json"


def translate(text):
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:450], "langpair": "en|bg"},
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("responseData", {}).get("translatedText") or text
    except Exception:
        return text


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def main():
    response = requests.get(
        FEED_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=25,
    )
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    if not feed.entries:
        raise RuntimeError("RSS източникът не върна публикации.")

    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT, "r", encoding="utf-8") as file:
            existing = json.load(file)

    known = {item["id"] for item in existing}
    new_items = []

    for entry in feed.entries[:20]:
        link = entry.get("link", "")
        identifier = entry.get("id", link)
        if not identifier or identifier in known:
            continue

        title = clean(entry.get("title", "Fortnite новина"))
        description = clean(entry.get("summary", title))
        published = entry.get("published", "")

        new_items.append({
            "id": identifier,
            "title": translate(title),
            "description": translate(description[:450]),
            "source": "HYPEX",
            "url": link,
            "published": published,
            "added": datetime.now(timezone.utc).isoformat(),
        })
        known.add(identifier)

    all_items = (new_items + existing)[:100]
    with open(OUTPUT, "w", encoding="utf-8") as file:
        json.dump(all_items, file, ensure_ascii=False, indent=2)

    print(f"Добавени новини: {len(new_items)}")


if __name__ == "__main__":
    main()

