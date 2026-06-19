from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from crop_zizouqi_sprites import infer_data_offset, parse_object_table, parse_object_table_fallback, parse_sprite_entries


CAB_PATH = Path("autochess_dump/icon_zizouqi_cabs/ua_257__CAB-b27f68566db337151983cfbb301f15f1")
ATLAS_PNG = Path("autochess_dump/cab_texture_extract/ua_257__CAB-b27f68566db337151983cfbb301f15f1/10_texture_10_1024x1024.png")
OUT_DIR = Path("autochess_dump/ua257_texture10_card_frame_slices")
TARGET_MONO_INDICES = {59, 60, 61}


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def crop_from_atlas(atlas: Image.Image, entry: dict, out_path: Path, fix_rb: bool = False) -> bool:
    x, y, w, h = entry["x"], entry["y"], entry["w"], entry["h"]
    py = atlas.height - y - h
    if x < 0 or py < 0 or x + w > atlas.width or py + h > atlas.height:
        return False
    crop = atlas.crop((x, py, x + w, py + h))
    if fix_rb:
        r, g, b, a = crop.split()
        crop = Image.merge("RGBA", (b, g, r, a))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path)
    return True


def rb_swap_png(src_path: Path, dst_path: Path) -> bool:
    if not src_path.exists():
        return False
    image = Image.open(src_path).convert("RGBA")
    r, g, b, a = image.split()
    swapped = Image.merge("RGBA", (b, g, r, a))
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    swapped.save(dst_path)
    return True


def rb_swap_flip_y_png(src_path: Path, dst_path: Path) -> bool:
    if not src_path.exists():
        return False
    image = Image.open(src_path).convert("RGBA")
    r, g, b, a = image.split()
    fixed = Image.merge("RGBA", (b, g, r, a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    fixed.save(dst_path)
    return True


def load_entries() -> list[dict]:
    data = CAB_PATH.read_bytes()
    try:
        meta_end, objects, _ = parse_object_table(data)
        data_offset = infer_data_offset(data, meta_end, objects)
        if not any(obj.get("class_id") == 28 for obj in objects):
            raise ValueError("no Texture2D objects in regular table")
    except Exception:
        meta_end, objects, _ = parse_object_table_fallback(data)
        data_offset = infer_data_offset(data, meta_end, objects)

    rows: list[dict] = []
    for obj in objects:
        if obj.get("class_id") != 114 or obj.get("index") not in TARGET_MONO_INDICES:
            continue
        start = data_offset + obj["offset"]
        end = start + obj["size"]
        for entry in parse_sprite_entries(data, start, end):
            rows.append({**entry, "mono_object_index": obj["index"], "cab": str(CAB_PATH)})
    return rows


def category_for(sprite: str) -> str:
    if "Card_Bg" in sprite:
        return "card_bg"
    if "Card_Mian" in sprite or "Card_LvSe" in sprite or "Card_LanSe" in sprite or "Card_ZiSe" in sprite or "Card_ChengSe" in sprite or "Card_HuiSe" in sprite:
        return "card_quality"
    if "Attack" in sprite or "Hp" in sprite or "ATK" in sprite or "HP" in sprite:
        return "stat_ui"
    if "Job" in sprite or "Career" in sprite:
        return "job_icon"
    if "Shop" in sprite:
        return "shop_ui"
    return "misc"


def make_checker(size: tuple[int, int], cell: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, (245, 245, 245, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(218, 222, 228, 255))
    return image


def make_contact_sheet(rows: list[dict], out_path: Path) -> None:
    if not rows:
        return
    thumb = 104
    label_h = 34
    pad = 10
    cols = 7
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb + pad) + pad, rows_count * (thumb + label_h + pad) + pad), (30, 34, 42, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, row in enumerate(rows):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb + pad)
        y = pad + grid_row * (thumb + label_h + pad)
        sheet.alpha_composite(make_checker((thumb, thumb)), (x, y))
        icon = Image.open(row["output_png"]).convert("RGBA")
        icon.thumbnail((thumb - 6, thumb - 6), Image.Resampling.LANCZOS)
        sheet.alpha_composite(icon, (x + (thumb - icon.width) // 2, y + (thumb - icon.height) // 2))
        draw.text((x, y + thumb + 4), row["sprite"][:20], fill=(238, 241, 245, 255), font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    atlas = Image.open(ATLAS_PNG).convert("RGBA")
    entries = load_entries()
    manifest: list[dict] = []
    for index, entry in enumerate(sorted(entries, key=lambda row: (row["mono_object_index"], row["record_pos"])), 1):
        category = category_for(entry["sprite"])
        out_path = OUT_DIR / "slices" / category / f"{index:03d}_{safe_name(entry['sprite'])}.png"
        ok = crop_from_atlas(atlas, entry, out_path, fix_rb=False)
        rb_swap_path = OUT_DIR / "slices_rb_swap" / category / f"{index:03d}_{safe_name(entry['sprite'])}.png"
        rb_ok = rb_swap_png(out_path, rb_swap_path) if ok else False
        rb_swap_flip_y_path = OUT_DIR / "slices_rb_swap_flip_y" / category / f"{index:03d}_{safe_name(entry['sprite'])}.png"
        rb_flip_ok = rb_swap_flip_y_png(out_path, rb_swap_flip_y_path) if ok else False
        row = {
            "index": index,
            "sprite": entry["sprite"],
            "category": category,
            "output_png": str(out_path) if ok else None,
            "rb_swap_png": str(rb_swap_path) if rb_ok else None,
            "rb_swap_flip_y_png": str(rb_swap_flip_y_path) if rb_flip_ok else None,
            "source_atlas_png": str(ATLAS_PNG),
            "mono_object_index": entry["mono_object_index"],
            "x": entry["x"],
            "y": entry["y"],
            "w": entry["w"],
            "h": entry["h"],
            "record_pos": entry["record_pos"],
            "color_fix": "none",
            "rb_swap_color_fix": "swap_r_b",
            "rb_swap_flip_y_color_fix": "swap_r_b_flip_y",
        }
        manifest.append(row)

    (OUT_DIR / "texture10_slices_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "texture10_slices_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "sprite",
            "category",
            "output_png",
            "rb_swap_png",
            "rb_swap_flip_y_png",
            "source_atlas_png",
            "mono_object_index",
            "x",
            "y",
            "w",
            "h",
            "color_fix",
            "rb_swap_color_fix",
            "rb_swap_flip_y_color_fix",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})

    copied_atlas = OUT_DIR / "source_atlas" / ATLAS_PNG.name
    copied_atlas.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ATLAS_PNG, copied_atlas)

    ok_rows = [row for row in manifest if row.get("output_png")]
    rb_rows = [
        {**row, "output_png": row["rb_swap_png"]}
        for row in manifest
        if row.get("rb_swap_png")
    ]
    rb_flip_rows = [
        {**row, "output_png": row["rb_swap_flip_y_png"]}
        for row in manifest
        if row.get("rb_swap_flip_y_png")
    ]
    make_contact_sheet(ok_rows, OUT_DIR / "texture10_slices_check_contact.png")
    make_contact_sheet(rb_rows, OUT_DIR / "texture10_slices_rb_swap_check_contact.png")
    make_contact_sheet(rb_flip_rows, OUT_DIR / "texture10_slices_rb_swap_flip_y_check_contact.png")
    for category in sorted({row["category"] for row in ok_rows}):
        make_contact_sheet([row for row in ok_rows if row["category"] == category], OUT_DIR / f"{category}_check_contact.png")
    for category in sorted({row["category"] for row in rb_rows}):
        make_contact_sheet([row for row in rb_rows if row["category"] == category], OUT_DIR / f"{category}_rb_swap_check_contact.png")
    for category in sorted({row["category"] for row in rb_flip_rows}):
        make_contact_sheet([row for row in rb_flip_rows if row["category"] == category], OUT_DIR / f"{category}_rb_swap_flip_y_check_contact.png")

    print(f"entries={len(entries)}")
    print(f"exported={len(ok_rows)}")
    print(f"rb_swap_exported={len(rb_rows)}")
    print(f"rb_swap_flip_y_exported={len(rb_flip_rows)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
