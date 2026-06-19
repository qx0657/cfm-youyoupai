from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import crop_zizouqi_sprites as zcrop


CAB_PATH = Path("autochess_dump/icon_zizouqi_cabs/ua_260__CAB-0f3fab72a734f78f52dc7f90592ef892")
ATLAS_PATH = Path(
    "autochess_dump/cab_texture_extract/"
    "ua_260__CAB-0f3fab72a734f78f52dc7f90592ef892/"
    "76_Icon_Pvp_ZiZouQi_Ladder_1024x1024.png"
)
OUT_DIR = Path("autochess_dump/organized_ladder_icons")
SPRITE_NAME_RE = re.compile(r"^Ladder_Card_Icon(?:_\d+|\d{2}_\d{2})$")
MANUAL_ENTRIES = [
    # The loose UIAtlas scanner starts cleanly from 01_02 in this object, but
    # 01_01 is present immediately before it with the same packed rect layout.
    {"sprite": "Ladder_Card_Icon01_01", "x": 406, "y": 558, "w": 248, "h": 349, "record_pos": 6319800},
]


def crop_ladder_sprite(atlas: Image.Image, entry: dict, out_path: Path) -> tuple[bool, tuple[int, int, int, int] | None]:
    x, y, w, h = entry["x"], entry["y"], entry["w"], entry["h"]
    rect = None
    for scale in (1.0, 0.5, 0.25):
        sx, sy = round(x * scale), round(y * scale)
        sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
        py = atlas.height - sy - sh
        if sx + sw <= atlas.width and 0 <= py and py + sh <= atlas.height:
            rect = (sx, py, sx + sw, py + sh)
            break
    if rect is None:
        return False, None

    crop = atlas.crop(rect).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    r, g, b, a = crop.split()
    crop = Image.merge("RGBA", (b, g, r, a))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path)
    return True, rect


def parse_ladder_entries() -> list[dict]:
    data = CAB_PATH.read_bytes()
    meta_end, objects, _ = zcrop.parse_object_table(data)
    try:
        data_offset = zcrop.infer_data_offset(data, meta_end, objects)
        if not any(obj.get("class_id") == 114 for obj in objects):
            raise ValueError("no MonoBehaviour objects in regular table")
    except Exception:
        meta_end, objects, _ = zcrop.parse_object_table_fallback(data)
        data_offset = zcrop.infer_data_offset(data, meta_end, objects)

    old_re = zcrop.SPRITE_RE
    zcrop.SPRITE_RE = re.compile(r"^Ladder_Card_Icon(?:_\d+|\d{2}_\d{2})$")
    try:
        entries = []
        for obj in objects:
            if obj.get("class_id") != 114:
                continue
            abs_start = data_offset + obj["offset"]
            abs_end = abs_start + obj["size"]
            for entry in zcrop.parse_sprite_entries(data, abs_start, abs_end):
                if not SPRITE_NAME_RE.match(entry["sprite"]):
                    continue
                entries.append(
                    {
                        **entry,
                        "cab": str(CAB_PATH),
                        "mono_object_index": obj["index"],
                    }
                )
        return entries
    finally:
        zcrop.SPRITE_RE = old_re


def make_contact_sheet(rows: list[dict], out_path: Path) -> None:
    images = []
    for row in rows:
        png = row.get("output_png")
        if not png:
            continue
        image = Image.open(png).convert("RGBA")
        thumb = Image.new("RGBA", (96, 96), (18, 22, 32, 255))
        image.thumbnail((88, 72), Image.Resampling.LANCZOS)
        thumb.alpha_composite(image, ((96 - image.width) // 2, 6))
        images.append((row["sprite"], thumb))

    if not images:
        return

    cols = 8
    cell_w, cell_h = 150, 128
    rows_count = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell_w, rows_count * cell_h), (12, 16, 24, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, (name, thumb) in enumerate(images):
        col = index % cols
        row = index // cols
        x = col * cell_w
        y = row * cell_h
        sheet.alpha_composite(thumb, (x + 27, y + 4))
        draw.text((x + 6, y + 104), name, fill=(220, 230, 240, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atlas = Image.open(ATLAS_PATH).convert("RGBA")
    r, g, b, a = atlas.split()
    Image.merge("RGBA", (b, g, r, a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).save(
        OUT_DIR / "76_Icon_Pvp_ZiZouQi_Ladder_1024x1024_rb_swap_flip_y.png"
    )
    entries = parse_ladder_entries()
    existing = {entry["sprite"] for entry in entries}
    for entry in MANUAL_ENTRIES:
        if entry["sprite"] not in existing:
            entries.append(
                {
                    **entry,
                    "cab": str(CAB_PATH),
                    "mono_object_index": 37,
                    "manual": True,
                }
            )
    entries = sorted(entries, key=lambda item: (item["sprite"], item["record_pos"] or 0))

    rows = []
    seen = set()
    for entry in entries:
        sprite = entry["sprite"]
        if sprite in seen:
            continue
        seen.add(sprite)
        out_path = OUT_DIR / "icons_rb_swap_flip_y" / f"{zcrop.safe_name(sprite)}.png"
        ok, rect = crop_ladder_sprite(atlas, entry, out_path)
        rows.append(
            {
                **entry,
                "source_atlas": str(ATLAS_PATH),
                "output_png": str(out_path) if ok else None,
                "crop_rect_top_left": rect,
                "color_fix": "swap_r_b_flip_y",
            }
        )

    (OUT_DIR / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    make_contact_sheet(rows, OUT_DIR / "ladder_icons_rb_swap_flip_y_contact.png")
    print(f"parsed={len(entries)} exported={sum(1 for row in rows if row.get('output_png'))}")
    print(f"out_dir={OUT_DIR}")


if __name__ == "__main__":
    main()
