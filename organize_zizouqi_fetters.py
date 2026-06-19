from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CROPS_MANIFEST = Path("autochess_dump/zizouqi_sprite_crops/manifest.json")
OUT_DIR = Path("autochess_dump/organized_fetters")


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def split_variant(resource: str) -> tuple[str, str]:
    name = resource.replace("Icon_ZiZouQi_", "")
    for suffix in ("_Colour", "_Copper", "_Gold", "_Golden", "_Grey", "_HuiSe", "_Silver", "_Sliver", "_GOLD"):
        if name.endswith(suffix):
            return name[: -len(suffix)], suffix.strip("_")
    return name, ""


def copy_png(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
    return str(dst)


def rb_swap_flip_y_png(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    image = Image.open(src_path).convert("RGBA")
    r, g, b, a = image.split()
    fixed = Image.merge("RGBA", (b, g, r, a)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fixed.save(dst)
    return str(dst)


def make_checker(size: tuple[int, int], cell: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, (245, 245, 245, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(214, 214, 214, 255))
    return image


def make_contact_sheet(manifest: list[dict], out_path: Path) -> None:
    if not manifest:
        return
    thumb = 84
    label_h = 34
    pad = 10
    cols = 8
    count = min(len(manifest), 80)
    rows = (count + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb + pad) + pad, rows * (thumb + label_h + pad) + pad), (32, 36, 43, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for i, row in enumerate(manifest[:count]):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb + pad)
        y = pad + grid_row * (thumb + label_h + pad)
        sheet.alpha_composite(make_checker((thumb, thumb)), (x, y))
        icon = Image.open(row["fetter_png"]).convert("RGBA")
        icon.thumbnail((thumb - 8, thumb - 8), Image.Resampling.LANCZOS)
        sheet.alpha_composite(icon, (x + (thumb - icon.width) // 2, y + (thumb - icon.height) // 2))
        label = f"{row['base_name']}_{row['variant']}" if row["variant"] else row["base_name"]
        draw.text((x, y + thumb + 5), label[:18], fill=(235, 238, 242, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    rows = json.loads(CROPS_MANIFEST.read_text(encoding="utf-8"))
    fetters = [
        row
        for row in rows
        if row.get("crop_png")
        and row.get("sprite", "").startswith("Icon_ZiZouQi_")
        and (row.get("atlas_hint") or {}).get("atlasAssetName") == "Icon_Pvp_ZiZouQi_Fetter_01"
    ]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    icons_dir = OUT_DIR / "fetter_icons"
    grouped_dir = OUT_DIR / "grouped"
    fixed_icons_dir = OUT_DIR / "fetter_icons_rb_swap_flip_y"
    fixed_grouped_dir = OUT_DIR / "grouped_rb_swap_flip_y"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for index, row in enumerate(sorted(fetters, key=lambda item: item["sprite"]), 1):
        base_name, variant = split_variant(row["sprite"])
        filename = f"{index:03d}_{safe_name(row['sprite'])}.png"
        out_path = copy_png(row.get("crop_png"), icons_dir / filename)
        grouped_path = copy_png(row.get("crop_png"), grouped_dir / safe_name(base_name) / f"{safe_name(variant or 'default')}.png")
        fixed_path = rb_swap_flip_y_png(row.get("crop_png"), fixed_icons_dir / filename)
        fixed_grouped_path = rb_swap_flip_y_png(row.get("crop_png"), fixed_grouped_dir / safe_name(base_name) / f"{safe_name(variant or 'default')}.png")
        manifest.append(
            {
                "index": index,
                "resource": row["sprite"],
                "base_name": base_name,
                "variant": variant,
                "source_png": row.get("crop_png"),
                "fetter_png": out_path,
                "grouped_png": grouped_path,
                "fetter_png_rb_swap_flip_y": fixed_path,
                "grouped_png_rb_swap_flip_y": fixed_grouped_path,
                "x": row.get("x"),
                "y": row.get("y"),
                "w": row.get("w"),
                "h": row.get("h"),
                "atlasAssetName": (row.get("atlas_hint") or {}).get("atlasAssetName"),
                "color_fix": "swap_r_b_flip_y",
            }
        )

    (OUT_DIR / "fetters_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "fetters_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "resource",
            "base_name",
            "variant",
            "fetter_png",
            "grouped_png",
            "fetter_png_rb_swap_flip_y",
            "grouped_png_rb_swap_flip_y",
            "source_png",
            "w",
            "h",
            "atlasAssetName",
            "color_fix",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_contact_sheet(manifest, OUT_DIR / "fetter_icons_check_contact.png")
    make_contact_sheet(
        [{**row, "fetter_png": row["fetter_png_rb_swap_flip_y"]} for row in manifest if row.get("fetter_png_rb_swap_flip_y")],
        OUT_DIR / "fetter_icons_rb_swap_flip_y_check_contact.png",
    )
    print(f"fetter_icons={len(manifest)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
