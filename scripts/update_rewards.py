
import json
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "leaks.json"

SOURCES = [
    {
        "name": "Fortnite News",
        "url": "https://fortnitenews.com/rss/",
        "type": "news"
    },
    {
        "name": "Fortnite Datamining",
        "url": (
            "https://raw.githubusercontent.com/"
            "Fortnite-Datamining/Fortnite-Datamining/"
            "main/feed.xml"
        ),
        "type": "datamining"
    }
]

KEYWORDS = (
    "leak", "rumor", "rumour", "upcoming",
    "unreleased", "datamin", "reward",
    "skin", "cosmetic", "outfit", "gold",
    "pirate", "weekly", "collab",
    "new", "added", "coming"
)


def fetch_feed(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "VankataGaming/1.0"}
    )

    with urllib.request.urlopen(
        request, timeout=20
    ) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    results = []

    for item in root.findall(".//channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        date = (item.findtext("pubDate") or "").strip()
        guid = (item.findtext("guid") or link).strip()

        if not title or not link.startswith("https://"):
            continue

        if source["type"] == "news":
            if not any(
                word in title.lower()
                for word in KEYWORDS
            ):
                continue

        # Datamining показва открити промени,
        # а не непременно бъдещи награди.
        label = (
            "Открита промяна в играта"
            if source["type"] == "datamining"
            else "Неофициална публикация"
        )

        identifier = hashlib.sha256(
            (source["name"] + guid).encode("utf-8")
        ).hexdigest()[:16]

        results.append({
            "id": identifier,
            "title": title,
            "source": source["name"],
            "url": link,
            "date": date,
            "type": source["type"],
            "label": label,
            "verified": False
        })

    return results


def main():
    old_items = []

    if OUTPUT.exists():
        try:
            old_data = json.loads(
                OUTPUT.read_text(encoding="utf-8")
            )
            old_items = old_data.get("items", [])
        except (ValueError, OSError):
            pass

    collected = []
    successful = 0

    for source in SOURCES:
        try:
            items = fetch_feed(source)
            collected.extend(items)
            successful += 1
            print(
                source["name"],
                "намерени:",
                len(items)
            )
        except Exception as error:
            print(
                "Грешка при",
                source["name"],
                str(error)
            )

    if successful == 0:
        raise RuntimeError(
            "Нито един RSS източник не отговори."
        )

    # Запазваме и старите публикации.
    unique = {}

    for item in old_items + collected:
        unique[item["id"]] = item

    items = list(unique.values())[-200:]

    output = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "items": items
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print("Общо запазени публикации:", len(items))


if __name__ == "__main__":
    main()
