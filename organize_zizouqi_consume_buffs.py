from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INDEX_PATH = Path("autochess_dump/zizouqi_card_image_index.json")
OUT_DIR = Path("autochess_dump/organized_consume_buffs")


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


def write_manifest(kind: str, rows: list[dict], out_dir: Path) -> list[dict]:
    cards_dir = out_dir / f"{kind}_cards"
    manifest: list[dict] = []
    for index, row in enumerate(sorted(rows, key=lambda item: item["resource"]), 1):
        out_path = copy_png(row.get("crop_png"), cards_dir / f"{index:03d}_{safe_name(row['resource'])}.png")
        manifest.append(
            {
                "index": index,
                "resource": row["resource"],
                "source_png": row.get("crop_png"),
                "png": out_path,
                "atlasAssetName": row.get("atlasAssetName"),
            }
        )

    json_path = out_dir / f"{kind}_cards_manifest.json"
    csv_path = out_dir / f"{kind}_cards_manifest.csv"
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["index", "resource", "png", "source_png", "atlasAssetName"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})
    return manifest


def make_contact_sheet(kind: str, manifest: list[dict], out_path: Path) -> None:
    if not manifest:
        return
    thumb_w, thumb_h = 150, 122
    label_h = 34
    pad = 12
    cols = 6
    count = min(len(manifest), 48)
    rows = (count + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb_w + pad) + pad, rows * (thumb_h + label_h + pad) + pad), (32, 36, 43, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    prefix = "Icon_ZiZouQi_XiaoHao_" if kind == "consume" else "Icon_ZiZouQi_RL_"

    for i, row in enumerate(manifest[:count]):
        col = i % cols
        grid_row = i // cols
        x = pad + col * (thumb_w + pad)
        y = pad + grid_row * (thumb_h + label_h + pad)
        sheet.alpha_composite(make_checker((thumb_w, thumb_h)), (x, y))
        image = Image.open(row["png"]).convert("RGBA")
        paste_center(sheet, fit_image(image, (thumb_w - 10, thumb_h - 10)), (x, y, x + thumb_w, y + thumb_h))
        label = row["resource"].replace(prefix, "")
        draw.text((x, y + thumb_h + 5), label[:28], fill=(235, 238, 242, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    rows = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    consume_rows = [row for row in rows if row.get("crop_png") and row.get("card_image_type") == "consume_card"]
    buff_rows = [row for row in rows if row.get("crop_png") and row.get("card_image_type") == "buff_card"]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    consume_manifest = write_manifest("consume", consume_rows, OUT_DIR)
    buff_manifest = write_manifest("buff", buff_rows, OUT_DIR)
    make_contact_sheet("consume", consume_manifest, OUT_DIR / "consume_cards_check_contact.png")
    make_contact_sheet("buff", buff_manifest, OUT_DIR / "buff_cards_check_contact.png")

    print(f"consume_cards={len(consume_manifest)}")
    print(f"buff_cards={len(buff_manifest)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
