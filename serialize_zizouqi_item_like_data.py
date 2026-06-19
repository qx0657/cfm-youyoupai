from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path("autochess_dump")
ITEM_STRINGS_TSV = ROOT / "AutoChessItemDataTable.strings.tsv"

THROWABLES_MANIFEST = ROOT / "organized_throwables" / "throwables_manifest.json"
THROWABLE_CARD_DATA = ROOT / "organized_throwable_card_previews" / "throwable_card_data.json"
ITEMS_MANIFEST = ROOT / "organized_items" / "items_manifest.json"
ITEM_CARD_DATA = ROOT / "organized_item_card_previews" / "item_card_data.json"
CONSUMES_MANIFEST = ROOT / "organized_consume_buffs" / "consume_cards_manifest.json"
CONSUME_CARD_DATA = ROOT / "organized_consume_card_previews" / "consume_card_data.json"
BUFFS_MANIFEST = ROOT / "organized_consume_buffs" / "buff_cards_manifest.json"

OUT_ROOT = ROOT

KEYWORD_RE = re.compile(r"<KeyWord>(.*?)</KeyWord>")
TAG_RE = re.compile(r"</?(?:KeyWord|Label|LabelTex)>")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")

QUALITY_ALIASES = {
    "BLUE": "blue",
    "Blue": "blue",
    "PURPLE": "purple",
    "Purple": "purple",
    "GOLD": "gold",
    "Golden": "gold",
}

THROWABLE_NAME_TO_RESOURCE = {
    "王者之翼手雷": "Icon_ZiZouQi_DaoJu_Wangzhezhiyi",
    "雷霆王者闪光弹": "Icon_ZiZouQi_DaoJu_Wangzhezhisuo",
    "王者之势烟雾弹": "Icon_ZiZouQi_DaoJu_Wangzhezhishi",
    "烛九阴燃烧弹": "Icon_ZiZouQi_DaoJu_Zujiuying",
    "手雷": "Icon_ZiZouQi_DaoJu_putongshoulei",
}

ITEM_NAME_TO_RESOURCE = {
    "肾上腺素": "Icon_ZiZouQi_DaoJu_zhusheqi",
    "医疗枪": "Icon_ZiZouQi_DaoJu_yiliaoqiang",
    "枪口补偿器": "Icon_ZiZouQi_DaoJu_Buqiangbuchangqi",
    "垂直握把": "Icon_ZiZouQi_DaoJu_chuizhiwoba",
    "八倍镜": "Icon_ZiZouQi_DaoJu_babeijing",
    "经验卡": "Icon_ZiZouQi_DaoJu_jingyanka",
    "防弹衣": "Icon_ZiZouQi_DaoJu_fangdanyi",
    "盾牌": "Icon_ZiZouQi_DaoJu_Dunpai",
    "狗头头套": "Icon_ZiZouQi_DaoJu_goutou",
    "弹夹": "Icon_ZiZouQi_DaoJu_buqiangdanjia",
    "背包": "Icon_ZiZouQi_DaoJu_beibao",
    "医疗包": "Icon_ZiZouQi_DaoJu_yiliaobao",
    "高级防弹衣": "Icon_ZiZouQi_DaoJu_gaojifangdanyi",
    "鸟头头套": "Icon_ZiZouQi_DaoJu_niaotoutoutao",
    "紫金头饰": "Icon_ZiZouQi_DaoJu_zijintou",
    "穿透弹": "Icon_ZiZouQi_DaoJu_zidan",
    "爆头挂饰": "Icon_ZiZouQi_DaoJu_baotouguajian",
    "猴头头套": "Icon_ZiZouQi_DaoJu_HouTou",
    "泰坦面饰": "Icon_ZiZouQi_DaoJu_TaiTanTouShi",
    "龙腾之力玩偶": "Icon_ZiZouQi_DaoJu_LongTengZhiLi",
    "凤凰戒指": "Icon_ZiZouQi_DaoJu_FengHuang",
    "炎龙晶石": "Icon_ZiZouQi_DaoJu_YanLongGuaShi",
    "风鹰晶石": "Icon_ZiZouQi_DaoJu_FengYingGuaShi",
    "黑犀晶石": "Icon_ZiZouQi_DaoJu_HeiXiGuaShi",
    "地虎晶石": "Icon_ZiZouQi_DaoJu_MiaoBianGuaShi",
    "雪獒晶石": "Icon_ZiZouQi_DaoJu_XueAoGuaShi",
    "麦克风": "Icon_ZiZouQi_DaoJu_MaiKeFeng",
}

CONSUME_NAME_TO_TOKEN = {
    "免费门票": "ShuaXin",
    "免费门票+": "ShuaXin",
    "队员集结": "TiaoXuan",
    "意外之财": "JinBi",
    "意外之财+": "JinBi",
    "意外之财++": "JinBi",
    "武器仓库": "BaoXiang",
    "防御加固": "TouKui",
    "及时支援+": "NiuDan",
    "及时支援": "NiuDan",
    "随意开火": "DanJia",
    "经验主义": "JingYan",
    "经验主义+": "JingYan",
    "快速升阶+": "JingYan",
    "快速升阶": "JingYan",
    "稳健射击+": "ZengShang",
    "稳健射击": "ZengShang",
    "稳健射击++": "ZengShang",
    "武器轮抽": "ChouJiang",
    "道具批发商": "BeiBao",
    "各司其职++": "ShuangShuXing",
    "各司其职+": "ShuangShuXing",
    "各司其职": "ShuangShuXing",
    "异能之力": "MoFang",
    "卡牌多多": "KaPai",
    "替补登场": "DianTai",
    "盾墙": "DunPai",
    "点金手": "JieZhi",
    "战场回收": "XuanShang",
    "资金储备": "JinBi",
    "后备能源": "FanJi",
    "噬魂": "XuanShang",
    "成长性": "XinPian",
    "营养均衡": "ShengHuaBaoShi",
    "龙映山海": "ZhiYuan",
    "幽临城下": "ZhiYuan",
    "斩首行动": "ZhiYuan",
    "舞台时刻": "ZhiYuan",
}

BUFF_NAME_TO_TOKEN = {
    "免费门票": "MianFeiShuaXin",
    "免费门票+": "MianFeiShuaXin",
    "队员集结": "NvTuan",
    "意外之财": "JinBi",
    "意外之财+": "JinBi",
    "意外之财++": "JinBi",
    "武器仓库": "BaoXiang",
    "防御加固": "TouKui",
    "及时支援+": "FuZhiJueSe",
    "及时支援": "FuZhiJueSe",
    "随意开火": "DanJia",
    "经验主义": "JingYan",
    "经验主义+": "JingYan",
    "快速升阶+": "JingYan",
    "快速升阶": "JingYan",
    "稳健射击+": "ZengShang",
    "稳健射击": "ZengShang",
    "稳健射击++": "ZengShang",
    "武器轮抽": "XiaoHao",
    "道具批发商": "DaoJuWei",
    "各司其职++": "ShuangShuXing",
    "各司其职+": "ShuangShuXing",
    "各司其职": "ShuangShuXing",
    "异能之力": "XiaoHao",
    "卡牌多多": "XiaoHao",
    "替补登场": "DianTai",
    "盾墙": "HuDun",
    "点金手": "DianJin",
    "战场回收": "XiaoHao",
    "资金储备": "JinBi",
    "后备能源": "YiYan",
    "噬魂": "JiSha",
    "成长性": "ChengZhang",
    "营养均衡": "XueLiang",
    "龙映山海": "ChengZhang",
    "幽临城下": "YiYan",
    "斩首行动": "JiSha",
}
BUFF_RESOURCE_TO_NAME_OVERRIDES = {
    "Icon_ZiZouQi_RL_FangDanYi_Blue": "防弹衣",
    "Icon_ZiZouQi_RL_FangDanYi_Golden": "防弹衣",
    "Icon_ZiZouQi_RL_FangDanYi_Purple": "防弹衣",
    "Icon_ZiZouQi_RL_GuanTou_Golden": "罐头",
    "Icon_ZiZouQi_RL_GuanTou_Purple": "罐头",
    "Icon_ZiZouQi_RL_kuaishou_Blue": "快手",
    "Icon_ZiZouQi_RL_kuaishou_Golden": "快手",
    "Icon_ZiZouQi_RL_kuaishou_Purple": "快手",
}

FILENAME_NAME_OVERRIDES = {
    "Icon_ZiZouQi_DaoJu_Guangxuemiaozhunjing": "光学瞄准镜",
    "Icon_ZiZouQi_DaoJu_HuMuJing": "护目镜",
    "Icon_ZiZouQi_DaoJu_HuangJinGaoBao": "黄金高爆",
    "Icon_ZiZouQi_DaoJu_MoLong": "魔龙",
    "Icon_ZiZouQi_DaoJu_NvHuangBeiShi": "女皇背饰",
    "Icon_ZiZouQi_DaoJu_QiangTuo": "枪托",
    "Icon_ZiZouQi_DaoJu_fangdantoukui": "防弹头盔",
    "Icon_ZiZouQi_DaoJu_gaojibeibao": "高级背包",
    "Icon_ZiZouQi_DaoJu_gaojidanjia": "高级弹夹",
    "Icon_ZiZouQi_DaoJu_gaojifangdantoukui": "高级防弹头盔",
    "Icon_ZiZouQi_DaoJu_hongbaijiC4": "红白机 C4",
    "Icon_ZiZouQi_DaoJu_huangjinniudan": "黄金扭蛋",
    "Icon_ZiZouQi_DaoJu_huoqilingbaoxiang": "火麒麟宝箱",
    "Icon_ZiZouQi_DaoJu_jiezhi": "戒指",
    "Icon_ZiZouQi_DaoJu_jiyinxinpian": "基因芯片",
    "Icon_ZiZouQi_DaoJu_jiyinyaoji": "基因药剂",
    "Icon_ZiZouQi_DaoJu_kuanggongmao": "矿工帽",
    "Icon_ZiZouQi_DaoJu_nvbaxianglian": "女娲项链",
    "Icon_ZiZouQi_DaoJu_shenghuabaoshi": "生化宝石",
    "Icon_ZiZouQi_DaoJu_sibeijing": "四倍镜",
    "Icon_ZiZouQi_DaoJu_wuseyu": "五色羽",
    "Icon_ZiZouQi_DaoJu_wusezhu": "五色珠",
    "Icon_ZiZouQi_DaoJu_xiaomieyinxiaoka": "消灭营销卡",
    "Icon_ZiZouQi_DaoJu_zhulongtou": "烛龙头",
    "Icon_ZiZouQi_DaoJu_putongranshaodan": "燃烧弹",
    "Icon_ZiZouQi_DaoJu_putongshanguangdan": "闪光弹",
    "Icon_ZiZouQi_DaoJu_putongyanwudan": "烟雾弹",
    "Icon_ZiZouQi_Weapon_WZZY_ZiDianRongYan": "紫电熔岩",
    "Icon_ZiZouQi_XiaoHao_C4_BLUE": "C4",
    "Icon_ZiZouQi_XiaoHao_C4_GOLD": "C4",
    "Icon_ZiZouQi_XiaoHao_C4_PURPLE": "C4",
    "Icon_ZiZouQi_XiaoHao_FengMoTie_BLUE": "封魔贴",
    "Icon_ZiZouQi_XiaoHao_FengMoTie_GOLD": "封魔贴",
    "Icon_ZiZouQi_XiaoHao_FengMoTie_PURPLE": "封魔贴",
    "Icon_ZiZouQi_XiaoHao_HuoZai_BLUE": "火灾",
    "Icon_ZiZouQi_XiaoHao_HuoZai_GOLD": "火灾",
    "Icon_ZiZouQi_XiaoHao_HuoZai_PURPLE": "火灾",
    "Icon_ZiZouQi_XiaoHao_MianJu_BLUE": "面具",
    "Icon_ZiZouQi_XiaoHao_MianJu_GOLD": "面具",
    "Icon_ZiZouQi_XiaoHao_MianJu_PURPLE": "面具",
    "Icon_ZiZouQi_XiaoHao_ShuJu_BLUE": "数据",
    "Icon_ZiZouQi_XiaoHao_ShuJu_GOLD": "数据",
    "Icon_ZiZouQi_XiaoHao_ShuJu_PURPLE": "数据",
    "Icon_ZiZouQi_XiaoHao_WeiZhuang_BLUE": "伪装",
    "Icon_ZiZouQi_XiaoHao_WeiZhuang_GOLD": "伪装",
    "Icon_ZiZouQi_XiaoHao_WeiZhuang_PURPLE": "伪装",
    "Icon_ZiZouQi_XiaoHao_XiangLian_BLUE": "项链",
    "Icon_ZiZouQi_XiaoHao_XiangLian_GOLD": "项链",
    "Icon_ZiZouQi_XiaoHao_XiangLian_PURPLE": "项链",
    "Icon_ZiZouQi_XiaoHao_XiaoHuangYa_BLUE": "小黄鸭",
    "Icon_ZiZouQi_XiaoHao_XiaoHuangYa_GOLD": "小黄鸭",
    "Icon_ZiZouQi_XiaoHao_XiaoHuangYa_PURPLE": "小黄鸭",
    "Icon_ZiZouQi_XiaoHao_XinPian2_BLUE": "芯片",
    "Icon_ZiZouQi_XiaoHao_XinPian2_GOLD": "芯片",
    "Icon_ZiZouQi_XiaoHao_XinPian2_PURPLE": "芯片",
    "Icon_ZiZouQi_XiaoHao_YaoJi_BLUE": "药剂",
    "Icon_ZiZouQi_XiaoHao_YaoJi_GOLD": "药剂",
    "Icon_ZiZouQi_XiaoHao_YaoJi_PURPLE": "药剂",
    "Icon_ZiZouQi_XiaoHao_ZiDan_BLUE": "子弹",
    "Icon_ZiZouQi_XiaoHao_ZiDan_GOLD": "子弹",
    "Icon_ZiZouQi_XiaoHao_ZiDan_PURPLE": "子弹",
    "Icon_ZiZouQi_XiaoHao_ZuoLun_BLUE": "左轮",
    "Icon_ZiZouQi_XiaoHao_ZuoLun_GOLD": "左轮",
    "Icon_ZiZouQi_XiaoHao_ZuoLun_PURPLE": "左轮",
}
THROWABLE_QUALITY_BY_RESOURCE = {
    "Icon_ZiZouQi_DaoJu_putongshoulei": "blue",
    "Icon_ZiZouQi_DaoJu_putongshanguangdan": "blue",
    "Icon_ZiZouQi_DaoJu_putongyanwudan": "blue",
    "Icon_ZiZouQi_DaoJu_putongranshaodan": "blue",
}
ITEM_QUALITY_BY_RESOURCE = {
    "Icon_ZiZouQi_DaoJu_zidan": "blue",
    "Icon_ZiZouQi_DaoJu_fangdanyi": "blue",
    "Icon_ZiZouQi_DaoJu_jingyanka": "blue",
    "Icon_ZiZouQi_DaoJu_chuizhiwoba": "blue",
    "Icon_ZiZouQi_DaoJu_yiliaoqiang": "blue",
    "Icon_ZiZouQi_DaoJu_zhusheqi": "blue",
    "Icon_ZiZouQi_DaoJu_Buqiangbuchangqi": "purple",
    "Icon_ZiZouQi_DaoJu_babeijing": "purple",
    "Icon_ZiZouQi_DaoJu_Dunpai": "purple",
    "Icon_ZiZouQi_DaoJu_goutou": "purple",
    "Icon_ZiZouQi_DaoJu_yiliaobao": "purple",
    "Icon_ZiZouQi_DaoJu_HouTou": "purple",
}

KNOWN_RECORD_NAMES = set(THROWABLE_NAME_TO_RESOURCE) | set(ITEM_NAME_TO_RESOURCE) | set(CONSUME_NAME_TO_TOKEN) | {
    "运输船",
    "沙漠灰",
    "黑色城镇",
    "新年广场",
    "生化酒店",
    "生化金字塔",
    "朝歌遗迹",
    "清新椰岛",
    "巨人城废墟",
    "卫星基地",
}

DESCRIPTION_TOKENS = {
    "玩家",
    "金币",
    "刷新",
    "获得",
    "角色",
    "所有",
    "每",
    "对",
    "使",
    "自身",
    "生命",
    "攻击",
    "增伤",
    "防护",
    "护盾",
    "嘲讽",
    "道具",
    "武器",
    "消灭",
    "成长",
    "快手",
    "反击",
    "造成",
    "免费",
    "战斗",
    "经验",
    "前排",
    "后排",
    "回合",
    "受到",
    "无法",
    "本局",
    "优先",
    "眩晕",
    "燃烧",
    "穿透",
    "光环",
    "永久",
    "目标",
    "遗言",
    "升级",
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
    value = re.sub(r"(?<=[\u4e00-\u9fff\d%>])(?:[<>]?[A-Za-z]{1,2}[\[\]]?|[<>])$", "", value)
    return value.strip().rstrip(",")


def looks_like_description(value: str) -> bool:
    if "<KeyWord>" in value:
        return True
    if not CHINESE_RE.search(value):
        return False
    return any(token in value for token in DESCRIPTION_TOKENS)


def is_noise(value: str) -> bool:
    if not value:
        return True
    if value in {"globalgamemanagers", "assets", "AutoChessItemDataTable"}:
        return True
    if re.fullmatch(r"[A-Za-z/<>\\[\\]_-]{1,4}", value):
        return True
    if re.fullmatch(r"-?\d+(?:,\-?\d+)*", value):
        return True
    if re.fullmatch(r"-?\d+[A-Za-z]+", value):
        return True
    return False


def parse_quality(resource: str) -> str | None:
    suffix = resource.rsplit("_", 1)[-1]
    return QUALITY_ALIASES.get(suffix)


def parse_item_table_records() -> list[dict]:
    values = load_tsv_values(ITEM_STRINGS_TSV)
    boundaries = []
    for row in values:
        value = clean_text(row["value"])
        if value in KNOWN_RECORD_NAMES:
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
            if is_noise(value) or value in KNOWN_RECORD_NAMES:
                continue
            if looks_like_description(value):
                descriptions.append(value)
            elif CHINESE_RE.search(value) and any(token in value for token in DESCRIPTION_TOKENS):
                brief_descriptions.append(value)

        keywords = []
        for desc in descriptions:
            keywords.extend(KEYWORD_RE.findall(desc))

        records.append(
            {
                "item_table_index": record_index + 1,
                "name": start["value"],
                "string_start_index": start["index"],
                "string_end_index": chunk[-1]["index"] if chunk else start["index"],
                "keywords": unique_keep_order(keywords),
                "descriptions": unique_keep_order(descriptions),
                "plain_descriptions": unique_keep_order(plain_text(v) for v in descriptions),
                "brief_descriptions": unique_keep_order(brief_descriptions),
                "raw_item_table_strings": raw_values,
            }
        )
    return records


def build_records_by_name(records: list[dict]) -> dict[str, dict]:
    return {record["name"]: record for record in records}


def build_throwable_card_map() -> dict[str, dict]:
    rows = load_json(THROWABLE_CARD_DATA, [])
    return {row["throwable_resource"]: row for row in rows if row.get("throwable_resource")}


def build_item_card_map() -> dict[str, dict]:
    rows = load_json(ITEM_CARD_DATA, [])
    return {row["item_resource"]: row for row in rows if row.get("item_resource")}


def build_consume_card_map() -> dict[str, dict]:
    rows = load_json(CONSUME_CARD_DATA, [])
    return {row["resource"]: row for row in rows if row.get("resource")}


def write_outputs(out_dir: Path, stem: str, rows: list[dict], records: list[dict] | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
        "index",
        "name",
        "resource",
        "png",
        "quality",
        "keywords",
        "descriptions",
        "plain_descriptions",
        "brief_descriptions",
        "item_table_index",
        "match_status",
    ]
    with (out_dir / f"{stem}.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            csv_row = {}
            for field in fields:
                value = row.get(field)
                if isinstance(value, list):
                    value = " | ".join(str(v) for v in value)
                csv_row[field] = value
            writer.writerow(csv_row)
    if records is not None:
        (out_dir / "item_table_records.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def merge_rows(manifest: list[dict], resource_field: str, png_field: str, resource_to_name: dict[str, str], records_by_name: dict[str, dict], category: str) -> list[dict]:
    rows = []
    for item in manifest:
        resource = item[resource_field]
        name = resource_to_name.get(resource)
        record = records_by_name.get(name) if name else None
        fallback_name = FILENAME_NAME_OVERRIDES.get(resource)
        if record:
            match_status = "matched_by_resource_alias"
        elif name:
            match_status = "name_from_apk_resource_token"
        elif fallback_name:
            match_status = "name_from_apk_filename"
        else:
            match_status = "not_found_in_AutoChessItemDataTable_strings"
        rows.append(
            {
                "index": item.get("index"),
                "category": category,
                "name": name or fallback_name or resource,
                "resource": resource,
                "png": item.get(png_field),
                "source_png": item.get("source_png"),
                "atlasAssetName": item.get("atlasAssetName"),
                "quality": parse_quality(resource),
                "keywords": record.get("keywords", []) if record else [],
                "descriptions": record.get("descriptions", []) if record else [],
                "plain_descriptions": record.get("plain_descriptions", []) if record else [],
                "brief_descriptions": record.get("brief_descriptions", []) if record else [],
                "item_table_index": record.get("item_table_index") if record else None,
                "string_start_index": record.get("string_start_index") if record else None,
                "match_status": match_status,
            }
        )
    return rows


def token_resource_map(manifest: list[dict], prefix: str, name_to_token: dict[str, str]) -> dict[str, str]:
    mapping = {}
    for item in manifest:
        resource = item["resource"]
        parts = resource.split("_")
        token = parts[-2] if parse_quality(resource) else parts[-1]
        for name, expected_token in name_to_token.items():
            if token.lower() == expected_token.lower():
                mapping.setdefault(resource, name)
    return mapping


def main() -> None:
    records = parse_item_table_records()
    records_by_name = build_records_by_name(records)
    throwable_card_map = build_throwable_card_map()
    item_card_map = build_item_card_map()
    consume_card_map = build_consume_card_map()

    throwable_resource_to_name = {resource: name for name, resource in THROWABLE_NAME_TO_RESOURCE.items()}
    item_resource_to_name = {resource: name for name, resource in ITEM_NAME_TO_RESOURCE.items()}

    throwables = merge_rows(
        load_json(THROWABLES_MANIFEST, []),
        "throwable_resource",
        "throwable_png",
        throwable_resource_to_name,
        records_by_name,
        "throwable",
    )
    for row in throwables:
        card = throwable_card_map.get(row["resource"])
        if card:
            row["composited_card_png"] = card.get("composited_card_png")
            row["quality"] = THROWABLE_QUALITY_BY_RESOURCE.get(row["resource"]) or row.get("quality") or card.get("quality")
            row["quality_source"] = "known_throwable_resource_quality" if row["resource"] in THROWABLE_QUALITY_BY_RESOURCE else card.get("quality_source")
            row["quality_background_png"] = card.get("quality_background_png")
            row["frame_png"] = card.get("frame_png")
    items = merge_rows(
        load_json(ITEMS_MANIFEST, []),
        "item_resource",
        "item_png",
        item_resource_to_name,
        records_by_name,
        "item",
    )
    for row in items:
        card = item_card_map.get(row["resource"])
        if card:
            row["composited_card_png"] = card.get("composited_card_png")
            row["quality"] = ITEM_QUALITY_BY_RESOURCE.get(row["resource"]) or row.get("quality") or card.get("quality")
            row["quality_source"] = "known_item_resource_quality" if row["resource"] in ITEM_QUALITY_BY_RESOURCE else card.get("quality_source")
            row["quality_background_png"] = card.get("quality_background_png")
            row["frame_png"] = card.get("frame_png")

    consume_manifest = load_json(CONSUMES_MANIFEST, [])
    consume_resource_to_name = token_resource_map(consume_manifest, "Icon_ZiZouQi_XiaoHao_", CONSUME_NAME_TO_TOKEN)
    consumes = merge_rows(
        consume_manifest,
        "resource",
        "png",
        consume_resource_to_name,
        records_by_name,
        "consume",
    )
    for row in consumes:
        card = consume_card_map.get(row["resource"])
        if card:
            row["composited_card_png"] = card.get("composited_card_png")
            row["spells_background_png"] = card.get("spells_background_png")
            row["composition_layers"] = card.get("composition_layers")

    buff_manifest = load_json(BUFFS_MANIFEST, [])
    buff_resource_to_name = token_resource_map(buff_manifest, "Icon_ZiZouQi_RL_", BUFF_NAME_TO_TOKEN)
    buff_resource_to_name.update(BUFF_RESOURCE_TO_NAME_OVERRIDES)
    buffs = merge_rows(
        buff_manifest,
        "resource",
        "png",
        buff_resource_to_name,
        records_by_name,
        "buff",
    )

    write_outputs(OUT_ROOT / "organized_throwable_data", "throwables_data", throwables, records)
    write_outputs(OUT_ROOT / "organized_item_data", "items_data", items, records)
    write_outputs(OUT_ROOT / "organized_consume_data", "consume_cards_data", consumes, records)
    write_outputs(OUT_ROOT / "organized_buff_data", "buff_cards_data", buffs, records)

    print(f"item table records parsed: {len(records)}")
    for label, rows in [
        ("throwables", throwables),
        ("items", items),
        ("consume_cards", consumes),
        ("buff_cards", buffs),
    ]:
        matched = sum(1 for row in rows if row["match_status"].startswith("matched"))
        print(f"{label}: {len(rows)}, matched_table: {matched}, unmatched: {len(rows) - matched}")


if __name__ == "__main__":
    main()
