from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path("autochess_dump")
TRAMMELS_STRINGS_TSV = ROOT / "AutoChessTrammelsDataTable.strings.tsv"
ROLE_RECORDS_JSON = ROOT / "organized_role_data" / "role_table_records.json"
OUT_DIR = ROOT / "organized_factions"

FACTION_ORDER = [
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
]

KEYWORD_CATEGORY = {
    "山海经": "成长",
    "隐袭": "消灭",
    "保卫者": "护盾",
    "幽灵": "生化幽灵",
    "HeartShot": "快手",
    "潜伏者": "飞刀",
    "谍报特工": "不动",
    "审判之眼": "商店",
    "鸿运星光": "金币",
    "核心兵器": "协同",
    "葫芦娃": "召唤",
    "铠甲勇士": "变身",
}

FACTION_NAME_ALIASES = {
    "审判之言": "审判之眼",
}

ROLE_ID_RE = re.compile(r"\b(11[23]\d{2})\b")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
MEANINGFUL_TEXT_TOKENS = {
    "获得",
    "角色",
    "战斗",
    "场上",
    "召唤",
    "永久",
    "触发",
    "攻击",
    "生命",
    "伤害",
    "金币",
    "护盾",
    "成长",
    "消灭",
    "快手",
    "遗言",
    "回合",
    "商店",
    "协同",
    "晶石",
    "属性",
    "友方",
    "敌方",
    "阵亡",
    "使用",
    "变身",
    "每有",
    "额外",
    "生化幽灵",
    "钢铁终结者",
    "葫芦娃",
    "爷爷",
}


def load_tsv_values(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return [
            {"index": int(row["index"]), "value": row["value"].strip()}
            for row in reader
            if row.get("value", "").strip()
        ]


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def unique_keep_order(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def clean_text(value: str) -> str:
    value = value.strip().rstrip(",")
    value = re.sub(r"(?<=[\u4e00-\u9fff\d%>])(?:[<>]?[A-Za-z]{1,2}|[<>])$", "", value)
    return value.strip().rstrip(",")


def is_noise(value: str) -> bool:
    if not value:
        return True
    if value.startswith("角色羁绊"):
        return True
    if value in {"globalgamemanagers", "assets", "AutoChessTrammelsDataTable"}:
        return True
    if ROLE_ID_RE.fullmatch(value):
        return True
    if re.fullmatch(r"[0-9]+(?:,[0-9]+)+", value):
        return True
    if re.fullmatch(r"[A-Za-z/]+", value):
        return True
    if re.fullmatch(r"\d+[A-Za-z]+", value):
        return True
    return False


def is_meaningful_text(value: str) -> bool:
    if not CHINESE_RE.search(value):
        return False
    return any(token in value for token in MEANINGFUL_TEXT_TOKENS)


def build_role_id_map() -> dict[int, str]:
    records = load_json(ROLE_RECORDS_JSON, [])
    return {
        int(record["inferred_role_id"]): record["name"]
        for record in records
        if record.get("inferred_role_id") and record.get("name")
    }


def parse_factions() -> list[dict]:
    values = load_tsv_values(TRAMMELS_STRINGS_TSV)
    faction_names = set(FACTION_ORDER)
    role_id_to_name = build_role_id_map()

    sections = []
    current = None
    for row in values:
        value = FACTION_NAME_ALIASES.get(row["value"], row["value"])
        if value in faction_names:
            if current:
                sections.append(current)
            current = {"name": value, "start_index": row["index"], "rows": []}
            continue
        if current:
            current["rows"].append({"index": row["index"], "value": row["value"]})
    if current:
        sections.append(current)

    output = []
    for section in sections:
        role_ids = []
        text_values = []

        for row in section["rows"]:
            value = clean_text(row["value"])
            for match in ROLE_ID_RE.findall(value):
                role_id = int(match)
                # Trammel effect parameters can include a summoned role id; keep it out
                # of the faction member list when the row is a multi-field effect config.
                if "," not in value:
                    role_ids.append(role_id)
            if is_noise(value):
                continue
            if is_meaningful_text(value) or section["name"] == "HeartShot":
                text_values.append(value)

        text_values = unique_keep_order(text_values)
        role_ids = unique_keep_order(role_ids)
        description = text_values[0] if text_values else None
        stage_effects = text_values[1:] if len(text_values) > 1 else []

        output.append(
            {
                "name": section["name"],
                "keyword_category": KEYWORD_CATEGORY.get(section["name"]),
                "description": description,
                "stage_effects": stage_effects,
                "role_ids": role_ids,
                "roles": [
                    {
                        "role_id": role_id,
                        "name": role_id_to_name.get(role_id),
                        "name_source": "inferred_by_role_table_order" if role_id in role_id_to_name else None,
                    }
                    for role_id in role_ids
                ],
                "source_table": "AutoChessTrammelsDataTable",
                "source_start_index": section["start_index"],
                "raw_values": [row["value"] for row in section["rows"]],
            }
        )

    order = {name: i for i, name in enumerate(FACTION_ORDER)}
    output.sort(key=lambda item: order.get(item["name"], 999))
    return output


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    factions = parse_factions()

    (OUT_DIR / "factions_data.json").write_text(
        json.dumps(factions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    fields = [
        "name",
        "keyword_category",
        "description",
        "stage_effects",
        "role_ids",
        "role_names",
        "source_start_index",
    ]
    with (OUT_DIR / "factions_data.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for faction in factions:
            writer.writerow(
                {
                    "name": faction["name"],
                    "keyword_category": faction["keyword_category"],
                    "description": faction["description"],
                    "stage_effects": " | ".join(faction["stage_effects"]),
                    "role_ids": " | ".join(str(role_id) for role_id in faction["role_ids"]),
                    "role_names": " | ".join(
                        role["name"] or f"UNKNOWN_{role['role_id']}" for role in faction["roles"]
                    ),
                    "source_start_index": faction["source_start_index"],
                }
            )

    print(f"wrote {OUT_DIR / 'factions_data.json'}")
    print(f"factions: {len(factions)}")
    for faction in factions:
        print(
            f"{faction['name']}: {faction['keyword_category']} / "
            f"{faction['description']} / roles={len(faction['role_ids'])}"
        )


if __name__ == "__main__":
    main()
