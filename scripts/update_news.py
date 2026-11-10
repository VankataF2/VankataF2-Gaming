
import json
import os
import re
from datetime import datetime, timezone
from html import unescape

import requests

API_URL = "https://fortnite-api.com/v2/news"
OUTPUT = "news.json"


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def translate(text):
    if not text:
        return ""
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:450], "langpair": "en|bg"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("responseStatus") == 200:
            return data["responseData"]["translatedText"]
    except (requests.RequestException, ValueError, KeyError):
        pass
    return text


def main():
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != 200:
        raise RuntimeError("Fortnite API върна грешка.")

    data = payload.get("data", {})
    entries = []

    for section in ("br", "stw", "creative"):
        section_data = data.get(section) or {}
        for item in section_data.get("motds") or []:
            entries.append(item)

    if not entries:
        raise RuntimeError("Няма налични Fortnite новини.")

    existing = []
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as file:
            existing = json.load(file)

    known = {item["id"] for item in existing}
    new_items = []

    for item in entries:
        title = clean(item.get("title"))
        description = clean(item.get("body"))
        identifier = str(
            item.get("id") or (title + description)
        )

        if identifier in known:
            continue

        image = item.get("image")
        if isinstance(image, dict):
            image = image.get("url") or image.get("background")

        new_items.append({
            "id": identifier,
            "title": translate(title),
            "description": translate(description),
            "image": image or "",
            "source": "Fortnite",
            "url": "https://www.fortnite.com/news",
            "added": datetime.now(timezone.utc).isoformat()
        })
        known.add(identifier)

    result = (new_items + existing)[:100]

    with open(OUTPUT, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print(f"Добавени новини: {len(new_items)}")


if __name__ == "__main__":
    main()
