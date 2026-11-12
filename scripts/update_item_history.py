
import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE = "https://itemshop.gg/api/v1"
KEY = os.environ.get("ITEMSHOP_API_KEY", "")

if not KEY:
    raise RuntimeError("ITEMSHOP_API_KEY is missing")

def get_json(path):
    url = BASE + path
    headers = {
        "Authorization": f"Bearer {KEY}",
        "User-Agent": "VANKATA-GAMING/1.0",
        "Accept": "application/json"
    }

    for attempt in range(4):
        try:
            request = urllib.request.Request(
                url, headers=headers
            )
            with urllib.request.urlopen(
                request, timeout=40
            ) as response:
                return json.load(response)

        except urllib.error.HTTPError as error:
            if error.code in (429, 503) and attempt < 3:
                delay = int(
                    error.headers.get("Retry-After", "5")
                )
                time.sleep(min(max(delay, 5), 60))
                continue
            raise

    raise RuntimeError("API request failed")

print("Loading Fortnite shop history...")

history = get_json("/history/fortnite")
dates = history.get("data", [])

if not isinstance(dates, list):
    raise RuntimeError("Invalid history response")

# Last 90 recorded shop rotations
dates = dates[:90]

items = {}

for number, day in enumerate(dates, 1):
    print(f"Processing {number}/{len(dates)}: {day}")

    response = get_json(
        "/history/fortnite/" + str(day)
    )

    data = response.get("data", {})
    shop = data.get("shop", data)

    if not isinstance(shop, dict):
        continue

    shop_date = (
        data.get("shopDate")
        or shop.get("shopDate")
        or day
    )

    for section in shop.get("sections", []):
        if section.get("upcoming"):
            continue

        for item in section.get("items", []):
            key = item.get("itemKey")
            if not key:
                continue

            price_data = item.get("price") or {}
            amount = price_data.get("amount")
            currency = price_data.get("currency")

            record = items.setdefault(key, {
                "name": item.get("name", ""),
                "itemKey": key,
                "lastAppearance": None,
                "price": None,
                "currency": None,
                "source": "itemshop.gg"
            })

            current_date = record["lastAppearance"]

            if (
                current_date is None
                or shop_date > current_date
            ):
                record["lastAppearance"] = shop_date
                record["price"] = amount
                record["currency"] = currency

    time.sleep(0.15)

output = {
    "updatedAt": datetime.now(
        timezone.utc
    ).isoformat(),
    "source": "https://itemshop.gg/fortnite",
    "scope": "Last 90 recorded rotations",
    "items": list(items.values())
}

with open(
    "item-history.json", "w", encoding="utf-8"
) as file:
    json.dump(
        output,
        file,
        ensure_ascii=False,
        separators=(",", ":")
    )

print(f"Saved {len(items)} item records.")

