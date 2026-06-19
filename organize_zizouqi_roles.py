from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path


INDEX_PATH = Path("autochess_dump/zizouqi_card_image_index.json")
OUT_DIR = Path("autochess_dump/organized_roles")

RESOURCE_NAME_OVERRIDES = {
    "Icon_ZiZouQi_JueSe_Chan": "蝉",
    "Icon_ZiZouQi_JueSe_Chan_S": "蝉",
    "Icon_ZiZouQi_JueSe_GuanXiaoYu_BWZ": "关小雨",
    "Icon_ZiZouQi_JueSe_JiGuanShe": "机关蛇",
    "Icon_ZiZouQi_JueSe_JiGuanShe_S": "机关蛇",
    "Icon_ZiZouQi_JueSe_Kui_BWZ": "葵",
    "Icon_ZiZouQi_JueSe_Lan": "兰",
    "Icon_ZiZouQi_JueSe_LuoLa": "萝拉",
    "Icon_ZiZouQi_JueSe_WuYi": "巫医",
    "Icon_ZiZouQi_JueSe_Ying": "樱",
}


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def avatar_key(resource: str) -> str:
    if resource.endswith("_S"):
        return resource[:-2]
    if resource.endswith("S") and not resource.endswith("_S"):
        # One resource is named ..._QFZS instead of ..._QFZ_S.
        return resource[:-1]
    return resource


def copy_png(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
    return str(dst)


def main() -> None:
    rows = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    role_cards = [row for row in rows if row.get("card_image_type") == "role_card" and row.get("crop_png")]
    avatars = [row for row in rows if row.get("card_image_type") == "role_avatar" and row.get("crop_png")]
    avatar_by_key = {avatar_key(row["resource"]): row for row in avatars}

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    cards_dir = OUT_DIR / "role_cards"
    avatars_dir = OUT_DIR / "role_avatars"
    paired_dir = OUT_DIR / "paired"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for index, card in enumerate(sorted(role_cards, key=lambda r: (r.get("display_name_guess") or "", r["resource"])), 1):
        resource = card["resource"]
        name = RESOURCE_NAME_OVERRIDES.get(resource) or card.get("display_name_guess") or resource
        base = safe_name(f"{index:03d}_{name}_{resource}")

        card_out = copy_png(card.get("crop_png"), cards_dir / f"{base}.png")
        avatar = avatar_by_key.get(resource)
        avatar_out = None
        if avatar:
            avatar_out = copy_png(avatar.get("crop_png"), avatars_dir / f"{base}_avatar.png")
            copy_png(card.get("crop_png"), paired_dir / base / "role.png")
            copy_png(avatar.get("crop_png"), paired_dir / base / "avatar.png")

        manifest.append(
            {
                "index": index,
                "name": name,
                "role_resource": resource,
                "role_source_png": card.get("crop_png"),
                "role_png": card_out,
                "avatar_resource": avatar.get("resource") if avatar else None,
                "avatar_source_png": avatar.get("crop_png") if avatar else None,
                "avatar_png": avatar_out,
                "has_avatar": avatar is not None,
            }
        )

    (OUT_DIR / "roles_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "roles_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "name",
                "role_resource",
                "role_png",
                "avatar_resource",
                "avatar_png",
                "has_avatar",
            ],
        )
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in writer.fieldnames})

    print(f"role_cards={len(role_cards)}")
    print(f"role_avatars={len(avatars)}")
    print(f"paired={sum(1 for row in manifest if row['has_avatar'])}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
