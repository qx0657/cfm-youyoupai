from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

from PIL import Image
import texture2ddecoder


NAME_RE = re.compile(rb"Icon_[A-Za-z0-9_]+")


def align4(value: int) -> int:
    return (value + 3) & ~3


def read_cstr(data: bytes, pos: int) -> tuple[str, int]:
    end = data.find(b"\0", pos)
    if end < 0:
        raise ValueError("unterminated string")
    return data[pos:end].decode("ascii", "replace"), end + 1


def skip_types(data: bytes) -> tuple[int, list[int]]:
    pos = 20
    _, pos = read_cstr(data, pos)
    pos = align4(pos)
    pos += 4  # target platform
    enable_type_tree = data[pos]
    pos += 1
    type_count = struct.unpack_from("<I", data, pos)[0]
    pos += 4

    class_ids = []
    for _ in range(type_count):
        class_id = struct.unpack_from("<i", data, pos)[0]
        class_ids.append(class_id)
        pos += 4
        pos += 1  # stripped type
        pos += 2  # script type index
        if class_id == 114:
            pos += 16
        pos += 16  # old type hash
        if enable_type_tree:
            node_count = struct.unpack_from("<I", data, pos)[0]
            string_buffer_size = struct.unpack_from("<I", data, pos + 4)[0]
            pos += 8 + node_count * 24 + string_buffer_size
    return pos, class_ids


def parse_object_table(data: bytes) -> tuple[int, list[dict], list[int]]:
    pos, class_ids = skip_types(data)
    object_count = struct.unpack_from("<I", data, pos)[0]
    pos += 4
    objects = []
    for index in range(object_count):
        path_id = struct.unpack_from("<q", data, pos)[0]
        offset = struct.unpack_from("<I", data, pos + 8)[0]
        size = struct.unpack_from("<I", data, pos + 12)[0]
        type_id = struct.unpack_from("<i", data, pos + 16)[0]
        class_id = class_ids[type_id] if 0 <= type_id < len(class_ids) else None
        pos += 20
        objects.append(
            {
                "index": index,
                "path_id": path_id,
                "offset": offset,
                "size": size,
                "type_id": type_id,
                "class_id": class_id,
            }
        )
    return pos, objects, class_ids


def parse_object_table_fallback(data: bytes) -> tuple[int, list[dict], list[int]]:
    """Find CF serialized object tables when the type tree skip overshoots.

    Most CABs parse with the regular Unity layout above. A few UI CABs have a
    type tree layout that our lightweight skipper does not fully understand,
    but their object table rows are still the normal Unity 5.x 20-byte rows:
    pathID:int64, offset:uint32, size:uint32, typeID:int32.
    """
    _, class_ids = skip_types(data)
    best: tuple[int, int] | None = None
    for pos in range(0x400, min(len(data), 0x8000), 4):
        valid = 0
        for i in range(256):
            row = pos + i * 20
            if row + 20 > len(data):
                break
            offset = struct.unpack_from("<I", data, row + 8)[0]
            size = struct.unpack_from("<I", data, row + 12)[0]
            type_id = struct.unpack_from("<i", data, row + 16)[0]
            if offset < len(data) and 0 < size < len(data) and offset + size <= len(data) and 0 <= type_id < len(class_ids):
                valid += 1
            else:
                break
        if best is None or valid > best[1]:
            best = (pos, valid)
    if best is None or best[1] < 8:
        raise ValueError("could not find fallback object table")

    pos, object_count = best
    objects = []
    for index in range(object_count):
        row = pos + index * 20
        path_id = struct.unpack_from("<q", data, row)[0]
        offset = struct.unpack_from("<I", data, row + 8)[0]
        size = struct.unpack_from("<I", data, row + 12)[0]
        type_id = struct.unpack_from("<i", data, row + 16)[0]
        class_id = class_ids[type_id] if 0 <= type_id < len(class_ids) else None
        objects.append(
            {
                "index": index,
                "path_id": path_id,
                "offset": offset,
                "size": size,
                "type_id": type_id,
                "class_id": class_id,
            }
        )
    return pos + object_count * 20, objects, class_ids


def plausible_string_at(data: bytes, pos: int) -> bool:
    if pos < 0 or pos + 8 > len(data):
        return False
    length = struct.unpack_from("<I", data, pos)[0]
    if not 4 <= length <= 96 or pos + 4 + length > len(data):
        return False
    raw = data[pos + 4 : pos + 4 + length]
    return all(32 <= c < 127 for c in raw) and (raw.startswith(b"Icon_") or b"ZiZouQi" in raw)


def infer_data_offset(data: bytes, meta_end: int, objects: list[dict]) -> int:
    first_offsets = [obj["offset"] for obj in objects[:12] if obj["type_id"] in (1, 3, 4, 5)]
    best = None
    for candidate in range(align4(meta_end), min(len(data), meta_end + 0x2000), 4):
        score = 0
        for obj in objects[:40]:
            pos = candidate + obj["offset"]
            if plausible_string_at(data, pos):
                score += 3
            if obj["type_id"] == 4 and pos + 12 <= len(data):
                # Transform often starts with zero/identity-ish floats.
                score += data[pos : pos + 12].count(0)
        if first_offsets and any(plausible_string_at(data, candidate + off) for off in first_offsets):
            score += 10
        if best is None or score > best[0]:
            best = (score, candidate)
    if not best or best[0] <= 0:
        raise ValueError("could not infer data offset")
    return best[1]


def collect_names(data: bytes, objects: list[dict], data_offset: int) -> list[tuple[int, str]]:
    names = []
    for obj in objects:
        if obj.get("class_id") == 28:
            continue
        start = data_offset + obj["offset"]
        chunk = data[start : start + min(obj["size"], 4096)]
        for match in NAME_RE.finditer(chunk):
            names.append((start + match.start(), match.group().decode("ascii", "ignore")))
    return sorted(names)


def nearest_name(names: list[tuple[int, str]], abs_pos: int) -> str | None:
    prev = [name for off, name in names if off < abs_pos]
    return prev[-1] if prev else None


def infer_texture_header(data: bytes, abs_pos: int) -> tuple[int, int, int, int, int] | None:
    if abs_pos < 0 or abs_pos + 0x60 > len(data):
        return None
    vals = [struct.unpack_from("<I", data, abs_pos + i)[0] for i in range(0, 0x60, 4)]
    for format_offset in (0x0C, 0x08, 0x04):
        if vals[format_offset // 4] != 47:
            continue
        image_len_offset = format_offset + 0x44
        image_len = struct.unpack_from("<I", data, abs_pos + image_len_offset)[0]
        if image_len not in (0x10000, 0x40000, 0x100000, 0x400000):
            continue
        image_rel = image_len_offset + 4
        if format_offset == 0x0C:
            width, height = vals[0], vals[1]
        elif format_offset == 0x08:
            width = vals[0]
            height = width if image_len == width * width else int(image_len**0.5)
        else:
            width = height = int(image_len**0.5)
        if width in (256, 512, 1024, 2048) and height in (256, 512, 1024, 2048):
            return width, height, image_len, image_rel, format_offset
    for image_len_offset in range(0, 0x60, 4):
        image_len = vals[image_len_offset // 4]
        if image_len not in (0x10000, 0x40000, 0x100000, 0x400000):
            continue
        image_rel = image_len_offset + 4
        width = height = int(image_len**0.5)
        if width in (256, 512, 1024, 2048) and abs_pos + image_rel + image_len <= len(data):
            return width, height, image_len, image_rel, -1
    return None


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "texture"


def extract_one(cab_path: Path, out_dir: Path) -> dict:
    data = cab_path.read_bytes()
    meta_end, objects, class_ids = parse_object_table(data)
    try:
        data_offset = infer_data_offset(data, meta_end, objects)
        if not any(obj.get("class_id") == 28 for obj in objects):
            raise ValueError("no Texture2D objects in regular table")
    except Exception:
        meta_end, objects, class_ids = parse_object_table_fallback(data)
        data_offset = infer_data_offset(data, meta_end, objects)
    names = collect_names(data, objects, data_offset)

    png_dir = out_dir / cab_path.stem
    png_dir.mkdir(parents=True, exist_ok=True)
    textures = []
    for obj in objects:
        if obj.get("class_id") != 28:
            continue
        abs_pos = data_offset + obj["offset"]
        header = infer_texture_header(data, abs_pos)
        item = dict(obj, abs=abs_pos)
        if not header:
            item["error"] = "unsupported texture header"
            textures.append(item)
            continue
        width, height, image_len, image_rel, format_offset = header
        raw = data[abs_pos + image_rel : abs_pos + image_rel + image_len]
        name = nearest_name(names, abs_pos) or f"texture_{obj['index']:02d}"
        try:
            rgba = texture2ddecoder.decode_etc2a8(raw, width, height)
            image = Image.frombytes("RGBA", (width, height), rgba)
            png_path = png_dir / f"{obj['index']:02d}_{safe_name(name)}_{width}x{height}.png"
            image.save(png_path)
            item.update(
                {
                    "name_guess": name,
                    "width": width,
                    "height": height,
                    "format": "ETC2_RGBA8",
                    "image_len": image_len,
                    "image_rel": image_rel,
                    "format_offset": format_offset,
                    "png": str(png_path),
                }
            )
        except Exception as exc:
            item.update(
                {
                    "name_guess": name,
                    "width": width,
                    "height": height,
                    "image_len": image_len,
                    "image_rel": image_rel,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
        textures.append(item)

    return {
        "cab": str(cab_path),
        "meta_end": meta_end,
        "data_offset": data_offset,
        "object_count": len(objects),
        "class_ids": class_ids,
        "texture_count": len([obj for obj in objects if obj.get("class_id") == 28]),
        "textures": textures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CF Mobile customized CAB Texture2D ETC2 atlases.")
    parser.add_argument("inputs", nargs="+", type=Path, help="Inner CAB files extracted from UnityFS bundles.")
    parser.add_argument("--out", type=Path, default=Path("autochess_dump/cab_texture_extract"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifests = []
    for input_path in args.inputs:
        result = extract_one(input_path, args.out)
        manifests.append(result)
        ok = sum(1 for tex in result["textures"] if "png" in tex)
        print(f"{input_path.name}: objects={result['object_count']} textures={result['texture_count']} exported={ok}")

    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
