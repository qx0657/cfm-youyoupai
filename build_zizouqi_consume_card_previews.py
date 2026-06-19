from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CONSUMES_MANIFEST = Path("autochess_dump/organized_consume_buffs/consume_cards_manifest.json")
UI_DIR = Path("autochess_dump/ua257_texture10_card_frame_slices/slices_rb_swap_flip_y/shop_ui")
OUT_DIR = Path("autochess_dump/organized_consume_card_previews")

SPELLS_BG_PNG = UI_DIR / "046_4U_Hud_ZiZouQi_Card_ShopAndMainBottom_Spells_Bg.png"
CONSUME_OFFSET_X = -1
CONSUME_OFFSET_Y = 7
LABEL_TEXT = "消耗"
LABEL_FONT_SIZE = 22
LABEL_Y = 176


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


def compose_card(consume_png: Path, out_path: Path) -> None:
    spells_bg = Image.open(SPELLS_BG_PNG).convert("RGBA")
    consume = Image.open(consume_png).convert("RGBA")
    canvas = Image.new("RGBA", spells_bg.size, (0, 0, 0, 0))
    alpha_blit(canvas, spells_bg, (0, 0))
    consume_x = (canvas.width - consume.width) // 2 + CONSUME_OFFSET_X
    consume_y = CONSUME_OFFSET_Y
    alpha_blit(canvas, consume, (consume_x, consume_y))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("msyh.ttc", LABEL_FONT_SIZE) if Path("C:/Windows/Fonts/msyh.ttc").exists() else ImageFont.load_default()
    bbox = draw.textbbox((0, 0), LABEL_TEXT, font=font)
    label_x = (canvas.width - (bbox[2] - bbox[0])) // 2
    draw.text((label_x, LABEL_Y), LABEL_TEXT, fill=(222, 235, 255, 255), font=font)
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
    count = min(len(rows), 120)
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
        draw.text((x, y + thumb_h + 4), str(row["resource"])[:18], fill=(238, 241, 245, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    consumes = json.loads(CONSUMES_MANIFEST.read_text(encoding="utf-8"))
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SPELLS_BG_PNG.exists():
        raise FileNotFoundError(SPELLS_BG_PNG)

    serialized: list[dict] = []
    cards_dir = OUT_DIR / "composited_cards"
    for consume in consumes:
        consume_png = Path(consume["png"])
        base = safe_name(f"{consume['index']:03d}_{consume['resource']}")
        out_path = cards_dir / f"{base}.png"
        compose_card(consume_png, out_path)
        serialized.append(
            {
                **consume,
                "spells_background_png": str(SPELLS_BG_PNG),
                "composited_card_png": str(out_path),
                "composition_layers": ["spells_background", "consume_image"],
                "consume_scale": "original_size",
                "consume_offset_x": CONSUME_OFFSET_X,
                "consume_offset_y": CONSUME_OFFSET_Y,
            }
        )

    (OUT_DIR / "consume_card_data.json").write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "consume_card_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["index", "resource", "png", "spells_background_png", "composited_card_png"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in serialized:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_contact_sheet(serialized, OUT_DIR / "consume_cards_preview_contact.png")
    print(f"consumes={len(serialized)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
