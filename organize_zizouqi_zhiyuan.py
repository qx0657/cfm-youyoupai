from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CROPS_MANIFEST = Path("autochess_dump/zizouqi_sprite_crops/manifest.json")
TABLE_STRINGS = Path("autochess_dump/all_target_table_strings.tsv")
OUT_DIR = Path("autochess_dump/organized_zhiyuan")


ZHINYUAN_NAME_MAP = {
    "BaGuaJing": "八卦镜",
    "BaiBaoRuYi": "百宝如意",
    "BaJingGongDeng": "八景宫灯",
    "CiXiongJian": "雌雄剑",
    "DaShenBian": "打神鞭",
    "FengHuoPuTuan": "风火蒲团",
    "HunYuanFan": "混元幡",
    "HunYuanSan": "混元伞",
    "JinXiaGuan": "金霞冠",
    "JuBaoPen": "聚宝盆",
    "KunXianShen": "捆仙绳",
    "LiuLiDeng": "琉璃灯",
    "LuHunFan": "戮魂幡",
    "LuoHunZhong": "落魂钟",
    "QianKunQuan": "乾坤圈",
    "QingJingZhu": "清净珠",
    "RiYueZhu": "日月珠",
    "RuYiDai": "如意袋",
    "ShuMu": "树木",
    "SiXiangTa": "四象塔",
    "TaiJiFu": "太极符",
    "XingHuangQi": "杏黄旗",
    "YuJingPing": "玉净瓶",
    "ZhanXianJian": "斩仙剑",
    "ZhaoTianYin": "照天印",
    "ZhaoYaoJian": "照妖剑",
    "ZiJinBo": "紫金钵",
    "ZiShouXianYi": "紫绶仙衣",
}


COLOR_MAP = {
    "Blue": "blue",
    "Gold": "gold",
    "Grey": "grey",
}


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", value).strip("_") or "unknown"


def parse_resource(resource: str) -> tuple[str, str]:
    name = resource.removeprefix("Icon_ZiZouQi_ZhiYuan_")
    for color in ("Gold", "Blue", "Grey"):
        suffix = f"_{color}"
        if name.endswith(suffix):
            return name[: -len(suffix)].strip("_"), color
    return name.strip("_"), ""


def load_text_hits() -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {name: [] for name in ZHINYUAN_NAME_MAP.values()}
    if not TABLE_STRINGS.exists():
        return hits
    for line in TABLE_STRINGS.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split("\t")
        text = parts[-1] if parts else line
        for cn_name in hits:
            if cn_name in text:
                hits[cn_name].append(line)
    return hits


def copy_png(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    src_path = Path(src)
    if not src_path.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst)
    return str(dst)


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
    thumb = 96
    label_h = 38
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
        label = f"{row['zhiyuan_key']}\n{row['color']}"
        draw.multiline_text((x, y + thumb + 4), label[:28], fill=(238, 241, 245, 255), font=font, spacing=1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out_path)


def main() -> None:
    rows = json.loads(CROPS_MANIFEST.read_text(encoding="utf-8"))
    text_hits = load_text_hits()
    zhiyuan_rows = [
        row
        for row in rows
        if row.get("crop_png")
        and row.get("sprite", "").startswith("Icon_ZiZouQi_ZhiYuan_")
    ]

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for index, row in enumerate(sorted(zhiyuan_rows, key=lambda item: (parse_resource(item["sprite"])[0], parse_resource(item["sprite"])[1])), 1):
        key, raw_color = parse_resource(row["sprite"])
        color = COLOR_MAP.get(raw_color, raw_color.lower() or "unknown")
        cn_name = ZHINYUAN_NAME_MAP.get(key)
        filename = f"{index:03d}_{safe_name(row['sprite'])}.png"
        color_dir = OUT_DIR / f"{color}_icons"
        output_png = copy_png(row.get("crop_png"), color_dir / filename)
        grouped_png = copy_png(row.get("crop_png"), OUT_DIR / "grouped" / safe_name(key) / f"{color}.png")
        hits = text_hits.get(cn_name or "", [])
        atlas_hint = row.get("atlas_hint") or {}
        tried_png = row.get("tried_png") or []
        manifest.append(
            {
                "index": index,
                "resource": row["sprite"],
                "zhiyuan_key": key,
                "chinese_name_guess": cn_name,
                "color": color,
                "quality_guess": color,
                "description": None,
                "description_match_status": "not_found_in_current_autochess_tables",
                "name_match_method": "filename_pinyin_map",
                "table_text_hits": hits[:5],
                "output_png": output_png,
                "grouped_png": grouped_png,
                "source_crop_png": row.get("crop_png"),
                "source_atlas_png": tried_png[0] if tried_png else None,
                "atlasAssetName": atlas_hint.get("atlasAssetName"),
                "x": row.get("x"),
                "y": row.get("y"),
                "w": row.get("w"),
                "h": row.get("h"),
                "manual": bool(row.get("manual")),
            }
        )

    (OUT_DIR / "zhiyuan_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT_DIR / "zhiyuan_manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = [
            "index",
            "resource",
            "zhiyuan_key",
            "chinese_name_guess",
            "color",
            "description",
            "description_match_status",
            "output_png",
            "grouped_png",
            "source_atlas_png",
            "w",
            "h",
            "atlasAssetName",
            "manual",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest:
            writer.writerow({key: row.get(key) for key in fieldnames})

    for color in ("blue", "gold", "grey"):
        make_contact_sheet([row for row in manifest if row["color"] == color], OUT_DIR / f"{color}_icons_check_contact.png")
    make_contact_sheet([row for row in manifest if row["color"] in {"blue", "gold"}], OUT_DIR / "blue_gold_icons_check_contact.png")

    print(f"zhiyuan_total={len(manifest)}")
    for color in ("blue", "gold", "grey"):
        print(f"{color}={sum(1 for row in manifest if row['color'] == color)}")
    print(f"out={OUT_DIR}")


if __name__ == "__main__":
    main()
