
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


def get_shop_date(data, shop, fallback):
    return str(
        data.get("shopDate")
        or shop.get("shopDate")
        or fallback
    )


def get_price(item):
    price_data = item.get("price") or {}

    if not isinstance(price_data, dict):
        return None, None

    return (
        price_data.get("amount"),
        price_data.get("currency")
    )


print("Loading Fortnite shop history...")

history = get_json("/history/fortnite")
dates = history.get("data", [])

if not isinstance(dates, list):
    raise RuntimeError("Invalid history response")

# Запазваме обхвата от 90 ротации.
# Това не е пълният архив за всички години.
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

    shop_date = get_shop_date(data, shop, day)

    for section in shop.get("sections", []):
        if section.get("upcoming"):
            continue

        for item in section.get("items", []):
            key = item.get("itemKey")

            if not key:
                continue

            price, currency = get_price(item)

            record = items.setdefault(key, {
                "name": item.get("name", ""),
                "itemKey": key,
                "lastAppearance": None,
                "price": None,
                "currency": None,
                "appearances": [],
                "source": "itemshop.gg"
            })

            # Не дублираме появите в един и същи ден.
            existing = next(
                (
                    appearance
                    for appearance in record["appearances"]
                    if appearance["date"] == shop_date
                ),
                None
            )

            if existing is None:
                record["appearances"].append({
                    "date": shop_date,
                    "price": price,
                    "currency": currency
                })
            elif existing["price"] is None and price is not None:
                existing["price"] = price
                existing["currency"] = currency

    time.sleep(0.15)


for record in items.values():
    record["appearances"].sort(
        key=lambda appearance: appearance["date"],
        reverse=True
    )

    if record["appearances"]:
        latest = record["appearances"][0]

        record["lastAppearance"] = latest["date"]
        record["price"] = latest["price"]
        record["currency"] = latest["currency"]


output = {
    "updatedAt": datetime.now(
        timezone.utc
    ).isoformat(),
    "source": "https://itemshop.gg/fortnite",
    "scope": "Last 90 recorded rotations",
    "items": list(items.values())
}

with open(
    "item-history.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        output,
        file,
        ensure_ascii=False,
        separators=(",", ":")
    )

print(f"Saved {len(items)} item records.")
print(
    "Saved appearances:",
    sum(
        len(item["appearances"])
        for item in items.values()
    )
)
