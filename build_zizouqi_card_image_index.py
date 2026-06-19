from __future__ import annotations

import json
from pathlib import Path


THROWABLE_RESOURCE_TOKENS = (
    "putongshoulei",
    "putongshanguangdan",
    "putongyanwudan",
    "putongranshaodan",
    "wangzhezhiyi",
    "wangzhezhishi",
    "wangzhezhisuo",
    "zujiuying",
    "zidianrongyan",
)


def classify(resource: str, atlas_name: str | None = None) -> str:
    lower_resource = resource.lower()
    is_throwable_resource = (
        "_DaoJu_" in resource and any(token in lower_resource for token in THROWABLE_RESOURCE_TOKENS)
    ) or lower_resource == "icon_zizouqi_weapon_wzzy_zidianrongyan"
    if is_throwable_resource:
        if resource.endswith("_S") or resource.endswith("_s") or (atlas_name and "Avatar" in atlas_name):
            return "throwable_avatar"
        return "throwable_card"
    if "_RL_" in resource or (atlas_name and "RLBuff" in atlas_name):
        return "buff_card"
    if "_XiaoHao_" in resource:
        return "consume_card"
    if "_JueSe_" in resource:
        if resource.endswith("_S") or (atlas_name and "Avatar" in atlas_name):
            return "role_avatar"
        return "role_card"
    if "_WuQi_" in resource:
        if resource.endswith("_S") or resource.endswith("_s") or (atlas_name and "Avatar" in atlas_name):
            return "weapon_avatar"
        if resource.endswith("_03") or (atlas_name and "HandCards" in atlas_name):
            return "weapon_card"
        if resource.endswith("_02") or (atlas_name and "Enemy" in atlas_name):
            return "weapon_enemy"
        if resource.endswith("_01") or (atlas_name and "Weapon_We" in atlas_name):
            return "weapon_own"
        return "weapon"
    if "_Weapon_" in resource:
        return "weapon"
    if "_DaoJu_" in resource:
        if resource.endswith("_S") or resource.endswith("_s") or (atlas_name and "Avatar" in atlas_name):
            return "item_avatar"
        return "item_card"
    if "_TouZhi_" in resource or "_TouZhiWu_" in resource:
        return "throwable"
    if "_RLBuff_" in resource:
        return "buff"
    if "_Spells_" in resource:
        return "spell"
    if "_ZhiYuan_" in resource:
        return "support"
    return "other"


def main() -> None:
    guesses_path = Path("autochess_dump/AutoChessResourceDataTable.resource_name_guesses.json")
    crops_path = Path("autochess_dump/zizouqi_sprite_crops/manifest.json")
    out_path = Path("autochess_dump/zizouqi_card_image_index.json")

    guesses = json.loads(guesses_path.read_text(encoding="utf-8"))
    crops = json.loads(crops_path.read_text(encoding="utf-8"))
    crop_by_sprite = {row["sprite"]: row for row in crops if row.get("crop_png")}

    guess_by_resource = {
        guess.get("resource"): guess
        for guess in guesses
        if guess.get("resource") and guess.get("resource").startswith("Icon_ZiZouQi_")
    }
    resources = set(guess_by_resource)
    resources.update(sprite for sprite in crop_by_sprite if sprite.startswith("Icon_ZiZouQi_"))

    rows = []
    seen = set()
    for resource in sorted(resources):
        if resource in seen:
            continue
        seen.add(resource)
        guess = guess_by_resource.get(resource, {})
        crop = crop_by_sprite.get(resource)
        atlas_name = (crop or {}).get("atlas_hint", {}).get("atlasAssetName")
        rows.append(
            {
                "resource": resource,
                "display_name_guess": guess.get("display_name_guess"),
                "card_image_type": classify(resource, atlas_name),
                "atlasAssetName": atlas_name,
                "atlasAssetId": (crop or {}).get("atlas_hint", {}).get("atlasAssetId"),
                "crop_png": (crop or {}).get("crop_png"),
                "x": (crop or {}).get("x"),
                "y": (crop or {}).get("y"),
                "w": (crop or {}).get("w"),
                "h": (crop or {}).get("h"),
            }
        )

    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    by_type = {}
    for row in rows:
        item = by_type.setdefault(row["card_image_type"], {"total": 0, "with_image": 0})
        item["total"] += 1
        item["with_image"] += 1 if row.get("crop_png") else 0
    print(f"wrote {out_path}")
    print(json.dumps(by_type, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
