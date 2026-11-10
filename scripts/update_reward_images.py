
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "rewards.json"

API = "https://fortnite-api.com/v2/cosmetics/br/search"

# Алтернативни имена само когато са известни.
# Не използваме приблизителни съвпадения.
ALIASES = {
    "London": ["London"],
    "Cadillac CT5-V Blackwing": [
        "Cadillac CT5-V Blackwing"
    ],
    "Pirate Shop Access": [
        "Pirate Shop Access"
    ],
    "Extraction Accelerator": [
        "Extraction Accelerator"
    ],
    "Portable Extractor": [
        "Portable Extractor"
    ],
    "Golden Firework": [
        "Golden Firework"
    ],
    "Sprite Locator": [
        "Sprite Locator"
    ],
    "Lucky Locator": [
        "Lucky Locator"
    ]
}


def find_image(name):
    names = ALIASES.get(name, [name])

    for search_name in names:
        params = urllib.parse.urlencode({
            "name": search_name,
            "matchMethod": "full"
        })

        request = urllib.request.Request(
            API + "?" + params,
            headers={
                "User-Agent": "VankataGaming/1.0"
            }
        )

        try:
            with urllib.request.urlopen(
                request, timeout=15
            ) as response:
                result = json.load(response)

            item = result.get("data", {})

            if item.get("name", "").casefold() != (
                search_name.casefold()
            ):
                continue

            images = item.get("images") or {}

            image = (
                images.get("featured")
                or images.get("icon")
            )

            if image and image.startswith("https://"):
                return image

        except Exception as error:
            print("Не е намерено:", search_name, error)

    return None


def main():
    data = json.loads(
        FILE.read_text(encoding="utf-8")
    )

    added = 0
    missing = []

    for week in data.get("weeks", []):
        for reward in week.get("rewards", []):
            if reward.get("image"):
                continue

            name = reward.get("name", "")
            image = find_image(name)

            if image:
                reward["image"] = image
                added += 1
                print("Снимка:", name)
            else:
                missing.append(name)

    FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print("Добавени снимки:", added)

    if missing:
        print("Все още без снимки:")
        for name in missing:
            print("-", name)


if __name__ == "__main__":
    main()
