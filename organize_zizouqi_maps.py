from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CROPS_MANIFEST = Path("autochess_dump/zizouqi_sprite_crops/manifest.json")
OUT_DIR = Path("autochess_dump/organized_maps")


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def copy_png(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
    return str(dst)


def make_checker(size: tuple[int, int], cell: int = 12) -> Image.Image:
    image = Image.new("RGBA", size, (244, 246, 248, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(218, 222, 228, 255))
    return image


def short_label(sprite: str) -> str:
    for prefix in ("Icon_ZiZouQi_DiTu_", "Icon_ZiZouQi_Map_"):
        if sprite.startswith(prefix):
            return sprite[len(prefix) :]
    return sprite


def make_icon_sheet(rows: list[dict], out_path: Path) -> None:
    if not rows:
        return
    thumb = 96
    label_h = 30
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
        icon.thumbnail((thumb - 8, thumb - 8), Image.Resampling.LANCZOS)
        sheet.alpha_composite(icon, (x + (thumb - icon.width) // 2, y + (thumb - icon.height) // 2))
        draw.text((x, y + thumb + 5), row["map_key"][:18], fill=(238, 241, 245, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def make_background_sheet(rows: list[dict], out_path: Path) -> None:
    if not rows:
        return
    thumb_w = 256
    thumb_h = 128
    label_h = 26
    pad = 12
    cols = 2
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb_w + pad) + pad, rows_count * (thumb_h + label_h + pad) + pad), (25, 29, 36, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for i, row in enumerate(rows):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb_w + pad)
        y = pad + grid_row * (thumb_h + label_h + pad)
        image = Image.open(row["output_png"]).convert("RGBA")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.alpha_composite(image, (x + (thumb_w - image.width) // 2, y))
        draw.text((x, y + thumb_h + 5), row["map_key"][:32], fill=(238, 241, 245, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def build_row(index: int, kind: str, src_row: dict, dst_dir: Path) -> dict:
    sprite = src_row["sprite"]
    map_key = short_label(sprite).lstrip("_")
    filename = f"{index:03d}_{safe_name(sprite)}.png"
    output_png = copy_png(src_row.get("crop_png"), dst_dir / filename)
    atlas_hint = src_row.get("atlas_hint") or {}
    tried_png = src_row.get("tried_png") or []
    return {
        "index": index,
        "kind": kind,
        "resource": sprite,
        "map_key": map_key,
        "output_png": output_png,
        "source_crop_png": src_row.get("crop_png"),
        "source_atlas_png": tried_png[0] if tried_png else None,
        "atlasAssetName": atlas_hint.get("atlasAssetName"),
        "x": src_row.get("x"),
        "y": src_row.get("y"),
        "w": src_row.get("w"),
        "h": src_row.get("h"),
    }


def main() -> None:
    rows = json.loads(CROPS_MANIFEST.read_text(encoding="utf-8"))
    map_icons = [
        row
        for row in rows
        if row.get("crop_png")
        and row.get("sprite", "").startswith("Icon_ZiZouQi_Map_")
        and (row.get("atlas_hint") or {}).get("atlasAssetName") == "Icon_Pvp_ZiZouQi_MapBuff_01"
    ]
    map_backgrounds = [
        row
        for row in rows
        if row.get("crop_png")
        and row.get("sprite", "").startswith("Icon_ZiZouQi_DiTu_")
        and (row.get("atlas_hint") or {}).get("atlasAssetName", "").startswith("Icon_Pvp_ZiZouQi_BG_")
    ]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    icon_dir = OUT_DIR / "map_icons"
    background_dir = OUT_DIR / "map_backgrounds"
    atlas_dir = OUT_DIR / "source_atlases"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    icon_manifest = [
        build_row(index, "map_icon", row, icon_dir)
        for index, row in enumerate(sorted(map_icons, key=lambda item: item["sprite"]), 1)
    ]
    background_manifest = [
        build_row(index, "map_background", row, background_dir)
        for index, row in enumerate(sorted(map_backgrounds, key=lambda item: item["sprite"]), 1)
    ]
    manifest = icon_manifest + background_manifest

    copied_atlases: dict[str, str] = {}
    for row in manifest:
        source = row.get("source_atlas_png")
        if source and source not in copied_atlases:
            dst = atlas_dir / Path(source).name
            copied_atlases[source] = copy_png(source, dst) or ""
    for row in manifest:
        source = row.get("source_atlas_png")
        row["copied_source_atlas_png"] = copied_atlases.get(source)

    (OUT_DIR / "maps_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "maps_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "kind",
            "resource",
            "map_key",
            "output_png",
            "source_crop_png",
            "source_atlas_png",
            "copied_source_atlas_png",
            "w",
            "h",
            "atlasAssetName",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_icon_sheet(icon_manifest, OUT_DIR / "map_icons_check_contact.png")
    make_background_sheet(background_manifest, OUT_DIR / "map_backgrounds_check_contact.png")
    print(f"map_icons={len(icon_manifest)}")
    print(f"map_backgrounds={len(background_manifest)}")
    print(f"source_atlases={len(copied_atlases)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
