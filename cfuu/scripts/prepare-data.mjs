import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const workspaceRoot = path.resolve(projectRoot, "..");
const dumpRoot = path.join(workspaceRoot, "autochess_dump");
const publicRoot = path.join(projectRoot, "public");
const dataOut = path.join(publicRoot, "data");
const assetRoot = path.join(publicRoot, "assets", "cards");
const overridesPath = path.join(projectRoot, "data", "card-overrides.json");
const customCardsPath = path.join(projectRoot, "data", "custom-cards.json");
const factionOverridesPath = path.join(projectRoot, "data", "faction-overrides.json");
const videoGuidesPath = path.join(projectRoot, "data", "video-guides.json");
const recommendedLineupsPath = path.join(projectRoot, "data", "recommended-lineups.json");

const sourceFiles = {
  roles: "organized_role_data/roles_data.json",
  weapons: "organized_weapon_data/weapons_data.json",
  throwables: "organized_throwable_data/throwables_data.json",
  items: "organized_item_data/items_data.json",
  consumes: "organized_consume_data/consume_cards_data.json",
  buffs: "organized_buff_data/buff_cards_data.json",
  factions: "organized_factions/factions_data.json",
  fetters: "organized_fetters/fetters_manifest.json",
  maps: "organized_maps/maps_manifest.json",
  wordExplanations: "AutoChessWordExplanationDataTable.strings.tsv",
};

const categoryLabels = {
  role: "角色卡",
  weapon: "武器卡",
  throwable: "投掷物",
  item: "道具卡",
  consume: "消耗卡",
  buff: "增益卡",
};

const factionIconBaseNames = {
  "隐袭": "YinXi",
  "保卫者": "BWZ",
  "幽灵": "ShengHuaYouLing",
  "山海经": "ShanHaiJing",
  HeartShot: "NvTuan",
  "潜伏者": "QFZ",
  "葫芦娃": "HuLuWa",
  "谍报特工": "DieBao",
  "审判之眼": "DuiZhang",
  "铠甲勇士": "KaiJiaYongShi",
  "鸿运星光": "XingGuang",
  "核心兵器": "GaiZaoZhe",
};

const factionDisplayNamesByBaseName = {
  BWZ: "保卫者",
  BuQiang: "步枪",
  ChongFengQiang: "冲锋枪",
  DieBao: "谍报特工",
  DuiZhang: "审判之眼",
  GaiZaoZhe: "核心兵器",
  HuLuWa: "葫芦娃",
  JiQiang: "机枪",
  JingDianZuHe: "经典组合",
  JuJiQiang: "狙击枪",
  KaiJiaYongShi: "铠甲勇士",
  NvTuan: "HeartShot",
  QFZ: "潜伏者",
  SanGuo: "三国",
  ShanHaiJing: "山海经",
  ShengHuaYouLing: "幽灵",
  XianDanQiang: "霰弹枪",
  XingGuang: "鸿运星光",
  YinXi: "隐袭",
};

const mapDisplayNames = {
  CangNiZhiDi: "藏匿之地",
  HeiSeChengZhen: "黑色城镇",
  JuRenCheng: "巨人城废墟",
  JuRenChengFeiXu: "巨人城废墟",
  QingXinYeDao: "清新椰岛",
  ShaMoHui: "沙漠灰",
  ShengHuaJinZiTa: "生化金字塔",
  ShengHuaJiuDian: "生化酒店",
  ShouWangZhiCheng: "守望之城",
  WeiXingJiDi: "卫星基地",
  XiangZhan: "巷战",
  XinNianGuangChang: "新年广场",
  YunShuChuan: "运输船",
  ZhaoGeYiJi: "朝歌遗迹",
};

const mapBonusDescriptions = {
  YunShuChuan: "玩家生命值低于15时，金币+20",
  ShaMoHui: "刷新商店时，使你1号位的角色+1+2",
  HeiSeChengZhen: "在2级时，获得2张复制",
  XinNianGuangChang: "所有角色道具栏+1",
  ShengHuaJiuDian: "每阵亡7个敌方角色，获得1张随机角色牌",
  ShengHuaJinZiTa: "每刷新4次商店，获得1金币",
  ZhaoGeYiJi: "在2级时，获得1张消耗卡：异能爆发",
  QingXinYeDao: "角色每次攻击时，永久+1+2",
  WeiXingJiDi: "商店升级时，获得6次免费刷新",
  JuRenChengFeiXu: "未知",
  CangNiZhiDi: "未知",
  ShouWangZhiCheng: "未知",
  XiangZhan: "未知",
};

const iconVariantRank = {
  Gold: 0,
  GOLD: 0,
  Colour: 1,
  Silver: 2,
  Sliver: 2,
  Copper: 3,
  Grey: 4,
  HuiSe: 4,
};

const keywordDisplayOrder = [
  "快手",
  "成长",
  "消灭",
  "遗言",
  "生化幽灵",
  "护盾",
  "增伤",
  "子弹",
  "燃烧",
  "穿透",
  "反击",
  "散射",
  "连续行动",
  "防护",
  "嘲讽",
];

const wordExplanationOverrides = {
  "散射": "攻击时对同排其他的目标造成一定伤害",
  "嘲讽": "让对方优先攻击该角色",
};

const misparsedBuffResourceStems = new Set([
  "Icon_ZiZouQi_RL_ShangHai",
  "Icon_ZiZouQi_RL_ShouHuan",
  "Icon_ZiZouQi_RL_ShuangShuXing",
  "Icon_ZiZouQi_RL_TouKui",
  "Icon_ZiZouQi_RL_XiaoHong",
  "Icon_ZiZouQi_RL_XiaoHao",
  "Icon_ZiZouQi_RL_XuanYun",
  "Icon_ZiZouQi_RL_YiYan",
]);

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(dumpRoot, relativePath), "utf8"));
}

function readProjectJson(filePath, fallback) {
  if (!existsSync(filePath)) return fallback;
  return JSON.parse(readFileSync(filePath, "utf8"));
}

function readPreparedJson(fileName, fallback) {
  return readProjectJson(path.join(dataOut, fileName), fallback);
}

function writePreparedJson(fileName, value) {
  writeFileSync(path.join(dataOut, fileName), JSON.stringify(value, null, 2), "utf8");
}

function readTsvValues(relativePath) {
  const filePath = path.join(dumpRoot, relativePath);
  return readFileSync(filePath, "utf8")
    .split(/\r?\n/)
    .slice(1)
    .map((line) => {
      const [, index, value] = line.split("\t");
      return { index: Number(index), value: (value || "").trim() };
    })
    .filter((row) => Number.isFinite(row.index) && row.value);
}

function hasChinese(value) {
  return /[\u4e00-\u9fff]/.test(value);
}

function safeName(value) {
  return String(value || "asset")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "_")
    .slice(0, 180);
}

function resolveSourcePath(relativeOrAbsolute) {
  if (!relativeOrAbsolute) return null;
  const normalized = String(relativeOrAbsolute).replace(/\\/g, path.sep);
  if (path.isAbsolute(normalized)) return normalized;
  return path.join(workspaceRoot, normalized);
}

function copyAsset(sourcePath, category, id) {
  const resolved = resolveSourcePath(sourcePath);
  if (!resolved || !existsSync(resolved)) return null;
  const ext = path.extname(resolved) || ".png";
  const folder = path.join(assetRoot, category);
  mkdirSync(folder, { recursive: true });
  const fileName = `${safeName(id)}${ext}`;
  const target = path.join(folder, fileName);
  copyFileSync(resolved, target);
  return `/assets/cards/${category}/${encodeURIComponent(fileName).replace(/%2F/g, "/")}`;
}

function normalizeDescriptions(row) {
  return [
    ...(Array.isArray(row.plain_descriptions) ? row.plain_descriptions : []),
    ...(Array.isArray(row.brief_descriptions) ? row.brief_descriptions : []),
  ].filter(Boolean);
}

function isMisparsedBuff(row) {
  const resource = String(row.resource || row.name || "");
  return Array.from(misparsedBuffResourceStems).some((stem) => resource === stem || resource.startsWith(`${stem}_`));
}

function normalizeRole(row) {
  const id = `role-${row.role_resource || row.index}`;
  const image = copyAsset(row.composited_card_png || row.role_png, "roles", id);
  const goldImage = copyAsset(row.gold_composited_card_png, "roles-gold", id);
  const originalImage = copyAsset(row.role_png, "original/roles", id);
  const avatar = copyAsset(row.avatar_png, "avatars", `${id}-avatar`);
  return {
    id,
    category: "role",
    categoryLabel: categoryLabels.role,
    name: row.name,
    image,
    goldImage,
    originalImage,
    avatar,
    quality: row.quality || null,
    factions: Array.isArray(row.factions) ? row.factions : [],
    keywords: Array.isArray(row.keywords) ? row.keywords : [],
    descriptions: normalizeDescriptions(row),
    resource: row.role_resource,
    matchStatus: row.role_table_match_status || "unknown",
    hidden: false,
    raw: row,
  };
}

function normalizeWeapon(row) {
  const id = `weapon-${row.base_resource || row.index}`;
  const originalImage = copyAsset(row.weapon_png, "original/weapons", id);
  return {
    id,
    category: "weapon",
    categoryLabel: categoryLabels.weapon,
    name: row.name,
    image: copyAsset(row.composited_card_png || row.weapon_png, "weapons", id),
    originalImage,
    avatar: null,
    quality: row.quality || null,
    factions: [],
    keywords: Array.isArray(row.keywords) ? row.keywords : [],
    descriptions: normalizeDescriptions(row),
    resource: row.base_resource,
    matchStatus: row.match_status || "unknown",
    hidden: false,
    raw: row,
  };
}

function normalizeItemLike(row, category) {
  const id = `${category}-${row.resource || row.index}`;
  const displayImageSource = category === "buff" ? row.png : row.composited_card_png || row.png;
  const originalCategoryMap = {
    throwable: "original/throwables",
    item: "original/items",
    consume: "original/consumes",
  };
  const originalImage = originalCategoryMap[category] ? copyAsset(row.png, originalCategoryMap[category], id) : null;
  return {
    id,
    category,
    categoryLabel: categoryLabels[category],
    name: row.name,
    image: copyAsset(displayImageSource, category, id),
    originalImage,
    avatar: null,
    quality: row.quality || null,
    factions: [],
    keywords: Array.isArray(row.keywords) ? row.keywords : [],
    descriptions: normalizeDescriptions(row),
    resource: row.resource,
    matchStatus: row.match_status || "unknown",
    hidden: false,
    raw: row,
  };
}

function normalizeStringList(value) {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item).trim()).filter(Boolean);
}

function applyCardOverrides(cards, overridesById) {
  return cards.map((card) => {
    const override = overridesById[card.id] || overridesById[card.resource];
    if (!override || typeof override !== "object") return { ...card, hidden: Boolean(card.hidden) };
    return {
      ...card,
      name: typeof override.name === "string" && override.name.trim() ? override.name.trim() : card.name,
      quality: typeof override.quality === "string" && override.quality.trim() ? override.quality.trim() : card.quality,
      factions: Array.isArray(override.factions) ? normalizeStringList(override.factions) : card.factions,
      keywords: Array.isArray(override.keywords) ? normalizeStringList(override.keywords) : card.keywords,
      descriptions: Array.isArray(override.descriptions) ? normalizeStringList(override.descriptions) : card.descriptions,
      hidden: Boolean(override.hidden),
      raw: {
        ...card.raw,
        card_override: override,
      },
    };
  });
}

function appendCustomCards(cards, definitions) {
  const output = [...cards];
  const cardsById = new Map(output.map((card) => [card.id, card]));
  for (const definition of definitions) {
    if (!definition || definition.category !== "consume" || !definition.id || !definition.sourceId) continue;
    const source = cardsById.get(definition.sourceId);
    if (!source || source.category !== "consume" || cardsById.has(definition.id)) continue;
    const customCard = {
      ...source,
      id: definition.id,
      resource: definition.resource || definition.id,
      name: definition.name || `${source.name}（复制）`,
      raw: {
        ...source.raw,
        custom_card: definition,
      },
    };
    output.push(customCard);
    cardsById.set(customCard.id, customCard);
  }
  return output;
}

function selectFactionIcon(baseName, fetterIcons) {
  const candidates = fetterIcons
    .filter((item) => item.base_name === baseName)
    .sort((a, b) => (iconVariantRank[a.variant] ?? 99) - (iconVariantRank[b.variant] ?? 99));
  const icon = candidates[0];
  if (!icon) return null;
  return copyAsset(
    icon.fetter_png_rb_swap_flip_y || icon.grouped_png_rb_swap_flip_y || icon.fetter_png || icon.grouped_png || icon.source_png,
    "factions",
    `faction-${baseName}`,
  );
}

function listFetterIconBaseNames(fetterIcons) {
  const baseNames = new Set();
  for (const icon of fetterIcons) {
    const baseName = icon.base_name;
    if (!baseName) continue;
    baseNames.add(baseName);
  }

  return Array.from(baseNames).sort((a, b) => a.localeCompare(b));
}

function normalizeFactions(rows, fetterIcons) {
  const rowsByBaseName = new Map(rows.map((row) => [factionIconBaseNames[row.name], row]));
  return listFetterIconBaseNames(fetterIcons).map((baseName) => {
    const row = rowsByBaseName.get(baseName);
    const name = row?.name || factionDisplayNamesByBaseName[baseName] || baseName;
    return {
      baseName,
      name,
      keywordCategory: row?.keyword_category || "待补全",
      description: row?.description || "当前只有阵营图标资源，阵营描述待补全。",
      stageEffects: Array.isArray(row?.stage_effects) ? row.stage_effects : [],
      roles: Array.isArray(row?.roles) ? row.roles : [],
      icon: selectFactionIcon(baseName, fetterIcons),
      hidden: false,
      raw: row || null,
    };
  });
}

function applyFactionOverrides(factions, overridesById) {
  return factions.map((faction) => {
    const override = overridesById[faction.baseName] || overridesById[faction.name];
    if (!override || typeof override !== "object") return { ...faction, hidden: Boolean(faction.hidden) };
    return {
      ...faction,
      name: typeof override.name === "string" && override.name.trim() ? override.name.trim() : faction.name,
      keywordCategory: typeof override.keywordCategory === "string" && override.keywordCategory.trim() ? override.keywordCategory.trim() : faction.keywordCategory,
      description: typeof override.description === "string" && override.description.trim() ? override.description.trim() : faction.description,
      stageEffects: Array.isArray(override.stageEffects) ? normalizeStringList(override.stageEffects) : faction.stageEffects,
      hidden: Boolean(override.hidden),
      raw: {
        ...(faction.raw || {}),
        faction_override: override,
      },
    };
  });
}

function normalizeMapKey(mapKey) {
  if (mapKey === "JuRenCheng") return "JuRenChengFeiXu";
  return mapKey;
}

function normalizeMaps(rows) {
  const byKey = new Map();
  for (const row of rows) {
    const key = normalizeMapKey(row.map_key);
    if (!byKey.has(key)) {
      byKey.set(key, {
        key,
        name: mapDisplayNames[key] || key,
        bonusDescription: mapBonusDescriptions[key] || "未知",
        icon: null,
        background: null,
        iconResource: null,
        backgroundResource: null,
        raw: [],
      });
    }
    const item = byKey.get(key);
    item.raw.push(row);
    if (row.kind === "map_icon") {
      item.icon = copyAsset(row.output_png, "maps/icons", `map-icon-${key}`);
      item.iconResource = row.resource;
    }
    if (row.kind === "map_background") {
      item.background = copyAsset(row.output_png, "maps/backgrounds", `map-background-${key}`);
      item.backgroundResource = row.resource;
    }
  }
  return Array.from(byKey.values()).sort((a, b) => a.name.localeCompare(b.name, "zh-Hans-CN"));
}

function normalizeWordExplanations(rows) {
  const byTerm = new Map();
  const wanted = new Set(keywordDisplayOrder);
  for (let index = 0; index < rows.length - 1; index += 1) {
    const term = rows[index].value.replace(/\d+$/, "");
    const description = rows[index + 1].value;
    if (!wanted.has(term) || !hasChinese(description)) continue;
    if (description.startsWith("AutoChess")) continue;
    byTerm.set(term, {
      term,
      description: wordExplanationOverrides[term] || description,
      sourceIndex: rows[index].index,
    });
  }
  return keywordDisplayOrder
    .map((term) => byTerm.get(term))
    .filter(Boolean);
}

function hasDumpSources() {
  return Object.values(sourceFiles).every((relativePath) => existsSync(path.join(dumpRoot, relativePath)));
}

function isCustomPreparedCard(card) {
  return String(card?.id || "").startsWith("consume-custom-") || Boolean(card?.raw?.custom_card);
}

function refreshFromPreparedData() {
  mkdirSync(dataOut, { recursive: true });

  const cardOverrides = readProjectJson(overridesPath, {});
  const customCards = readProjectJson(customCardsPath, []);
  const factionOverrides = readProjectJson(factionOverridesPath, {});
  const baseCards = readPreparedJson("cards-base.json", readPreparedJson("cards.json", [])).filter((card) => !isCustomPreparedCard(card));
  const baseFactions = readPreparedJson("factions-base.json", readPreparedJson("factions-normalized.json", []));
  const normalizedMaps = readPreparedJson("maps-normalized.json", []);
  const videoGuides = readProjectJson(videoGuidesPath, []);
  const recommendedLineups = readProjectJson(recommendedLineupsPath, []);
  const cards = applyCardOverrides(appendCustomCards(baseCards, customCards), cardOverrides);
  const normalizedFactions = applyFactionOverrides(baseFactions, factionOverrides);
  const countsByCategory = cards.reduce((counts, card) => {
    counts[card.category] = (counts[card.category] || 0) + 1;
    return counts;
  }, {});

  writePreparedJson("cards.json", cards);
  writePreparedJson("factions-normalized.json", normalizedFactions);
  writePreparedJson("video-guides.json", videoGuides);
  writePreparedJson("recommended-lineups.json", recommendedLineups);
  writePreparedJson("summary.json", {
    generatedAt: new Date().toISOString(),
    source: "prepared-data",
    counts: {
      roles: countsByCategory.role || 0,
      weapons: countsByCategory.weapon || 0,
      throwables: countsByCategory.throwable || 0,
      items: countsByCategory.item || 0,
      consumes: countsByCategory.consume || 0,
      buffs: countsByCategory.buff || 0,
      factions: normalizedFactions.filter((faction) => !faction.hidden).length,
      maps: normalizedMaps.length,
      cards: cards.length,
    },
  });

  console.log(`Refreshed ${cards.length} cards, ${normalizedFactions.length} factions, and ${normalizedMaps.length} maps from prepared data.`);
}

mkdirSync(dataOut, { recursive: true });

if (!hasDumpSources()) {
  refreshFromPreparedData();
  process.exit(0);
}

rmSync(assetRoot, { recursive: true, force: true, maxRetries: 8, retryDelay: 250 });
mkdirSync(assetRoot, { recursive: true });

const roles = readJson(sourceFiles.roles);
const weapons = readJson(sourceFiles.weapons);
const throwables = readJson(sourceFiles.throwables);
const items = readJson(sourceFiles.items);
const consumes = readJson(sourceFiles.consumes);
const buffs = readJson(sourceFiles.buffs);
const normalizedBuffRows = buffs.filter((row) => !isMisparsedBuff(row));
const factions = readJson(sourceFiles.factions);
const fetterIcons = readJson(sourceFiles.fetters);
const maps = readJson(sourceFiles.maps);
const wordExplanationRows = readTsvValues(sourceFiles.wordExplanations);

for (const [name, relativePath] of Object.entries(sourceFiles)) {
  const source = path.join(dumpRoot, relativePath);
  if (existsSync(source) && path.extname(relativePath) === ".json") {
    copyFileSync(source, path.join(dataOut, `${name}.json`));
  }
}
writeFileSync(path.join(dataOut, "buffs.json"), JSON.stringify(normalizedBuffRows, null, 2), "utf8");

const cardOverrides = readProjectJson(overridesPath, {});
const customCards = readProjectJson(customCardsPath, []);
const factionOverrides = readProjectJson(factionOverridesPath, {});
const baseCards = [
  ...roles.map(normalizeRole),
  ...weapons.map(normalizeWeapon),
  ...throwables.map((row) => normalizeItemLike(row, "throwable")),
  ...items.map((row) => normalizeItemLike(row, "item")),
  ...consumes.map((row) => normalizeItemLike(row, "consume")),
  ...normalizedBuffRows.map((row) => normalizeItemLike(row, "buff")),
];
const baseFactions = normalizeFactions(factions, fetterIcons);
const cards = applyCardOverrides(appendCustomCards(baseCards, customCards), cardOverrides);
const normalizedFactions = applyFactionOverrides(baseFactions, factionOverrides);
const normalizedMaps = normalizeMaps(maps);
const normalizedWordExplanations = normalizeWordExplanations(wordExplanationRows);
const videoGuides = readProjectJson(videoGuidesPath, []);
const recommendedLineups = readProjectJson(recommendedLineupsPath, []);

writePreparedJson("cards-base.json", baseCards);
writePreparedJson("factions-base.json", baseFactions);
writePreparedJson("cards.json", cards);
writePreparedJson("factions-normalized.json", normalizedFactions);
writePreparedJson("maps-normalized.json", normalizedMaps);
writePreparedJson("word-explanations.json", normalizedWordExplanations);
writePreparedJson("video-guides.json", videoGuides);
writePreparedJson("recommended-lineups.json", recommendedLineups);
writeFileSync(
  path.join(dataOut, "summary.json"),
  JSON.stringify(
    {
      generatedAt: new Date().toISOString(),
      counts: {
        roles: roles.length,
        weapons: weapons.length,
        throwables: throwables.length,
        items: items.length,
        consumes: consumes.length,
        buffs: normalizedBuffRows.length,
        factions: normalizedFactions.filter((faction) => !faction.hidden).length,
        maps: normalizedMaps.length,
        cards: cards.length,
      },
    },
    null,
    2,
  ),
  "utf8",
);

console.log(`Prepared ${cards.length} cards, ${normalizedFactions.length} factions, and ${normalizedMaps.length} maps.`);
