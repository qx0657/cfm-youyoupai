from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WEAPONS_MANIFEST = Path("autochess_dump/organized_weapons/weapons_manifest.json")
UI_DIR = Path("autochess_dump/ua257_texture10_card_frame_slices/slices_rb_swap_flip_y/shop_ui")
OUT_DIR = Path("autochess_dump/organized_weapon_card_previews")

FRAME_PNG = UI_DIR / "052_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_Bg.png"
QUALITY_PNGS = {
    "gold": UI_DIR / "054_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_JinSe.png",
    "blue": UI_DIR / "055_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_LanSe.png",
    "purple": UI_DIR / "060_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_ZiSe.png",
}
WEAPON_QUALITY_BY_RESOURCE = {
    "Icon_ZiZouQi_WuQi_MK5_jixiejiyuan": "blue",
    "Icon_ZiZouQi_WuQi_M14EBR_anye": "blue",
    "Icon_ZiZouQi_WuQi_RPK_panlong": "blue",
    "Icon_ZiZouQi_WuQi_MG3_chufeng": "blue",
    "Icon_ZiZouQi_WuQi_CZS2_shancaitongzi": "purple",
    "Icon_ZiZouQi_WuQi_sitaieremo": "purple",
    "Icon_ZiZouQi_WuQi_P90_tututu": "purple",
    "Icon_ZiZouQi_WuQi_AWM_tianlong": "purple",
    "Icon_ZiZouQi_WuQi_M1216_xueyue": "purple",
    "Icon_ZiZouQi_WuQi_AN94_chaoxinxing": "purple",
    "Icon_ZiZouQi_WuQi_M249_zuilie": "purple",
    "Icon_ZiZouQi_WuQi_liuyisi_tianshi": "purple",
    "Icon_ZiZouQi_WuQi_QBZ97_lanwu": "purple",
    "Icon_ZiZouQi_WuQi_TAC_qingwu": "purple",
    "Icon_ZiZouQi_WuQi_9A91_moxi": "purple",
    "Icon_ZiZouQi_WuQi_VEPR12_BenChu": "purple",
    "Icon_ZiZouQi_WuQi_AK47_FengXian": "purple",
    "Icon_ZiZouQi_WuQi_AK47_WuYing": "purple",
    "Icon_ZiZouQi_WuQi_A180_DiYuFengHuang": "purple",
    "Icon_ZiZouQi_WuQi_CBJ_DuFeng": "purple",
    "Icon_ZiZouQi_WuQi_HK416_jiguang": "purple",
    "Icon_ZiZouQi_WuQi_AK12_TianQi": "purple",
    "Icon_ZiZouQi_WuQi_M4A1_XingXiang": "purple",
}

WEAPON_OFFSET_X = 0
WEAPON_OFFSET_Y = 20


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def alpha_blit(dst: Image.Image, src: Image.Image, xy: tuple[int, int]) -> None:
    x, y = xy
    src = src.convert("RGBA")
    dst_box = (max(0, x), max(0, y), min(dst.width, x + src.width), min(dst.height, y + src.height))
    if dst_box[0] >= dst_box[2] or dst_box[1] >= dst_box[3]:
        return
    src_box = (dst_box[0] - x, dst_box[1] - y, dst_box[2] - x, dst_box[3] - y)
    dst.alpha_composite(src.crop(src_box), (dst_box[0], dst_box[1]))


def compose_card(weapon_png: Path, quality_png: Path, out_path: Path) -> None:
    frame = Image.open(FRAME_PNG).convert("RGBA")
    quality_bg = Image.open(quality_png).convert("RGBA")
    weapon = Image.open(weapon_png).convert("RGBA")

    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    alpha_blit(canvas, frame, (0, 0))
    quality_x = (canvas.width - quality_bg.width) // 2
    quality_y = (canvas.height - quality_bg.height) // 2
    alpha_blit(canvas, quality_bg, (quality_x, quality_y))

    weapon_x = quality_x + (quality_bg.width - weapon.width) // 2 + WEAPON_OFFSET_X
    weapon_y = quality_y + (quality_bg.height - weapon.height) // 2 + WEAPON_OFFSET_Y
    alpha_blit(canvas, weapon, (weapon_x, weapon_y))

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
        draw.text((x, y + thumb_h + 4), str(row["base_resource"])[:18], fill=(238, 241, 245, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    weapons = json.loads(WEAPONS_MANIFEST.read_text(encoding="utf-8"))
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    missing_assets = [path for path in [FRAME_PNG, *set(QUALITY_PNGS.values())] if not path.exists()]
    if missing_assets:
        raise FileNotFoundError("\n".join(str(path) for path in missing_assets))

    serialized: list[dict] = []
    cards_dir = OUT_DIR / "composited_cards"
    for weapon in weapons:
        quality = WEAPON_QUALITY_BY_RESOURCE.get(weapon["base_resource"], "gold")
        quality_source = "known_weapon_resource_quality" if weapon["base_resource"] in WEAPON_QUALITY_BY_RESOURCE else "default_weapon_gold"
        quality_png = QUALITY_PNGS.get(quality) or QUALITY_PNGS["gold"]
        weapon_png = Path(weapon["weapon_png"])
        base = safe_name(f"{weapon['index']:03d}_{weapon['base_resource']}")
        out_path = cards_dir / f"{base}.png"
        compose_card(weapon_png, quality_png, out_path)
        serialized.append(
            {
                **weapon,
                "quality": quality,
                "quality_source": quality_source,
                "quality_background_png": str(quality_png),
                "frame_png": str(FRAME_PNG),
                "composited_card_png": str(out_path),
                "composition_layers": ["frame", "quality_background", "weapon_image"],
                "weapon_scale": "original_size",
                "weapon_offset_x": WEAPON_OFFSET_X,
                "weapon_offset_y": WEAPON_OFFSET_Y,
            }
        )

    (OUT_DIR / "weapon_card_data.json").write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "weapon_card_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "base_resource",
            "weapon_resource",
            "quality",
            "quality_source",
            "weapon_png",
            "quality_background_png",
            "frame_png",
            "composited_card_png",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in serialized:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_contact_sheet(serialized, OUT_DIR / "weapon_cards_preview_contact.png")
    print(f"weapons={len(serialized)}")
    print(f"default_gold={sum(1 for row in serialized if row['quality_source'] == 'default_weapon_gold')}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
