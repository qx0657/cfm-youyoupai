from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path("autochess_dump")
WEAPON_STRINGS_TSV = ROOT / "AutoChessWeaponDataTable.strings.tsv"
WEAPONS_MANIFEST = ROOT / "organized_weapons" / "weapons_manifest.json"
WEAPON_PREVIEW_DATA = ROOT / "organized_weapon_card_previews" / "weapon_card_data.json"
OUT_DIR = ROOT / "organized_weapon_data"

KEYWORD_RE = re.compile(r"<KeyWord>(.*?)</KeyWord>")
TAG_RE = re.compile(r"</?(?:KeyWord|Label|LabelTex)>")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

NAME_TO_RESOURCE = {
    "81式-瑜": "Icon_ZiZouQi_WuQi_81_yu",
    "9A91-魔蜥": "Icon_ZiZouQi_WuQi_9A91_moxi",
    "A180-地狱凤凰": "Icon_ZiZouQi_WuQi_A180_DiYuFengHuang",
    "AK12-天启": "Icon_ZiZouQi_WuQi_AK12_TianQi",
    "AK47-奉先": "Icon_ZiZouQi_WuQi_AK47_FengXian",
    "AK47-无影": "Icon_ZiZouQi_WuQi_AK47_WuYing",
    "AK47-元让": "Icon_ZiZouQi_WuQi_AK47_YuanRang",
    "AK47-火麒麟": "Icon_ZiZouQi_WuQi_AK47_huoqilin",
    "AN94-超新星": "Icon_ZiZouQi_WuQi_AN94_chaoxinxing",
    "AWM-天龙": "Icon_ZiZouQi_WuQi_AWM_tianlong",
    "CBJ-MS-毒蜂": "Icon_ZiZouQi_WuQi_CBJ_DuFeng",
    "CZS2-善财童子": "Icon_ZiZouQi_WuQi_CZS2_shancaitongzi",
    "HK416-极光": "Icon_ZiZouQi_WuQi_HK416_jiguang",
    "黑龙魂": "Icon_ZiZouQi_WuQi_HeiLongHun",
    "极光剑": "Icon_ZiZouQi_WuQi_JiGuangJian",
    "加特林-堡垒": "Icon_ZiZouQi_WuQi_JiaTeLin_BaoLei03",
    "KAC-变色龙": "Icon_ZiZouQi_WuQi_KAC_bianselong",
    "KSG-黑骑士": "Icon_ZiZouQi_WuQi_KSG_heiqishi",
    "烈焰刀": "Icon_ZiZouQi_WuQi_LieYanDao",
    "M1216-血月": "Icon_ZiZouQi_WuQi_M1216_xueyue",
    "M14EBR-暗夜": "Icon_ZiZouQi_WuQi_M14EBR_anye",
    "M200-幻神": "Icon_ZiZouQi_WuQi_M200_huanshen",
    "M249-追猎": "Icon_ZiZouQi_WuQi_M249_zuilie",
    "M4A1-星象": "Icon_ZiZouQi_WuQi_M4A1_XingXiang",
    "M4A1-雷神": "Icon_ZiZouQi_WuQi_M4A1_leishen",
    "MG3-雏凤": "Icon_ZiZouQi_WuQi_MG3_chufeng",
    "MK47-云舞": "Icon_ZiZouQi_WuQi_MK47_yunwu",
    "MK5-机械纪元": "Icon_ZiZouQi_WuQi_MK5_jixiejiyuan",
    "P90-突突兔": "Icon_ZiZouQi_WuQi_P90_tututu",
    "QBZ97-岚舞": "Icon_ZiZouQi_WuQi_QBZ97_lanwu",
    "RPK-盘龙": "Icon_ZiZouQi_WuQi_RPK_panlong",
    "Light-白虎": "Icon_ZiZouQi_WuQi_SCAR_Light_baihu",
    "沙漠之鹰-游骑兵": "Icon_ZiZouQi_WuQi_shamozhiying_youqibing",
    "斯泰尔-恶魔": "Icon_ZiZouQi_WuQi_sitaieremo",
    "TAC-晴舞": "Icon_ZiZouQi_WuQi_TAC_qingwu",
    "VEPR12-本初": "Icon_ZiZouQi_WuQi_VEPR12_BenChu",
    "VEPR12-宙斯": "Icon_ZiZouQi_WuQi_VEPR12_zhousi",
    "王者之心": "Icon_ZiZouQi_WuQi_WangZheZhiXin",
    "王者之翼": "Icon_ZiZouQi_WuQi_WangZheZhiYi",
    "巴雷特-毁灭": "Icon_ZiZouQi_WuQi_baleite_huimie",
    "cop": "Icon_ZiZouQi_WuQi_cop",
    "加特林-炼狱": "Icon_ZiZouQi_WuQi_jiatelin_lianyu",
    "刘易斯-天使": "Icon_ZiZouQi_WuQi_liuyisi_tianshi",
    "汤姆逊-烈龙": "Icon_ZiZouQi_WuQi_tomxunlielong",
}
RESOURCE_TO_TABLE_RESOURCE_ALIASES = {
    "Icon_ZiZouQi_WuQi_ShaYing_YouQiBing": "Icon_ZiZouQi_WuQi_shamozhiying_youqibing",
}
FILENAME_NAME_OVERRIDES = {
    "Icon_ZiZouQi_WuQi_An94_QinShi": "AN94-侵蚀",
    "Icon_ZiZouQi_WuQi_HK416_ZhuQue03": "HK416-朱雀",
    "Icon_ZiZouQi_WuQi_JiaTeLin_BaoLeiChe03": "加特林-暴雷车",
    "Icon_ZiZouQi_WuQi_KSG_MengHuo03": "KSG-孟获",
    "Icon_ZiZouQi_WuQi_M16_EMo03": "M16-恶魔",
    "Icon_ZiZouQi_WuQi_MG36_weizhentian": "MG36-威震天",
    "Icon_ZiZouQi_WuQi_MK5_jiguang": "MK5-极光",
    "Icon_ZiZouQi_WuQi_P90_MengHuo03": "P90-孟获",
    "Icon_ZiZouQi_WuQi_SKS_yeding": "SKS-夜鼎",
    "Icon_ZiZouQi_WuQi_SPAS12_qintianzhu": "SPAS12-擎天柱",
    "Icon_ZiZouQi_WuQi_WangMingZhiTu_GuiMeiShuangSheng": "亡命之徒-鬼魅双生",
    "Icon_ZiZouQi_WuQi_WangZheZhiYing": "王者之影",
    "Icon_ZiZouQi_WuQi_cop_LeiTing": "COP-雷霆",
    "Icon_ZiZouQi_WuQi_cop_LeiTingWangZhe": "COP-雷霆王者",
    "Icon_ZiZouQi_WuQi_duomingzhilian": "夺命之镰",
    "Icon_ZiZouQi_WuQi_liuyisi_xueyue": "刘易斯-血月",
    "Icon_ZiZouQi_WuQi_qichui_mojiezuo": "气锤-摩羯座",
    "Icon_ZiZouQi_WuQi_qingtian": "擎天",
    "Icon_ZiZouQi_WuQi_tulong": "屠龙",
}
WEAPON_QUALITY_BY_RESOURCE = {
    "Icon_ZiZouQi_WuQi_MK5_jixiejiyuan": "blue",
    "Icon_ZiZouQi_WuQi_M14EBR_anye": "blue",
    "Icon_ZiZouQi_WuQi_RPK_panlong": "blue",
    "Icon_ZiZouQi_WuQi_MG3_chufeng": "blue",
    "Icon_ZiZouQi_WuQi_CZS2_shancaitongzi": "purple",
    "Icon_ZiZouQi_WuQi_sitaieremo": "purple",
    "Icon_ZiZouQi_WuQi_P90_tututu": "purple",
    "Icon_ZiZouQi_WuQi_AWM_tianlong": "purple",
    "Icon_ZiZouQi_WuQi_M1216_xueyue": "purple",
    "Icon_ZiZouQi_WuQi_AN94_chaoxinxing": "purple",
    "Icon_ZiZouQi_WuQi_M249_zuilie": "purple",
    "Icon_ZiZouQi_WuQi_liuyisi_tianshi": "purple",
    "Icon_ZiZouQi_WuQi_QBZ97_lanwu": "purple",
    "Icon_ZiZouQi_WuQi_TAC_qingwu": "purple",
    "Icon_ZiZouQi_WuQi_9A91_moxi": "purple",
    "Icon_ZiZouQi_WuQi_VEPR12_BenChu": "purple",
    "Icon_ZiZouQi_WuQi_AK47_FengXian": "purple",
    "Icon_ZiZouQi_WuQi_AK47_WuYing": "purple",
    "Icon_ZiZouQi_WuQi_A180_DiYuFengHuang": "purple",
    "Icon_ZiZouQi_WuQi_CBJ_DuFeng": "purple",
    "Icon_ZiZouQi_WuQi_HK416_jiguang": "purple",
    "Icon_ZiZouQi_WuQi_AK12_TianQi": "purple",
    "Icon_ZiZouQi_WuQi_M4A1_XingXiang": "purple",
}
KNOWN_UNMATCHED_WEAPON_NAMES = {
    "宋雨琦默认武器",
    "横扫武器",
}

DESCRIPTION_TOKENS = {
    "攻击",
    "获得",
    "造成",
    "友方",
    "敌方",
    "自身",
    "自己",
    "永久",
    "受到",
    "触发",
    "召唤",
    "武器",
    "免疫",
    "阵亡",
    "战斗",
    "死亡",
    "目标",
    "伤害",
    "金币",
    "护盾",
    "子弹",
    "消灭",
    "遗言",
    "快手",
    "成长",
    "穿透",
    "散射",
    "连续行动",
    "反击",
    "增伤",
    "燃烧",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_tsv_values(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [
            {"index": int(row["index"]), "value": row["value"].strip()}
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


def clean_text(value: str) -> str:
    value = value.strip().rstrip(",")
    value = re.sub(r"(?<=[\u4e00-\u9fff\d%>])(?:[<>]?[A-Za-z]{1,2}|[<>])$", "", value)
    return value.strip().rstrip(",")


def is_noise(value: str) -> bool:
    if not value:
        return True
    if value in {"globalgamemanagers", "assets"}:
        return True
    if re.fullmatch(r"[A-Za-z/<>\\[\\]_-]{1,4}", value):
        return True
    if re.fullmatch(r"-?\d+(?:,\d+)*", value):
        return True
    if re.fullmatch(r"-?\d+[A-Za-z]+", value):
        return True
    if len(value) <= 3 and not CHINESE_RE.search(value):
        return True
    return False


def looks_like_weapon_name(value: str) -> bool:
    return value in NAME_TO_RESOURCE or value in KNOWN_UNMATCHED_WEAPON_NAMES


def looks_like_description(value: str) -> bool:
    if "<KeyWord>" in value:
        return True
    if not CHINESE_RE.search(value):
        return False
    return any(token in value for token in DESCRIPTION_TOKENS)


def looks_like_brief_text(value: str) -> bool:
    if not CHINESE_RE.search(value):
        return False
    return any(token in value for token in DESCRIPTION_TOKENS)


def parse_weapon_records() -> list[dict]:
    values = load_tsv_values(WEAPON_STRINGS_TSV)
    boundaries = []
    for row in values:
        value = clean_text(row["value"])
        if looks_like_weapon_name(value):
            boundaries.append({**row, "value": value})

    records = []
    for record_index, start in enumerate(boundaries):
        end_index = boundaries[record_index + 1]["index"] if record_index + 1 < len(boundaries) else 10**9
        chunk = [row for row in values if start["index"] <= row["index"] < end_index]
        raw_values = [row["value"] for row in chunk]
        descriptions = []
        brief_descriptions = []

        for raw in raw_values[1:]:
            value = clean_text(raw)
            if is_noise(value):
                continue
            if looks_like_weapon_name(value):
                continue
            if looks_like_description(value):
                descriptions.append(value)
            elif looks_like_brief_text(value):
                brief_descriptions.append(value)

        keywords = []
        for desc in descriptions:
            keywords.extend(KEYWORD_RE.findall(desc))

        records.append(
            {
                "weapon_table_index": record_index + 1,
                "name": start["value"],
                "string_start_index": start["index"],
                "string_end_index": chunk[-1]["index"] if chunk else start["index"],
                "keywords": unique_keep_order(keywords),
                "descriptions": unique_keep_order(descriptions),
                "plain_descriptions": unique_keep_order(plain_text(v) for v in descriptions),
                "brief_descriptions": unique_keep_order(brief_descriptions),
                "raw_weapon_table_strings": raw_values,
            }
        )
    return records


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_json(WEAPONS_MANIFEST, [])
    preview_by_resource = {item.get("base_resource"): item for item in load_json(WEAPON_PREVIEW_DATA, []) if item.get("base_resource")}
    records = parse_weapon_records()

    records_by_resource = {}
    for record in records:
        resource = NAME_TO_RESOURCE.get(record["name"])
        if resource:
            records_by_resource[resource] = record

    output = []
    for item in manifest:
        resource = item.get("base_resource")
        table_resource = RESOURCE_TO_TABLE_RESOURCE_ALIASES.get(resource, resource)
        record = records_by_resource.get(table_resource)
        preview = preview_by_resource.get(resource, {})
        fallback_name = FILENAME_NAME_OVERRIDES.get(resource)
        quality = WEAPON_QUALITY_BY_RESOURCE.get(resource) or "gold"
        quality_source = "known_weapon_resource_quality" if resource in WEAPON_QUALITY_BY_RESOURCE else "default_weapon_gold"
        output.append(
            {
                "index": item.get("index"),
                "name": record["name"] if record else fallback_name or resource,
                "base_resource": resource,
                "weapon_resource": item.get("weapon_resource"),
                "weapon_png": item.get("weapon_png"),
                "composited_card_png": preview.get("composited_card_png"),
                "quality": quality,
                "quality_source": quality_source,
                "source_png": item.get("source_png"),
                "atlasAssetName": item.get("atlasAssetName"),
                "keywords": record.get("keywords", []) if record else [],
                "descriptions": record.get("descriptions", []) if record else [],
                "plain_descriptions": record.get("plain_descriptions", []) if record else [],
                "brief_descriptions": record.get("brief_descriptions", []) if record else [],
                "weapon_table_index": record.get("weapon_table_index") if record else None,
                "string_start_index": record.get("string_start_index") if record else None,
                "match_status": "matched_by_manual_resource_alias" if record and table_resource == resource else ("matched_by_resource_alias" if record else ("name_from_apk_filename" if fallback_name else "not_found_in_AutoChessWeaponDataTable_strings")),
            }
        )

    # Keep data-table records that currently do not have a card image match.
    matched_names = {row["name"] for row in output if row["match_status"].startswith("matched")}
    unmatched_records = [record for record in records if record["name"] not in matched_names]

    (OUT_DIR / "weapons_data.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "weapon_table_records.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "weapon_table_unmatched_records.json").write_text(
        json.dumps(unmatched_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_fields = [
        "index",
        "name",
        "base_resource",
        "weapon_png",
        "composited_card_png",
        "quality",
        "keywords",
        "descriptions",
        "plain_descriptions",
        "brief_descriptions",
        "weapon_table_index",
        "match_status",
    ]
    with (OUT_DIR / "weapons_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
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

    matched = sum(1 for row in output if row["match_status"].startswith("matched"))
    print(f"wrote {OUT_DIR / 'weapons_data.json'}")
    print(f"weapon images: {len(output)}, matched_table: {matched}, unmatched_images: {len(output) - matched}")
    print(f"weapon table records parsed: {len(records)}, unmatched_records: {len(unmatched_records)}")


if __name__ == "__main__":
    main()
