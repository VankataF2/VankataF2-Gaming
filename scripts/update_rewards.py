
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REWARDS_FILE = ROOT / "rewards.json"

# Потвърдени базови шансове за нормален мач.
# Това са шансове по КАТЕГОРИИ, не за произволен скин.
ODDS = {
    "gold_outfit": 1562500,
    "pirate_shop": 137500,
    "vehicle": 7813,
    "pickaxe_backbling": 568,
    "jam_track": 391,
    "loading_screen": 272,
    "gizmo": 127
}

# Категориите не се сменят автоматично по календар.
# Новите конкретни награди трябва първо да бъдат
# потвърдени и добавени в rewards.json.

def main():
    if not REWARDS_FILE.exists():
        raise FileNotFoundError(
            "Липсва rewards.json в главната папка."
        )

    with REWARDS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data.get("weeks"), list):
        raise ValueError("Липсва списъкът weeks.")

    current_week = data.get("current_week")

    for week in data["weeks"]:
        week["status"] = (
            "current"
            if week.get("week") == current_week
            else "archive"
        )

        for reward in week.get("rewards", []):
            # Попълваме шанс само при изрично
            # зададена проверена категория.
            category_key = reward.get("odds_category")

            if category_key in ODDS:
                reward["chance"] = ODDS[category_key]
                reward["verified"] = True

                reward.setdefault(
                    "source",
                    "https://x.com/FortniteStatus"
                )

            # Не превръщаме примерни награди
            # в потвърдени автоматично.

    data["updated_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    with REWARDS_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )
        file.write("\n")

    print("Rewards JSON е проверен и обновен.")
    print("Седмици:", len(data["weeks"]))
    print("Текуща седмица:", current_week)


if __name__ == "__main__":
    main()

