from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROLES_MANIFEST = Path("autochess_dump/organized_roles/roles_manifest.json")
ROLES_DATA = Path("autochess_dump/organized_role_data/roles_data.json")
FETTERS_MANIFEST = Path("autochess_dump/organized_fetters/fetters_manifest.json")
UI_DIR = Path("autochess_dump/ua257_texture10_card_frame_slices/slices_rb_swap_flip_y/shop_ui")
OUT_DIR = Path("autochess_dump/organized_role_card_previews")

FRAME_PNG = UI_DIR / "052_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_Bg.png"
GOLD_UPGRADE_PNG = UI_DIR / "059_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_UpGrades.png"
QUALITY_PNGS = {
    "grey": UI_DIR / "053_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_HuiSe.png",
    "gray": UI_DIR / "053_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_HuiSe.png",
    "gold": UI_DIR / "054_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_JinSe.png",
    "jinse": UI_DIR / "054_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_JinSe.png",
    "blue": UI_DIR / "055_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_LanSe.png",
    "lanse": UI_DIR / "055_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_LanSe.png",
    "green": UI_DIR / "056_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_LvSe.png",
    "lvse": UI_DIR / "056_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_LvSe.png",
    "purple": UI_DIR / "060_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_ZiSe.png",
    "zise": UI_DIR / "060_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_ZiSe.png",
    "red": UI_DIR / "054_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_Hongse.png",
    "hongse": UI_DIR / "054_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_Hongse.png",
}

QUALITY_ALIASES = {
    "金": "gold",
    "金色": "gold",
    "橙": "gold",
    "橙色": "gold",
    "紫": "purple",
    "紫色": "purple",
    "蓝": "blue",
    "蓝色": "blue",
    "绿": "green",
    "绿色": "green",
    "灰": "grey",
    "灰色": "grey",
    "红": "red",
    "红色": "red",
}

QUALITY_KEYS = ("quality", "quality_guess", "品质", "card_quality", "role_quality", "rarity")
ROLE_TARGET_WIDTH = 160
ROLE_OFFSET_X = 2
ROLE_OFFSET_Y = 2
FACTION_ICON_SIZE = 28
FACTION_ICON_X = 8
FACTION_ICON_Y = 8

FACTION_ICON_BASE_NAMES = {
    "隐袭": "YinXi",
    "保卫者": "BWZ",
    "幽灵": "ShengHuaYouLing",
    "山海经": "ShanHaiJing",
    "HeartShot": "NvTuan",
    "潜伏者": "QFZ",
    "葫芦娃": "HuLuWa",
    "谍报特工": "DieBao",
    "审判之眼": "DuiZhang",
    "铠甲勇士": "KaiJiaYongShi",
    "鸿运星光": "XingGuang",
    "核心兵器": "GaiZaoZhe",
}

FACTION_ICON_VARIANT_RANK = {
    "Gold": 0,
    "GOLD": 0,
    "Colour": 1,
    "Silver": 2,
    "Sliver": 2,
    "Copper": 3,
    "Grey": 4,
    "HuiSe": 4,
}


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def normalize_quality(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in QUALITY_PNGS:
        return lowered
    if text in QUALITY_ALIASES:
        return QUALITY_ALIASES[text]
    numeric_map = {
        "1": "green",
        "2": "blue",
        "3": "purple",
        "4": "gold",
        "5": "red",
    }
    return numeric_map.get(text)


def read_role_quality(role: dict) -> tuple[str, str]:
    for key in QUALITY_KEYS:
        if key in role:
            quality = normalize_quality(role.get(key))
            if quality:
                return quality, key
    attrs = role.get("attributes")
    if isinstance(attrs, dict):
        for key in QUALITY_KEYS:
            if key in attrs:
                quality = normalize_quality(attrs.get(key))
                if quality:
                    return quality, f"attributes.{key}"
    return "gold", "default_missing_quality"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_role_faction_map() -> dict[str, list[str]]:
    rows = load_json(ROLES_DATA, [])
    return {
        row["role_resource"]: row.get("factions", [])
        for row in rows
        if row.get("role_resource") and row.get("factions")
    }


def build_role_data_map() -> dict[str, dict]:
    return {
        row["role_resource"]: row
        for row in load_json(ROLES_DATA, [])
        if row.get("role_resource")
    }


def build_faction_icon_map() -> dict[str, str]:
    icons = load_json(FETTERS_MANIFEST, [])
    icon_map: dict[str, str] = {}
    for faction_name, base_name in FACTION_ICON_BASE_NAMES.items():
        candidates = [
            icon
            for icon in icons
            if icon.get("base_name") == base_name
        ]
        candidates.sort(key=lambda icon: FACTION_ICON_VARIANT_RANK.get(icon.get("variant"), 99))
        if not candidates:
            continue
        selected = candidates[0]
        icon_path = (
            selected.get("fetter_png_rb_swap_flip_y")
            or selected.get("grouped_png_rb_swap_flip_y")
            or selected.get("fetter_png")
            or selected.get("grouped_png")
            or selected.get("source_png")
        )
        if icon_path:
            icon_map[faction_name] = icon_path
    return icon_map


def alpha_blit(dst: Image.Image, src: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    src = src.convert("RGBA")
    dst_box = (max(0, x), max(0, y), min(dst.width, x + src.width), min(dst.height, y + src.height))
    if dst_box[0] >= dst_box[2] or dst_box[1] >= dst_box[3]:
        return
    src_box = (dst_box[0] - x, dst_box[1] - y, dst_box[2] - x, dst_box[3] - y)
    dst.alpha_composite(src.crop(src_box), (dst_box[0], dst_box[1]))


def fit_image(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    if image.width <= max_size[0] and image.height <= max_size[1]:
        return image
    ratio = min(max_size[0] / image.width, max_size[1] / image.height)
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    image = image.convert("RGBA")
    if image.width == width:
        return image
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def compose_card(role_png: Path, quality_png: Path, out_path: Path, frame_png: Path = FRAME_PNG) -> None:
    frame = Image.open(frame_png).convert("RGBA")
    quality_bg = Image.open(quality_png).convert("RGBA")
    role = Image.open(role_png).convert("RGBA")

    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    alpha_blit(canvas, frame, (0, 0))
    quality_x = (canvas.width - quality_bg.width) // 2
    quality_y = (canvas.height - quality_bg.height) // 2
    alpha_blit(canvas, quality_bg, (quality_x, quality_y))

    role = resize_to_width(role, ROLE_TARGET_WIDTH)
    role_x = quality_x + ROLE_OFFSET_X
    role_y = quality_y + quality_bg.height - role.height + ROLE_OFFSET_Y
    alpha_blit(canvas, role, (role_x, role_y))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def make_contact_sheet(rows: list[dict], out_path: Path) -> None:
    if not rows:
        return
    thumb_w = 112
    thumb_h = 150
    label_h = 30
    pad = 10
    cols = 8
    count = min(len(rows), 96)
    rows_count = (count + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb_w + pad) + pad, rows_count * (thumb_h + label_h + pad) + pad), (28, 32, 40, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, row in enumerate(rows[:count]):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb_w + pad)
        y = pad + grid_row * (thumb_h + label_h + pad)
        image = Image.open(row["composited_card_png"]).convert("RGBA")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.alpha_composite(image, (x + (thumb_w - image.width) // 2, y))
        draw.text((x, y + thumb_h + 4), str(row["name"])[:18], fill=(238, 241, 245, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    roles = json.loads(ROLES_MANIFEST.read_text(encoding="utf-8"))
    role_data_map = build_role_data_map()
    role_faction_map = build_role_faction_map()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    missing_assets = [path for path in [FRAME_PNG, GOLD_UPGRADE_PNG, *set(QUALITY_PNGS.values())] if not path.exists()]
    if missing_assets:
        raise FileNotFoundError("\n".join(str(path) for path in missing_assets))

    serialized: list[dict] = []
    cards_dir = OUT_DIR / "composited_cards"
    gold_cards_dir = OUT_DIR / "gold_composited_cards"
    for manifest_role in roles:
        role_data = role_data_map.get(manifest_role.get("role_resource"), {})
        role = {**manifest_role, **role_data, "role_png": manifest_role.get("role_png"), "avatar_png": manifest_role.get("avatar_png")}
        quality, quality_source = read_role_quality(role)
        quality_png = QUALITY_PNGS.get(quality) or QUALITY_PNGS["gold"]
        role_png = Path(role["role_png"])
        factions = role.get("factions") or role_faction_map.get(role.get("role_resource"), [])
        faction = factions[0] if factions else None
        base = safe_name(f"{role['index']:03d}_{role['name']}_{role['role_resource']}")
        out_path = cards_dir / f"{base}.png"
        gold_out_path = gold_cards_dir / f"{base}.png"
        compose_card(role_png, quality_png, out_path)
        compose_card(role_png, quality_png, gold_out_path, GOLD_UPGRADE_PNG)
        serialized.append(
            {
                **role,
                "quality": quality,
                "quality_source": quality_source,
                "quality_background_png": str(quality_png),
                "frame_png": str(FRAME_PNG),
                "factions": factions,
                "faction_icon_name": faction,
                "composited_card_png": str(out_path),
                "gold_composited_card_png": str(gold_out_path),
                "composition_layers": ["frame", "quality_background", "role_image"],
            }
        )

    (OUT_DIR / "role_card_data.json").write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "role_card_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "name",
            "role_resource",
            "quality",
            "quality_source",
            "role_png",
            "quality_background_png",
            "frame_png",
            "factions",
            "faction_icon_name",
            "composited_card_png",
            "gold_composited_card_png",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in serialized:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_contact_sheet(serialized, OUT_DIR / "role_cards_preview_contact.png")
    print(f"roles={len(serialized)}")
    print(f"default_gold={sum(1 for row in serialized if row['quality_source'] == 'default_missing_quality')}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
