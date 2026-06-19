from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INDEX_PATH = Path("autochess_dump/zizouqi_card_image_index.json")
OUT_DIR = Path("autochess_dump/organized_throwables")


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
    image = Image.new("RGBA", size, (245, 245, 245, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(214, 214, 214, 255))
    return image


def fit_image(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    out = image.copy()
    out.thumbnail(box, Image.Resampling.LANCZOS)
    return out


def paste_center(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    x = x1 + ((x2 - x1) - image.width) // 2
    y = y1 + ((y2 - y1) - image.height) // 2
    canvas.alpha_composite(image, (x, y))


def make_contact_sheet(manifest: list[dict], out_path: Path) -> None:
    if not manifest:
        return
    thumb_w, thumb_h = 150, 122
    label_h = 34
    pad = 12
    cols = 5
    rows = (len(manifest) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb_w + pad) + pad, rows * (thumb_h + label_h + pad) + pad), (32, 36, 43, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for i, row in enumerate(manifest):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb_w + pad)
        y = pad + grid_row * (thumb_h + label_h + pad)
        sheet.alpha_composite(make_checker((thumb_w, thumb_h)), (x, y))
        image = Image.open(row["throwable_png"]).convert("RGBA")
        paste_center(sheet, fit_image(image, (thumb_w - 10, thumb_h - 10)), (x, y, x + thumb_w, y + thumb_h))
        label = row["throwable_resource"].replace("Icon_ZiZouQi_DaoJu_", "").replace("Icon_ZiZouQi_Weapon_", "")
        draw.text((x, y + thumb_h + 5), label[:28], fill=(235, 238, 242, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    rows = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    throwables = [
        row
        for row in rows
        if row.get("crop_png") and row.get("card_image_type") == "throwable_card"
    ]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)

    cards_dir = OUT_DIR / "throwable_cards"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for index, row in enumerate(sorted(throwables, key=lambda item: item["resource"]), 1):
        out_path = copy_png(row.get("crop_png"), cards_dir / f"{index:03d}_{safe_name(row['resource'])}.png")
        manifest.append(
            {
                "index": index,
                "throwable_resource": row["resource"],
                "source_png": row.get("crop_png"),
                "throwable_png": out_path,
                "atlasAssetName": row.get("atlasAssetName"),
            }
        )

    (OUT_DIR / "throwables_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "throwables_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["index", "throwable_resource", "throwable_png", "source_png", "atlasAssetName"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})

    make_contact_sheet(manifest, OUT_DIR / "throwable_cards_check_contact.png")

    print(f"throwable_cards={len(manifest)}")
    print(f"out={cards_dir}")


if __name__ == "__main__":
    main()
