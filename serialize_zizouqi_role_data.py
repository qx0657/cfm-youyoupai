from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path("autochess_dump")
ROLES_MANIFEST = ROOT / "organized_roles" / "roles_manifest.json"
ROLE_PREVIEW_DATA = ROOT / "organized_role_card_previews" / "role_card_data.json"
RESOURCE_GUESSES = ROOT / "AutoChessResourceDataTable.resource_name_guesses.json"
ROLE_STRINGS_TSV = ROOT / "AutoChessRoleDataTable.strings.tsv"
TRAMMELS_STRINGS_TSV = ROOT / "AutoChessTrammelsDataTable.strings.tsv"
OUT_DIR = ROOT / "organized_role_data"

ROLE_ID_START = 11201
FACTION_NAMES = {
    "隐袭",
    "保卫者",
    "幽灵",
    "山海经",
    "HeartShot",
    "潜伏者",
    "葫芦娃",
    "谍报特工",
    "审判之眼",
    "铠甲勇士",
    "鸿运星光",
    "核心兵器",
}
RESOURCE_NAME_OVERRIDES = {
    "Icon_ZiZouQi_JueSe_Chan": "蝉",
    "Icon_ZiZouQi_JueSe_DiHuangXia": "帝皇侠",
    "Icon_ZiZouQi_JueSe_FengHuangYiXing": "凤凰异形",
    "Icon_ZiZouQi_JueSe_GaoBaoYiXing": "高爆异形",
    "Icon_ZiZouQi_JueSe_HeiAnJinGang": "黑暗金刚",
    "Icon_ZiZouQi_JueSe_HuiTuiYiXing": "毁腿异形",
    "Icon_ZiZouQi_JueSe_JingZheQingYa": "惊蛰晴雅",
    "Icon_ZiZouQi_JueSe_JiGuanShe": "机关蛇",
    "Icon_ZiZouQi_JueSe_JuDuSheNv": "剧毒蛇女",
    "Icon_ZiZouQi_JueSe_LuZhangYiXing": "路障异形",
    "Icon_ZiZouQi_JueSe_Mulan": "木兰",
    "Icon_ZiZouQi_JueSe_N22_QFZ": "N22",
    "Icon_ZiZouQi_JueSe_PuTongYiXing": "普通异形",
    "Icon_ZiZouQi_JueSe_ShengDanLingHu": "圣诞灵狐",
    "Icon_ZiZouQi_JueSe_SongYuQi": "宋雨琦",
    "Icon_ZiZouQi_JueSe_SunWuKong_QFZ": "孙悟空",
    "Icon_ZiZouQi_JueSe_Tong": "铜",
    "Icon_ZiZouQi_JueSe_WeiZhuangYouLing": "伪装幽灵",
    "Icon_ZiZouQi_JueSe_WuYi": "巫医",
    "Icon_ZiZouQi_JueSe_XiaRiLingHu": "夏日灵狐",
    "Icon_ZiZouQi_JueSe_XiangSuYunYouYou": "像素云悠悠",
    "Icon_ZiZouQi_JueSe_XunJieChong": "迅捷虫",
    "Icon_ZiZouQi_JueSe_YanLongXia": "炎龙侠",
    "Icon_ZiZouQi_JueSe_YaoJi": "妖姬",
    "Icon_ZiZouQi_JueSe_Ying": "樱",
    "Icon_ZiZouQi_JueSe_Youlinglieshou": "幽灵猎手",
    "Icon_ZiZouQi_JueSe_ZhiChangLingHu": "职场灵狐",
    "Icon_ZiZouQi_JueSe_ZhongXiaoKui": "钟小葵",
    "Icon_ZiZouQi_JueSe_ZhuRong": "祝融",
    "Icon_ZiZouQi_JueSe_ZiBaoYiXing": "自爆异形",
    "Icon_ZiZouQi_JueSe_GuanXiaoYu_BWZ": "关小雨",
    "Icon_ZiZouQi_JueSe_Kui_BWZ": "葵",
    "Icon_ZiZouQi_JueSe_Lan": "兰",
    "Icon_ZiZouQi_JueSe_LuoLa": "萝拉",
}
ROLE_QUALITY_BY_RESOURCE = {
    "Icon_ZiZouQi_JueSe_Bosaidong_QFZ": "green",
    "Icon_ZiZouQi_JueSe_Anying_QFZ": "green",
    "Icon_ZiZouQi_JueSe_LvJuRen": "green",
    "Icon_ZiZouQi_JueSe_Luoyi": "green",
    "Icon_ZiZouQi_JueSe_Lan": "green",
    "Icon_ZiZouQi_JueSe_LongYe_QFZ": "green",
    "Icon_ZiZouQi_JueSe_Huanying": "green",
    "Icon_ZiZouQi_JueSe_LingHuZhe_QFZ": "green",
    "Icon_ZiZouQi_JueSe_WuMengMeng_BWZ": "green",
    "Icon_ZiZouQi_JueSe_ShengHuaYouLing": "green",
    "Icon_ZiZouQi_JueSe_SiWoTe_BWZ": "green",
    "Icon_ZiZouQi_JueSe_SiWeiTe_QFZ": "green",
    "Icon_ZiZouQi_JueSe_GaoBaoYiXing": "green",
    "Icon_ZiZouQi_JueSe_HuiTuiYiXing": "green",
    "Icon_ZiZouQi_JueSe_LuZhangYiXing": "green",
    "Icon_ZiZouQi_JueSe_PuTongYiXing": "green",
    "Icon_ZiZouQi_JueSe_ZiBaoYiXing": "green",
    "Icon_ZiZouQi_JueSe_HeiHuaGe1": "red",
    "Icon_ZiZouQi_JueSe_HeiHuaGe2": "red",
    "Icon_ZiZouQi_JueSe_N22_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_Yadianna_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_Shuxue_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_QianLongDui_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_MaQue_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_Chitianshi_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_NaTaSha_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_Ying": "blue",
    "Icon_ZiZouQi_JueSe_Saisi_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_Kui_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_Lieying_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_TieQi_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_YuMo_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_FengKuangBaoBei": "blue",
    "Icon_ZiZouQi_JueSe_LingHunRenZhe": "blue",
    "Icon_ZiZouQi_JueSe_GuLang_QFZ": "blue",
    "Icon_ZiZouQi_JueSe_SaiSi_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_Yangyuning_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_GuanXiaoYu_BWZ": "blue",
    "Icon_ZiZouQi_JueSe_XunJieChong": "blue",
    "Icon_ZiZouQi_JueSe_FengHuangYiXing": "purple",
    "Icon_ZiZouQi_JueSe_JuDuSheNv": "purple",
    "Icon_ZiZouQi_JueSe_WuYi": "purple",
    "Icon_ZiZouQi_JueSe_WeiZhuangYouLing": "purple",
    "Icon_ZiZouQi_JueSe_YeMeiGui_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_Duotianshi": "purple",
    "Icon_ZiZouQi_JueSe_Yueshen_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_Taiyangshen_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_MoYiLong": "purple",
    "Icon_ZiZouQi_JueSe_Fuchouzhe_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_WuMeiYaoJi_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_Chan": "purple",
    "Icon_ZiZouQi_JueSe_BaiLang_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_LanXiEr_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_BianYiBaoBei": "purple",
    "Icon_ZiZouQi_JueSe_PanDuoLa_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_CaiWenZhao_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_Lingxiao_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_LingDongWuShi_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_JiuWeiHu_BWZ": "purple",
    "Icon_ZiZouQi_JueSe_LongMei_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_Chun": "purple",
    "Icon_ZiZouQi_JueSe_LuoKe_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_LuoLa": "purple",
    "Icon_ZiZouQi_JueSe_LuoLa_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_HuDie_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_NvMei_QFZ": "purple",
    "Icon_ZiZouQi_JueSe_JiGuanShe": "purple",
}
ROLE_RECORD_NAME_ALIASES = {
}

KEYWORD_RE = re.compile(r"<KeyWord>(.*?)</KeyWord>")
TAG_RE = re.compile(r"</?(?:KeyWord|Label|LabelTex)>")
ROLE_ID_RE = re.compile(r"\b(11[23]\d{2})\b")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
ROLE_NAME_BLOCKLIST = {"坦克", "输出", "辅助", "角色羁绊"}
ROLE_NAME_TEXT_TOKENS = {
    "友方",
    "敌方",
    "获得",
    "造成",
    "触发",
    "永久",
    "攻击",
    "生命",
    "受到",
    "同排",
    "自身",
    "自己",
    "随机",
    "回合",
    "战斗",
    "角色",
    "护盾",
    "消灭",
    "遗言",
    "快手",
    "成长",
    "伤害",
    "召唤",
    "场上",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_tsv_values(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [
            {
                "index": int(row["index"]),
                "value": row["value"].strip(),
            }
            for row in reader
            if row.get("value", "").strip()
        ]


def unique_keep_order(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def plain_text(value: str) -> str:
    return TAG_RE.sub("", value).strip()


def clean_desc(value: str) -> str:
    value = value.strip().rstrip(",")
    # Raw extraction occasionally keeps one or two dangling binary-looking bytes.
    value = re.sub(r"(?<=[\u4e00-\u9fff\d>])(?:[<>]?[A-Za-z]{1,2}|[<>])$", "", value)
    return value.strip().rstrip(",")


def is_probable_role_resource(resource: str) -> bool:
    if not resource.startswith("Icon_ZiZouQi_JueSe_"):
        return False
    return not resource.endswith("_S")


def build_resource_name_map() -> dict[str, str]:
    mapping = {}
    for item in load_json(RESOURCE_GUESSES, []):
        resource = item.get("resource", "")
        name = item.get("display_name_guess", "")
        if is_probable_role_resource(resource) and name:
            mapping[resource] = RESOURCE_NAME_OVERRIDES.get(resource, name)
    mapping.update(RESOURCE_NAME_OVERRIDES)
    return mapping


def build_preview_map() -> dict[str, dict]:
    preview_map = {}
    for item in load_json(ROLE_PREVIEW_DATA, []):
        resource = item.get("role_resource")
        if resource:
            preview_map[resource] = item
    return preview_map


def looks_like_description(value: str, known_names: set[str]) -> bool:
    if value in known_names:
        return False
    if "<KeyWord>" in value:
        return True
    if not CHINESE_RE.search(value):
        return False
    return any(token in value for token in ("获得", "触发", "造成", "召唤", "永久", "攻击", "生命", "护盾", "消灭", "遗言", "快手", "成长", "伤害", "友方", "敌方", "回合", "战斗"))


def looks_like_role_name(value: str, known_names: set[str]) -> bool:
    if value in known_names:
        return True
    if value in ROLE_NAME_BLOCKLIST:
        return False
    if not CHINESE_RE.search(value):
        return False
    if "<" in value or ">" in value or "：" in value or "," in value:
        return False
    if any(token in value for token in ROLE_NAME_TEXT_TOKENS):
        return False
    return 2 <= len(value) <= 6


def parse_role_records(known_names: set[str]) -> list[dict]:
    values = load_tsv_values(ROLE_STRINGS_TSV)
    boundaries = []
    for row in values:
        value = row["value"]
        if looks_like_role_name(value, known_names):
            boundaries.append(row)

    records = []
    for record_index, start in enumerate(boundaries):
        end_index = boundaries[record_index + 1]["index"] if record_index + 1 < len(boundaries) else 10**9
        chunk = [row for row in values if start["index"] <= row["index"] < end_index]
        raw_values = [row["value"] for row in chunk]

        descriptions = []
        brief_descriptions = []
        for value in raw_values[1:]:
            cleaned = clean_desc(value)
            if not cleaned:
                continue
            if looks_like_description(cleaned, known_names):
                descriptions.append(cleaned)
            elif CHINESE_RE.search(cleaned) and ("+" in cleaned or cleaned.startswith("获得")):
                brief_descriptions.append(cleaned)

        keywords = []
        for desc in descriptions:
            keywords.extend(KEYWORD_RE.findall(desc))

        inferred_id = ROLE_ID_START + record_index
        records.append(
            {
                "role_table_index": record_index + 1,
                "inferred_role_id": inferred_id,
                "name": start["value"],
                "string_start_index": start["index"],
                "string_end_index": chunk[-1]["index"] if chunk else start["index"],
                "keywords": unique_keep_order(keywords),
                "descriptions": unique_keep_order(descriptions),
                "plain_descriptions": unique_keep_order(plain_text(v) for v in descriptions),
                "brief_descriptions": unique_keep_order(clean_desc(v) for v in brief_descriptions),
                "raw_role_table_strings": raw_values,
                "id_source": "inferred_by_role_table_order_starting_at_11201",
            }
        )
    return records


def parse_factions_by_role_id() -> dict[int, list[str]]:
    values = load_tsv_values(TRAMMELS_STRINGS_TSV)
    current_faction = None
    role_id_to_factions: dict[int, list[str]] = defaultdict(list)

    for row in values:
        value = row["value"]
        if value in FACTION_NAMES:
            current_faction = value
            continue
        if not current_faction:
            continue
        for match in ROLE_ID_RE.findall(value):
            role_id = int(match)
            if current_faction not in role_id_to_factions[role_id]:
                role_id_to_factions[role_id].append(current_faction)

    return dict(role_id_to_factions)


def infer_role_quality(resource: str) -> tuple[str | None, str | None]:
    quality = ROLE_QUALITY_BY_RESOURCE.get(resource)
    if quality:
        return quality, "known_role_resource_quality"
    return None, None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    roles_manifest = load_json(ROLES_MANIFEST, [])
    resource_name_map = build_resource_name_map()
    preview_map = build_preview_map()

    known_names = {
        name
        for name in resource_name_map.values()
        if name and not name.startswith("Icon_")
    }
    known_names.update(
        item["name"]
        for item in roles_manifest
        if item.get("name") and not item["name"].startswith("Icon_")
    )

    role_records = parse_role_records(known_names)
    records_by_name: dict[str, list[dict]] = defaultdict(list)
    for record in role_records:
        records_by_name[record["name"]].append(record)

    factions_by_role_id = parse_factions_by_role_id()
    output = []

    for item in roles_manifest:
        resource = item.get("role_resource", "")
        display_name = resource_name_map.get(resource) or item.get("name", resource)
        role_record = records_by_name.get(display_name, [None])[0]
        if role_record is None and display_name in ROLE_RECORD_NAME_ALIASES:
            role_record = records_by_name.get(ROLE_RECORD_NAME_ALIASES[display_name], [None])[0]
        preview = preview_map.get(resource, {})
        inferred_quality, inferred_quality_source = infer_role_quality(resource)

        inferred_role_id = role_record.get("inferred_role_id") if role_record else None
        factions = factions_by_role_id.get(inferred_role_id, []) if inferred_role_id else []

        output.append(
            {
                "index": item.get("index"),
                "name": display_name,
                "role_resource": resource,
                "role_png": item.get("role_png"),
                "avatar_resource": item.get("avatar_resource"),
                "avatar_png": item.get("avatar_png"),
                "has_avatar": bool(item.get("has_avatar")),
                "composited_card_png": preview.get("composited_card_png"),
                "gold_composited_card_png": preview.get("gold_composited_card_png"),
                "quality": inferred_quality or "gold",
                "quality_source": inferred_quality_source or "default_missing_quality",
                "factions": factions,
                "faction_source": "inferred_by_role_id_from_AutoChessTrammelsDataTable" if factions else None,
                "keywords": role_record.get("keywords", []) if role_record else [],
                "descriptions": role_record.get("descriptions", []) if role_record else [],
                "plain_descriptions": role_record.get("plain_descriptions", []) if role_record else [],
                "brief_descriptions": role_record.get("brief_descriptions", []) if role_record else [],
                "role_table_index": role_record.get("role_table_index") if role_record else None,
                "inferred_role_id": inferred_role_id,
                "role_table_match_status": "matched_by_display_name" if role_record else "not_found_in_AutoChessRoleDataTable_strings",
            }
        )

    (OUT_DIR / "roles_data.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "role_table_records.json").write_text(
        json.dumps(role_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_fields = [
        "index",
        "name",
        "role_resource",
        "role_png",
        "avatar_resource",
        "avatar_png",
        "composited_card_png",
        "gold_composited_card_png",
        "quality",
        "factions",
        "keywords",
        "descriptions",
        "plain_descriptions",
        "brief_descriptions",
        "role_table_index",
        "inferred_role_id",
        "role_table_match_status",
    ]
    with (OUT_DIR / "roles_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for row in output:
            csv_row = {}
            for field in csv_fields:
                value = row.get(field)
                if isinstance(value, list):
                    value = " | ".join(str(v) for v in value)
                csv_row[field] = value
            writer.writerow(csv_row)

    matched = sum(1 for row in output if row["role_table_match_status"].startswith("matched"))
    with_faction = sum(1 for row in output if row["factions"])
    print(f"wrote {OUT_DIR / 'roles_data.json'}")
    print(f"roles: {len(output)}, matched_role_table: {matched}, with_faction: {with_faction}")
    print(f"role table records parsed: {len(role_records)}")


if __name__ == "__main__":
    main()
