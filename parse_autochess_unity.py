#!/usr/bin/env python3
"""Extract AutoChess/悠悠牌 Unity data tables from the CF Mobile APK.

The script is read-only with respect to the APK. It extracts selected Unity
serialized asset files to an output folder, asks UnityPy to deserialize them,
and writes JSON/debug files that can be inspected or post-processed.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import UnityPy


DEFAULT_APK = Path(
    r"F:\GameAssistData\app"
    r"\7AD1C3736F7CF7FD2E77C77CCECB6744_840_com.tencent.tmgp.cf_840.apk"
)


TARGET_TABLES = {
    "assets/bin/Data/f5979883009ec504db5e581b43fb9f5a": "AutoChessRoleDataTable",
    "assets/bin/Data/a6df50c4d4344cc47865956c67bf8948": "AutoChessWeaponDataTable",
    "assets/bin/Data/fc4c92104a7fac64a98d7dcde6b940c0": "AutoChessItemDataTable",
    "assets/bin/Data/82b167d047887ba4a9b00c25af8dbee1": "AutoChessSkillConfigDataTable",
    "assets/bin/Data/ab6131e64f68b25458a3b454727b102a": "AutoChessTrammelsDataTable",
    "assets/bin/Data/906e57ae4e4dee34c88cc9611379e93e": "AutoChessResourceDataTable",
    "assets/bin/Data/d603c8793c8a4a34b9af03173033853c": "AutoChessSimpleConfigDataTable",
    "assets/bin/Data/ec5dec5a96ac9fb42a74898cf3384e04": "AutoChessSeasonInfoDataTable",
    "assets/bin/Data/bfc6f50a27551bd439aaf4cbe60417a9": "AutoChessVideoInfoDataTable",
    "assets/bin/Data/044447c884d8c504f8e67a89c07ab5de": "AutoChessWordExplanationDataTable",
    "assets/bin/Data/0dffa01da2db8364aa51a24784ace3c2": "AutoChessMapConfigDataTable",
    "assets/bin/Data/b68a49db9007ac648a489169485accda": "AutoChessRecommendCardDataTable",
    "assets/bin/Data/f4b8f146de77826409c03be9fae7433f": "AutoChessCombinationShowDataTable",
}

TEXT_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_\-：:+，,。（）()【】\[\]/%<>]{2,120}")


@dataclass(frozen=True)
class ExtractedAsset:
    apk_entry: str
    table_name: str
    path: Path


def safe_name(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.\-\u4e00-\u9fff]+", "_", name).strip("_")


def to_jsonable(value: Any, depth: int = 0, max_depth: int = 12) -> Any:
    if depth > max_depth:
        return repr(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return {
            "__bytes__": len(value),
            "preview_hex": value[:64].hex(),
            "strings": extract_strings(value, limit=40),
        }
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item, depth + 1, max_depth) for item in value]
    if isinstance(value, dict):
        return {
            str(key): to_jsonable(val, depth + 1, max_depth)
            for key, val in value.items()
        }
    if hasattr(value, "to_dict"):
        try:
            return to_jsonable(value.to_dict(), depth + 1, max_depth)
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        data = {}
        for key, val in vars(value).items():
            if key.startswith("_"):
                continue
            data[key] = to_jsonable(val, depth + 1, max_depth)
        if data:
            return data
    return repr(value)


def extract_strings(blob: bytes, limit: int = 300) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()
    for encoding in ("utf-8", "utf-16-le"):
        try:
            decoded = blob.decode(encoding, errors="ignore")
        except Exception:
            continue
        for match in TEXT_RE.finditer(decoded):
            value = match.group(0).strip("\x00")
            if len(value) < 2 or value in seen:
                continue
            seen.add(value)
            texts.append(value)
            if len(texts) >= limit:
                return texts
    return texts


def extract_targets(apk: Path, output: Path) -> list[ExtractedAsset]:
    target_dir = output / "extracted_assets"
    target_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[ExtractedAsset] = []

    with zipfile.ZipFile(apk) as zf:
        names = set(zf.namelist())
        for entry, table_name in TARGET_TABLES.items():
            if entry not in names:
                print(f"[miss] {entry}", file=sys.stderr)
                continue
            out_path = target_dir / f"{table_name}__{Path(entry).name}"
            with zf.open(entry) as src, out_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(ExtractedAsset(entry, table_name, out_path))

    return extracted


def read_unity_objects(asset: ExtractedAsset) -> dict[str, Any]:
    env = UnityPy.load(str(asset.path))
    objects: list[dict[str, Any]] = []

    for obj in env.objects:
        item: dict[str, Any] = {
            "path_id": obj.path_id,
            "type": obj.type.name,
        }
        try:
            data = obj.read()
            item["name"] = getattr(data, "name", None) or getattr(data, "m_Name", None)
            item["data"] = to_jsonable(data)
        except Exception as exc:
            item["read_error"] = repr(exc)
            try:
                item["typetree"] = to_jsonable(obj.read_typetree())
            except Exception as tree_exc:
                item["typetree_error"] = repr(tree_exc)
        objects.append(item)

    raw = asset.path.read_bytes()
    return {
        "apk_entry": asset.apk_entry,
        "table_name": asset.table_name,
        "file": str(asset.path),
        "size": len(raw),
        "note": (
            "UnityPy object_count=0 usually means this file is a game binary "
            "DataTable/resource dependency rather than a standalone Unity "
            "serialized object. Use strings_preview / strings.txt outputs, or "
            "load a decrypted AssetBundle if available."
        ),
        "strings_preview": extract_strings(raw),
        "objects": objects,
    }


def write_strings_outputs(asset: ExtractedAsset, output: Path, strings: list[str]) -> None:
    txt = output / f"{safe_name(asset.table_name)}.strings.txt"
    txt.write_text("\n".join(strings) + "\n", encoding="utf-8")

    rows = ["table\tindex\tvalue"]
    rows.extend(
        f"{asset.table_name}\t{index}\t{value.replace(chr(9), ' ')}"
        for index, value in enumerate(strings)
    )
    tsv = output / f"{safe_name(asset.table_name)}.strings.tsv"
    tsv.write_text("\n".join(rows) + "\n", encoding="utf-8")


def is_chinese_name(value: str) -> bool:
    if not re.search(r"[\u4e00-\u9fff]", value):
        return False
    if any(ch in value for ch in "：，。,+/%<>[]【】()（）"):
        return False
    return 1 <= len(value) <= 16


def guess_resource_mappings(strings: list[str]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for index, value in enumerate(strings):
        if not re.match(r"^(Icon|UI|Hall|AutoChess|Card|ZiZouQi|Weapon|Item)_", value):
            continue
        window = strings[index + 1 : index + 6]
        display_name = next((item for item in window if is_chinese_name(item)), None)
        mappings.append(
            {
                "index": index,
                "resource": value,
                "display_name_guess": display_name,
                "next_values": window,
            }
        )
    return mappings


def scan_autochess_tables(apk: Path, output: Path) -> None:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(rb"AutoChess[A-Za-z0-9_]+DataTable")

    with zipfile.ZipFile(apk) as zf:
        for info in zf.infolist():
            if not info.filename.startswith("assets/bin/Data/"):
                continue
            if info.file_size > 20_000_000:
                continue
            data = zf.read(info)
            tables = sorted({m.group(0).decode("ascii", errors="ignore") for m in pattern.finditer(data)})
            if tables or any(key in data for key in ("悠悠牌".encode(), "小小牌手".encode())):
                rows.append(
                    {
                        "entry": info.filename,
                        "size": info.file_size,
                        "tables": tables,
                        "strings": extract_strings(data, limit=50),
                    }
                )

    (output / "autochess_table_scan.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] wrote {output / 'autochess_table_scan.json'} ({len(rows)} entries)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, default=DEFAULT_APK, help="Path to com.tencent.tmgp.cf APK")
    parser.add_argument("--out", type=Path, default=Path("autochess_dump"), help="Output directory")
    parser.add_argument("--scan", action="store_true", help="Also scan all assets/bin/Data entries for AutoChess tables")
    args = parser.parse_args()

    if not args.apk.exists():
        print(f"APK not found: {args.apk}", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)

    if args.scan:
        scan_autochess_tables(args.apk, args.out)

    extracted = extract_targets(args.apk, args.out)
    if not extracted:
        print("No target assets extracted.", file=sys.stderr)
        return 1

    summary: list[dict[str, Any]] = []
    all_strings_rows = ["table\tindex\tvalue"]
    for asset in extracted:
        print(f"[read] {asset.table_name}")
        result = read_unity_objects(asset)
        out_file = args.out / f"{safe_name(asset.table_name)}.json"
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        strings = result["strings_preview"]
        write_strings_outputs(asset, args.out, strings)
        all_strings_rows.extend(
            f"{asset.table_name}\t{index}\t{value.replace(chr(9), ' ')}"
            for index, value in enumerate(strings)
        )

        if asset.table_name == "AutoChessResourceDataTable":
            mappings = guess_resource_mappings(strings)
            (args.out / "AutoChessResourceDataTable.resource_name_guesses.json").write_text(
                json.dumps(mappings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        summary.append(
            {
                "table_name": asset.table_name,
                "apk_entry": asset.apk_entry,
                "json": str(out_file),
                "object_count": len(result["objects"]),
                "string_count": len(result["strings_preview"]),
                "strings_txt": str(args.out / f"{safe_name(asset.table_name)}.strings.txt"),
            }
        )

    summary_file = args.out / "summary.json"
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "all_target_table_strings.tsv").write_text(
        "\n".join(all_strings_rows) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] wrote {summary_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
