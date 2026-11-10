
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "rewards.json"

HEADERS = {
    "User-Agent": "VankataGaming/1.0"
}

def find_image(name):
    query = urllib.parse.urlencode({
        "name": name,
        "matchMethod": "full"
    })

    url = (
        "https://fortnite-api.com/v2/"
        "cosmetics/br/search?" + query
    )

    request = urllib.request.Request(
        url, headers=HEADERS
    )

    try:
        with urllib.request.urlopen(
            request, timeout=15
        ) as response:
            result = json.load(response)

        item = result.get("data", {})
        images = item.get("images", {})

        return (
            images.get("featured")
            or images.get("icon")
        )

    except Exception as error:
        print("Няма снимка за:", name, error)
        return None


def main():
    data = json.loads(
        FILE.read_text(encoding="utf-8")
    )

    for week in data.get("weeks", []):
        for reward in week.get("rewards", []):
            name = reward.get("name", "")

            if reward.get("image"):
                continue

            image = find_image(name)

            if image:
                reward["image"] = image
                print("Добавена снимка:", name)

    FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()

