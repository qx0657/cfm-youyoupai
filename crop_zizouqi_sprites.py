from __future__ import annotations

import json
import re
import struct
from bisect import bisect_right
from pathlib import Path

from PIL import Image

from extract_cf_cab_textures import infer_data_offset, parse_object_table, parse_object_table_fallback, safe_name


SPRITE_RE = re.compile(r"^(?:Icon_(?:ZiZouQi|Pvp_ZiZouQi)|4U_(?:Hud_)?ZiZouQi|4U_Hud_CardMode)[A-Za-z0-9_]*$")

ATLAS_TEXTURE_OVERRIDES = {
    # These two atlases have sprite metadata under their real atlas names, but
    # the decoded Texture2D name guesses point at unrelated UI assets.
    "Icon_Pvp_ZiZouQi_Spells_02": ("ua_249", 3),
    "Icon_Pvp_ZiZouQi_Spells_03": ("ua_283", 40),
    "Icon_Pvp_ZiZouQi_MapBuff_01": ("ua_260", 45),
    "Icon_Pvp_ZiZouQi_Role_06": ("ua_335", 74),
    "Icon_Pvp_ZiZouQi_ZhiYuan_01": ("ua_300", 37),
    "Icon_Pvp_ZiZouQi_ZhiYuan_02": ("ua_300", 56),
    "Icon_Pvp_ZiZouQi_ZhiYuan_03": ("ua_300", 57),
    "Icon_Pvp_ZiZouQi_Weapon_HandCards_02": ("ua_260", 61),
    "Icon_Pvp_ZiZouQi_Weapon_We_02": ("ua_260", 45),
}

MANUAL_SPRITE_ENTRIES = [
    # The sprite-to-atlas table references this map icon, but the loose
    # UIAtlas binary scanner misses its rect. The atlas is a regular 256 grid,
    # and this is the only occupied cell missing from parsed rows.
    {"sprite": "Icon_ZiZouQi_Map_CangNiZhiDi", "x": 512, "y": 512, "w": 256, "h": 256, "record_pos": None},
    {"sprite": "Icon_ZiZouQi_ZhiYuan_BaGuaJing_Gold", "x": 0, "y": 896, "w": 128, "h": 128, "record_pos": None},
    {"sprite": "Icon_ZiZouQi_ZhiYuan_BaGuaJing__Grey", "x": 0, "y": 896, "w": 128, "h": 128, "record_pos": None},
    {"sprite": "Icon_ZiZouQi_ZhiYuan_BaGuaJing_Blue", "x": 0, "y": 896, "w": 128, "h": 128, "record_pos": None},
    # The Role_06 atlas mapping contains JiGuanShe, but its sprite rect is the
    # only occupied 168x224 grid cell omitted by the loose UIAtlas scanner.
    {"sprite": "Icon_ZiZouQi_JueSe_JiGuanShe", "x": 682, "y": 2, "w": 168, "h": 224, "record_pos": None},
    # 81式-瑜 occupies the first cell in these two weapon atlases. Their first
    # records are omitted by the loose UIAtlas scanner while the other 23 parse.
    {"sprite": "Icon_ZiZouQi_WuQi_81_yu_03", "x": 797, "y": 665, "w": 157, "h": 219, "record_pos": None},
    {"sprite": "Icon_ZiZouQi_WuQi_81_yu_01", "x": 852, "y": 680, "w": 168, "h": 224, "record_pos": None},
]


def align4(value: int) -> int:
    return (value + 3) & ~3


def read_prefixed_string(data: bytes, pos: int) -> tuple[str, int] | None:
    if pos + 4 > len(data):
        return None
    length = struct.unpack_from("<I", data, pos)[0]
    if not 4 <= length <= 128 or pos + 4 + length > len(data):
        return None
    raw = data[pos + 4 : pos + 4 + length]
    if not all(32 <= c < 127 for c in raw):
        return None
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    return text, align4(pos + 4 + length)


def parse_sprite_entries(data: bytes, start: int, end: int) -> list[dict]:
    entries: list[dict] = []
    pos = start
    while pos + 24 <= end:
        parsed = read_prefixed_string(data, pos)
        if not parsed:
            pos += 4
            continue
        name, after_name = parsed
        if not SPRITE_RE.match(name) or after_name + 16 > end:
            pos += 4
            continue
        x, y, w, h = struct.unpack_from("<iiii", data, after_name)
        if not (0 <= x <= 4096 and 0 <= y <= 4096 and 1 <= w <= 2048 and 1 <= h <= 2048):
            pos += 4
            continue
        # In these UIAtlas objects every entry carries many extra fields; the
        # next length-prefixed sprite usually starts on a 4-byte boundary later.
        entries.append({"sprite": name, "x": x, "y": y, "w": w, "h": h, "record_pos": pos})
        pos = after_name + 16
    return entries


def load_manifest(manifest_path: Path) -> tuple[dict[tuple[str, int], dict], list[dict]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    textures: dict[tuple[str, int], dict] = {}
    all_textures = []
    for bundle in data:
        cab_name = Path(bundle["cab"]).name
        for tex in bundle["textures"]:
            if "png" in tex:
                row = {**tex, "cab_name": cab_name}
                textures[(cab_name, tex["index"])] = row
                all_textures.append(row)
    return textures, all_textures


def build_atlas_lookup(path: Path) -> dict[str, dict]:
    lookup = {}
    if not path.exists():
        return lookup
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        lookup[row["sprite"]] = row
    return lookup


def crop_from_atlas(atlas_path: Path, entry: dict, out_path: Path) -> bool:
    image = Image.open(atlas_path).convert("RGBA")
    x, y, w, h = entry["x"], entry["y"], entry["w"], entry["h"]
    rect = None
    for scale in (1.0, 0.5, 0.25):
        sx, sy = round(x * scale), round(y * scale)
        sw, sh = max(1, round(w * scale)), max(1, round(h * scale))
        for py in (image.height - sy - sh, sy):
            if sx + sw <= image.width and 0 <= py and py + sh <= image.height:
                rect = (sx, py, sx + sw, py + sh)
                break
        if rect is not None:
            break
    if rect is None:
        return False
    # UIAtlas rects use a bottom-left origin; top-left is kept as a fallback.
    crop = image.crop(rect)
    if any(token in entry["sprite"] for token in ("_JueSe_", "_WuQi_", "_Weapon_", "_DaoJu_", "_XiaoHao_", "_RL_", "_Map_", "_DiTu_", "_ZhiYuan_")):
        crop = crop.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        r, g, b, a = crop.split()
        crop = Image.merge("RGBA", (b, g, r, a))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path)
    return True


def build_reference_maps(data: bytes, objects: list[dict], data_offset: int) -> tuple[dict[int, int], dict[int, int]]:
    by_path_id = {obj["path_id"]: obj for obj in objects}
    material_path_ids = {obj["path_id"] for obj in objects if obj.get("class_id") == 21}
    texture_path_ids = {obj["path_id"]: obj["index"] for obj in objects if obj.get("class_id") == 28}

    material_to_texture: dict[int, int] = {}
    for obj in objects:
        if obj.get("class_id") != 21:
            continue
        chunk = data[data_offset + obj["offset"] : data_offset + obj["offset"] + obj["size"]]
        for texture_path_id, texture_index in texture_path_ids.items():
            if struct.pack("<q", texture_path_id) in chunk:
                material_to_texture[obj["index"]] = texture_index
                break

    mono_to_texture: dict[int, int] = {}
    for obj in objects:
        if obj.get("class_id") != 114:
            continue
        chunk = data[data_offset + obj["offset"] : data_offset + obj["offset"] + min(obj["size"], 64)]
        for material_path_id in material_path_ids:
            if struct.pack("<q", material_path_id) in chunk:
                material = by_path_id[material_path_id]
                texture_index = material_to_texture.get(material["index"])
                if texture_index is not None:
                    mono_to_texture[obj["index"]] = texture_index
                    break
    return material_to_texture, mono_to_texture


def texture_matches_atlas(texture: dict, atlas_name: str) -> int:
    if not atlas_name:
        return 0
    candidates = [
        texture.get("name_guess", ""),
        Path(texture.get("png", "")).stem,
    ]
    best = 0
    for value in candidates:
        if not value:
            continue
        if value == atlas_name:
            best = max(best, 100)
        elif value.startswith(atlas_name) or atlas_name.startswith(value):
            best = max(best, min(len(value), len(atlas_name)))
        elif atlas_name in value:
            best = max(best, len(atlas_name) - 4)
    return best


def find_textures_for_atlas(all_textures: list[dict], atlas_name: str) -> list[dict]:
    ranked = []
    for tex in all_textures:
        score = texture_matches_atlas(tex, atlas_name)
        if score >= 18:
            ranked.append((score, tex))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [tex for _, tex in ranked]


def process_cab(
    cab_path: Path,
    manifest_textures: dict[tuple[str, int], dict],
    all_textures: list[dict],
    atlas_lookup: dict[str, dict],
    out_dir: Path,
) -> list[dict]:
    data = cab_path.read_bytes()
    meta_end, objects, _ = parse_object_table(data)
    try:
        data_offset = infer_data_offset(data, meta_end, objects)
        if not any(obj.get("class_id") == 28 for obj in objects):
            raise ValueError("no Texture2D objects in regular table")
    except Exception:
        meta_end, objects, _ = parse_object_table_fallback(data)
        data_offset = infer_data_offset(data, meta_end, objects)
    _, mono_to_texture = build_reference_maps(data, objects, data_offset)

    texture_indices = [obj["index"] for obj in objects if obj.get("class_id") == 28]
    texture_indices.sort()
    cab_name = cab_path.name
    results = []

    for obj in objects:
        if obj.get("class_id") != 114:
            continue
        abs_start = data_offset + obj["offset"]
        abs_end = abs_start + obj["size"]
        entries = parse_sprite_entries(data, abs_start, abs_end)
        if not entries:
            continue

        insert_at = bisect_right(texture_indices, obj["index"])
        candidate_texture_indices = []
        if insert_at:
            candidate_texture_indices.append(texture_indices[insert_at - 1])
        if insert_at < len(texture_indices):
            candidate_texture_indices.append(texture_indices[insert_at])

        for entry in entries:
            atlas_hint = atlas_lookup.get(entry["sprite"], {})
            exported = None
            tried = []
            atlas_name = atlas_hint.get("atlasAssetName") or ""
            referenced_texture_index = mono_to_texture.get(obj["index"])
            referenced_textures = []
            override = ATLAS_TEXTURE_OVERRIDES.get(atlas_name)
            if override:
                cab_marker, texture_index = override
                for (texture_cab_name, candidate_index), texture in manifest_textures.items():
                    if texture_index == candidate_index and cab_marker in texture_cab_name:
                        referenced_textures.append(texture)
                        break
            if referenced_texture_index is not None and (cab_name, referenced_texture_index) in manifest_textures:
                referenced_textures.append(manifest_textures[(cab_name, referenced_texture_index)])
            preferred_textures = find_textures_for_atlas(all_textures, atlas_name)
            fallback_textures = [
                manifest_textures[(cab_name, tex_index)]
                for tex_index in candidate_texture_indices
                if (cab_name, tex_index) in manifest_textures
            ]
            seen = set()
            for tex in [*referenced_textures, *preferred_textures, *fallback_textures]:
                key = tex.get("png")
                if key in seen:
                    continue
                seen.add(key)
                png = Path(tex["png"])
                tried.append(str(png))
                rel_dir = atlas_name or png.stem
                out_path = out_dir / safe_name(rel_dir) / f"{safe_name(entry['sprite'])}.png"
                if crop_from_atlas(png, entry, out_path):
                    exported = str(out_path)
                    break
            row = {
                **entry,
                "cab": str(cab_path),
                "mono_object_index": obj["index"],
                "atlas_hint": atlas_hint,
                "referenced_texture_index": referenced_texture_index,
                "candidate_textures": candidate_texture_indices,
                "tried_png": tried,
                "crop_png": exported,
            }
            results.append(row)
    return results


def append_manual_entries(
    all_rows: list[dict],
    manifest_textures: dict[tuple[str, int], dict],
    atlas_lookup: dict[str, dict],
    out_dir: Path,
) -> None:
    existing = {row.get("sprite") for row in all_rows}
    for entry in MANUAL_SPRITE_ENTRIES:
        if entry["sprite"] in existing:
            continue
        atlas_hint = atlas_lookup.get(entry["sprite"], {})
        atlas_name = atlas_hint.get("atlasAssetName") or ""
        tried = []
        exported = None
        override = ATLAS_TEXTURE_OVERRIDES.get(atlas_name)
        if override:
            cab_marker, texture_index = override
            for (texture_cab_name, candidate_index), texture in manifest_textures.items():
                if texture_index == candidate_index and cab_marker in texture_cab_name:
                    png = Path(texture["png"])
                    tried.append(str(png))
                    out_path = out_dir / safe_name(atlas_name or png.stem) / f"{safe_name(entry['sprite'])}.png"
                    if crop_from_atlas(png, entry, out_path):
                        exported = str(out_path)
                    break
        all_rows.append(
            {
                **entry,
                "cab": None,
                "mono_object_index": None,
                "atlas_hint": atlas_hint,
                "referenced_texture_index": None,
                "candidate_textures": [],
                "tried_png": tried,
                "crop_png": exported,
                "manual": True,
            }
        )


def main() -> None:
    cab_dir = Path("autochess_dump/icon_zizouqi_cabs")
    manifest_path = Path("autochess_dump/cab_texture_extract/manifest.json")
    out_dir = Path("autochess_dump/zizouqi_sprite_crops")
    manifest_textures, all_textures = load_manifest(manifest_path)
    atlas_lookup = build_atlas_lookup(Path("autochess_dump/icon_zizouqi_sprite_to_atlas.json"))

    all_rows = []
    for cab_path in sorted(cab_dir.iterdir()):
        if cab_path.is_file() and "__CAB-" in cab_path.name:
            rows = process_cab(cab_path, manifest_textures, all_textures, atlas_lookup, out_dir)
            ok = sum(1 for row in rows if row.get("crop_png"))
            print(f"{cab_path.name}: sprites={len(rows)} cropped={ok}")
            all_rows.extend(rows)

    append_manual_entries(all_rows, manifest_textures, atlas_lookup, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total sprites={len(all_rows)} cropped={sum(1 for row in all_rows if row.get('crop_png'))}")
    print(f"manifest: {out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
