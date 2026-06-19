import { useEffect, useMemo, useState } from "react";
import {
  Bot,
  BookOpen,
  Boxes,
  X,
  Crosshair,
  Database,
  EyeOff,
  Filter,
  Flame,
  GraduationCap,
  Layers,
  Library,
  Map as MapIcon,
  PlaySquare,
  Search,
  Shield,
  Sparkles,
  Swords,
  Target,
} from "lucide-react";
import { loadSiteData } from "./data/loaders";
import type { CardCategory, CardRecord, FactionRecord, MapRecord, RecommendedLineup, Summary, VideoGuide, WordExplanation } from "./data/types";

type ViewMode = "cards" | "factions";
type SitePage = "library" | "guide" | "ai" | "videos";
type BasicsSection = "guide" | "maps" | "buffs";
type AiSection = "lineups";
type LibraryCategory = Exclude<CardCategory, "buff"> | "all";

type AppRoute = {
  page: SitePage;
  view: ViewMode;
  category: LibraryCategory;
  basicsSection: BasicsSection;
  aiSection: AiSection;
};

const categories: Array<{ id: LibraryCategory; label: string; icon: typeof Database }> = [
  { id: "all", label: "全部", icon: Database },
  { id: "role", label: "角色", icon: Shield },
  { id: "weapon", label: "武器", icon: Crosshair },
  { id: "throwable", label: "投掷物", icon: Target },
  { id: "item", label: "道具", icon: Boxes },
  { id: "consume", label: "消耗", icon: Sparkles },
];

const qualityLabels: Record<string, string> = {
  grey: "灰",
  gray: "灰",
  green: "绿",
  blue: "蓝",
  purple: "紫",
  gold: "金",
  red: "红",
};

const qualityColors: Record<string, { background: string; foreground: string }> = {
  grey: { background: "#3b4654", foreground: "#edf4ff" },
  gray: { background: "#3b4654", foreground: "#edf4ff" },
  green: { background: "#0f5d3d", foreground: "#c7ffe0" },
  blue: { background: "#123f8f", foreground: "#d8e8ff" },
  purple: { background: "#56309a", foreground: "#f0dcff" },
  gold: { background: "#7a5a12", foreground: "#fff0b8" },
  red: { background: "#8a2632", foreground: "#ffe0e4" },
};

const qualityOrder = ["grey", "gray", "green", "blue", "purple", "gold", "red"];

const navItems: Array<{ id: SitePage; label: string; icon: typeof Library }> = [
  { id: "library", label: "卡牌资源库", icon: Library },
  { id: "guide", label: "游戏基础", icon: GraduationCap },
  { id: "ai", label: "推荐阵容", icon: Bot },
  { id: "videos", label: "视频攻略", icon: PlaySquare },
];

const libraryCategoryRoutes: Record<LibraryCategory, string> = {
  all: "all",
  role: "role",
  weapon: "weapon",
  throwable: "throwable",
  item: "item",
  consume: "consume",
};

function readAppRoute(): AppRoute {
  const parts = window.location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const [section, detail] = parts;

  if (section === "basics") {
    const basicsSection: BasicsSection = detail === "maps" || detail === "buffs" ? detail : "guide";
    return { page: "guide", view: "cards", category: "all", basicsSection, aiSection: "lineups" };
  }
  if (section === "ai") {
    return { page: "ai", view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" };
  }
  if (section === "videos") {
    return { page: "videos", view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" };
  }
  if (section === "library" && detail === "factions") {
    return { page: "library", view: "factions", category: "all", basicsSection: "guide", aiSection: "lineups" };
  }

  const category = (detail && Object.values(libraryCategoryRoutes).includes(detail as LibraryCategory) ? detail : "all") as LibraryCategory;
  return { page: "library", view: "cards", category, basicsSection: "guide", aiSection: "lineups" };
}

function appRouteHash(route: Pick<AppRoute, "page" | "view" | "category" | "basicsSection" | "aiSection">) {
  if (route.page === "guide") return `#/basics/${route.basicsSection}`;
  if (route.page === "ai") return "#/ai";
  if (route.page === "videos") return "#/videos";
  if (route.view === "factions") return "#/library/factions";
  return `#/library/${libraryCategoryRoutes[route.category]}`;
}

const ladderAssets = {
  cfLogo: "/assets/ladder/Ladder_Card_Icon02_01.png",
};

function classNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

function searchableText(card: CardRecord) {
  return [
    card.name,
    card.resource,
    card.categoryLabel,
    card.quality || "",
    ...card.factions,
    ...card.keywords,
    ...card.descriptions,
  ]
    .join(" ")
    .toLowerCase();
}

function displayDescriptions(card: CardRecord) {
  const descriptions = card.descriptions
    .map((description) => description.trim())
    .filter((description) => description && description !== "数据待补全");
  return descriptions.length ? descriptions : ["未知"];
}

function splitRoleUpgradeDescriptions(card: CardRecord) {
  const descriptions = displayDescriptions(card);
  if (descriptions.length < 2) return { base: descriptions, upgraded: [] };
  return {
    base: [descriptions[0]],
    upgraded: descriptions.slice(1),
  };
}

function hasBaseUpgradeDescriptions(card: CardRecord) {
  return (card.category === "role" || card.category === "weapon") && displayDescriptions(card).length > 1;
}

function DescriptionList({ card, limit }: { card: CardRecord; limit?: number }) {
  const grouped = hasBaseUpgradeDescriptions(card);
  const descriptions = grouped ? splitRoleUpgradeDescriptions(card) : { base: displayDescriptions(card), upgraded: [] };
  const rows = [
    ...descriptions.base.map((description) => ({ label: grouped ? "基础" : "", kind: "base", description })),
    ...descriptions.upgraded.map((description) => ({ label: "升级", kind: "upgraded", description })),
  ].slice(0, limit);

  return (
    <ul className={classNames("description-list", grouped && "description-list-grouped")}>
      {rows.map((item, index) => (
        <li className={classNames(item.kind === "upgraded" && "upgraded")} key={`${item.description}-${index}`}>
          {item.label ? <span className="description-tag">{item.label}</span> : null}
          <span>{item.description}</span>
        </li>
      ))}
    </ul>
  );
}

function countByCategory(cards: CardRecord[]) {
  return categories
    .filter((item) => item.id !== "all")
    .map((item) => ({
      id: item.id,
      label: item.label,
      count: cards.filter((card) => card.category === item.id).length,
      icon: item.icon,
    }));
}

function qualityLabel(quality: string) {
  return qualityLabels[quality] || quality;
}

function qualityOptionStyle(quality: string) {
  const color = qualityColors[quality];
  if (!color) return undefined;
  return {
    backgroundColor: color.background,
    color: color.foreground,
  };
}

function qualitySortValue(quality: string) {
  const index = qualityOrder.indexOf(quality);
  return index === -1 ? qualityOrder.length : index;
}

function cardQualityRank(card: CardRecord) {
  if (!card.quality) return -1;
  const index = qualityOrder.indexOf(card.quality);
  return index === -1 ? -1 : index;
}

function compareCardsByQualityDesc(a: CardRecord, b: CardRecord) {
  const qualityDelta = cardQualityRank(b) - cardQualityRank(a);
  if (qualityDelta !== 0) return qualityDelta;
  return a.name.localeCompare(b.name, "zh-Hans-CN") || a.id.localeCompare(b.id);
}

function buildQualityList(cards: CardRecord[]) {
  return Array.from(new Set(cards.map((card) => card.quality).filter((quality): quality is string => Boolean(quality))))
    .sort((a, b) => qualitySortValue(a) - qualitySortValue(b) || a.localeCompare(b));
}

function CardImage({ card, compact = false, factionIconMap }: { card: CardRecord; compact?: boolean; factionIconMap?: Map<string, string | null> }) {
  if (compact && card.category !== "buff" && card.category !== "item") {
    const factionIcon = card.category === "role" && card.factions[0] ? factionIconMap?.get(card.factions[0]) : null;
    return card.image ? (
      <span className="card-list-art">
        <img className="card-art-direct card-art-direct-compact" src={card.image} alt={card.name} loading="lazy" />
        {factionIcon ? <img className="card-list-faction-badge" src={factionIcon} alt="" loading="lazy" /> : null}
      </span>
    ) : (
      <div className="missing-art">暂无图片</div>
    );
  }

  const directImage = card.category === "item" || card.category === "buff";
  if (directImage) {
    const iconLike = card.category === "buff";
    return card.image ? (
      <div className={classNames("card-art-wrap", compact && "card-art-wrap-compact")}>
        <img
          className={classNames("card-art-direct", compact && "card-art-direct-compact", iconLike && "card-art-direct-iconlike")}
          src={card.image}
          alt={card.name}
          loading="lazy"
        />
      </div>
    ) : (
      <div className="missing-art">暂无图片</div>
    );
  }

  const factionIcon = card.category === "role" && card.factions[0] ? factionIconMap?.get(card.factions[0]) : null;
  return (
    <div className={classNames("card-art", compact && "card-art-compact")}>
      {card.image ? <img src={card.image} alt={card.name} loading="lazy" /> : <div className="missing-art">暂无图片</div>}
      {factionIcon ? <img className="card-faction-badge" src={factionIcon} alt="" loading="lazy" /> : null}
    </div>
  );
}

function FactionChip({ name, icon, strong = false }: { name: string; icon?: string | null; strong?: boolean }) {
  return (
    <span className={classNames("chip faction-chip", strong && "strong")}>
      {icon ? <img src={icon} alt="" /> : null}
      {name}
    </span>
  );
}

function CardTile({ card, selected, factionIconMap, onSelect }: { card: CardRecord; selected: boolean; factionIconMap: Map<string, string | null>; onSelect: () => void }) {
  const iconLike = card.category === "buff";
  const descriptions = displayDescriptions(card);
  return (
    <button className={classNames("card-tile", iconLike && "card-tile-iconlike", card.hidden && "hidden-card", selected && "selected")} onClick={onSelect} type="button">
      <CardImage card={card} compact factionIconMap={factionIconMap} />
      <div className="tile-body">
        <div className="tile-topline">
          <span>{card.categoryLabel}</span>
          {card.hidden ? <span className="hidden-card-badge"><EyeOff size={12} /> 已隐藏</span> : null}
        </div>
        <strong>{card.name}</strong>
        <p>{descriptions[0]}</p>
        <div className="chip-row">
          {card.factions.slice(0, 2).map((faction) => (
            <span className="chip" key={faction}>
              {faction}
            </span>
          ))}
          {card.keywords.slice(0, 3).map((keyword) => (
            <span className="chip muted" key={keyword}>
              {keyword}
            </span>
          ))}
        </div>
      </div>
    </button>
  );
}

function DetailPanel({
  card,
  factionIconMap,
  mobileOpen = false,
  onClose,
}: {
  card: CardRecord | null;
  factionIconMap: Map<string, string | null>;
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  if (!card) {
    return (
      <aside className={classNames("detail-panel empty", mobileOpen && "mobile-detail-open")}>
        {onClose ? (
          <button className="detail-close" onClick={onClose} type="button" aria-label="关闭详情">
            <X size={18} />
          </button>
        ) : null}
        <BookOpen size={28} />
        <h2>选择一张卡牌</h2>
        <p>点击左侧卡牌查看图片、词条、阵营和技能描述。</p>
      </aside>
    );
  }

  return (
    <aside className={classNames("detail-panel", mobileOpen && "mobile-detail-open")}>
      {onClose ? (
        <button className="detail-close" onClick={onClose} type="button" aria-label="关闭详情">
          <X size={18} />
        </button>
      ) : null}
      <div className="detail-summary">
        <div className="detail-visual">
          <CardImage card={card} factionIconMap={factionIconMap} />
        </div>
        <div className="detail-title">
          <span>{card.categoryLabel}</span>
          <h2>{card.name}</h2>
          {card.category === "role" ? (
            <section className="detail-section compact">
              <h3>阵营</h3>
              <div className="chip-row">
                {card.factions.length ? card.factions.map((faction) => <FactionChip icon={factionIconMap.get(faction)} key={faction} name={faction} strong />) : <span className="empty-text">无</span>}
              </div>
            </section>
          ) : null}
          <section className="detail-section compact">
            <h3>词条</h3>
            <div className="chip-row">
              {card.keywords.length ? card.keywords.map((keyword) => <span className="chip strong" key={keyword}>{keyword}</span>) : <span className="empty-text">无</span>}
            </div>
          </section>
        </div>
      </div>
      <section className="detail-section">
        <h3>描述</h3>
        <DescriptionList card={card} />
      </section>
    </aside>
  );
}

function FactionPanel({
  factions,
  factionRoleMap,
  selectedFaction,
  onSelect,
}: {
  factions: FactionRecord[];
  factionRoleMap: Map<string, CardRecord[]>;
  selectedFaction: string;
  onSelect: (name: string) => void;
}) {
  return (
    <section className="faction-panel">
      <div className="section-heading">
        <div>
          <span>阵营资料</span>
          <h2>关键词体系与角色归属</h2>
        </div>
        <Swords size={22} />
      </div>
      <div className="faction-grid">
        {factions.map((faction) => (
          <button
            className={classNames("faction-card", selectedFaction === faction.name && "selected")}
            key={faction.name}
            onClick={() => onSelect(faction.name)}
            type="button"
          >
            <div className="faction-card-head">
              <strong>
                <span className="faction-card-icon">
                  {faction.icon ? <img src={faction.icon} alt="" /> : null}
                </span>
                {faction.name}
              </strong>
              <span>{faction.keywordCategory}</span>
            </div>
            <p>{faction.description}</p>
            <div className="faction-effects">
              {faction.stageEffects.slice(0, 2).map((effect) => (
                <span key={effect}>{effect}</span>
              ))}
            </div>
            <small>{factionRoleMap.get(faction.name)?.length || 0} 名关联角色</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function FactionRoleAvatar({ card, factionIconMap }: { card: CardRecord; factionIconMap: Map<string, string | null> }) {
  return (
    <div className="faction-role">
      <button className="faction-role-avatar" type="button" aria-label={`查看${card.name}卡牌信息`}>
        {card.avatar || card.image ? (
          <img src={card.avatar || card.image || ""} alt={card.name} loading="lazy" />
        ) : (
          <span>{card.name.slice(0, 1)}</span>
        )}
      </button>
      <span className="faction-role-name">{card.name}</span>
      <div className="faction-role-popover" role="tooltip">
        {card.image ? <img className="faction-role-card-image" src={card.image} alt={`${card.name}卡牌`} loading="lazy" /> : null}
        <div className="faction-role-card-copy">
          <div className="faction-role-card-title">
            <strong>{card.name}</strong>
            <div className="faction-role-card-factions">
              {card.factions.map((faction) => (
                <FactionChip icon={factionIconMap.get(faction)} key={faction} name={faction} />
              ))}
            </div>
          </div>
          <section className="faction-role-card-section">
            <span className="faction-role-card-label">词条</span>
            <div className="chip-row">
              {card.keywords.length
                ? card.keywords.map((keyword) => <span className="chip strong" key={keyword}>{keyword}</span>)
                : <span className="empty-text">无</span>}
            </div>
          </section>
          <section className="faction-role-card-section faction-role-card-skills">
            <span className="faction-role-card-label">技能说明</span>
            <DescriptionList card={card} limit={3} />
          </section>
        </div>
      </div>
    </div>
  );
}

function FactionDetail({
  faction,
  roles,
  factionIconMap,
  mobileOpen = false,
  onClose,
}: {
  faction: FactionRecord | undefined;
  roles: CardRecord[];
  factionIconMap: Map<string, string | null>;
  mobileOpen?: boolean;
  onClose?: () => void;
}) {
  if (!faction) return null;
  return (
    <aside className={classNames("detail-panel faction-detail", mobileOpen && "mobile-detail-open")}>
      {onClose ? (
        <button className="detail-close" onClick={onClose} type="button" aria-label="关闭详情">
          <X size={18} />
        </button>
      ) : null}
      <div className="detail-title">
        <span>阵营</span>
        <h2 className="faction-title">
          {faction.icon ? <img src={faction.icon} alt="" /> : null}
          {faction.name}
        </h2>
        <span className="status-badge status-ready">{faction.keywordCategory}</span>
      </div>
      <section className="detail-section">
        <h3>阵营描述</h3>
        <p>{faction.description}</p>
      </section>
      <section className="detail-section">
        <h3>阶段效果</h3>
        {faction.stageEffects.length ? (
          <ul className="description-list">
            {faction.stageEffects.map((effect) => (
              <li key={effect}>{effect}</li>
            ))}
          </ul>
        ) : (
          <p className="empty-text">暂无阶段效果数据。</p>
        )}
      </section>
      <section className="detail-section">
        <h3>关联角色 <span className="section-count">{roles.length}</span></h3>
        <div className="faction-role-list">
          {roles.length ? roles.map((card) => (
            <FactionRoleAvatar card={card} factionIconMap={factionIconMap} key={card.id} />
          )) : <span className="empty-text">暂无关联角色数据。</span>}
        </div>
      </section>
    </aside>
  );
}

function ComingSoonPage({
  eyebrow,
  title,
  description,
  icon: Icon,
  cards,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: typeof BookOpen;
  cards: Array<{ title: string; description: string }>;
}) {
  return (
    <section className="content-page">
      <div className="page-hero">
        <div>
          <span>{eyebrow}</span>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <Icon size={34} />
      </div>
      <div className="feature-grid">
        {cards.map((card) => (
          <article className="feature-card" key={card.title}>
            <strong>{card.title}</strong>
            <p>{card.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

type LineupSlot = { role?: string; weapon?: string; items?: string[] };

const unavailableLineupRoles = new Set(["钢铁终结者", "小红", "黑暗金刚", "剧毒蛇女", "迅捷虫"]);

function LineupRole({ slot, cardsByName, factionIconMap }: { slot: LineupSlot; cardsByName: Map<string, CardRecord>; factionIconMap: Map<string, string | null> }) {
  if (!slot.role) return <div className="lineup-role-empty"><span>空位</span><small>按对局补充</small></div>;
  const role = cardsByName.get(slot.role);
  if (!role) return <div className="lineup-role missing">资料缺失</div>;
  const weapon = slot.weapon ? cardsByName.get(slot.weapon) : undefined;
  const items = (slot.items || []).map((name) => cardsByName.get(name)).filter((card): card is CardRecord => Boolean(card));
  const equipment = [weapon, ...(slot.items || []).map((name) => cardsByName.get(name))].filter((card): card is CardRecord => Boolean(card));
  const roleEffects = splitRoleUpgradeDescriptions(role);
  const lineupImage = role.goldImage || role.image;
  const roleEffectText = [role.name, ...role.keywords, ...role.descriptions].join(" ");
  const itemEffectTexts = items.map((item) => [item.name, ...item.keywords, ...item.descriptions].join(" "));
  const hasTaunt = roleEffectText.includes("嘲讽") || itemEffectTexts.some((text) => text.includes("嘲讽"));
  const cannotAct = itemEffectTexts.some((text) => text.includes("无法行动"));
  return (
    <div className="lineup-role">
      <button className="lineup-role-button" type="button" aria-label={`查看${role.name}阵容详情`}>
        <span className={classNames("lineup-role-visual", !equipment.length && "without-equipment")}>
          <span className="lineup-role-card-shell">
            {lineupImage ? <img className="lineup-role-card-preview" src={lineupImage} alt="" loading="lazy" /> : <span className="lineup-role-card-fallback">{role.name.slice(0, 1)}</span>}
            {hasTaunt ? <img className="lineup-status-icon taunt" src="/assets/effects/taunt.png" alt="嘲讽" title="嘲讽" /> : null}
            {cannotAct ? <img className="lineup-status-icon stop" src="/assets/effects/stop.png" alt="无法行动" title="无法行动" /> : null}
          </span>
          {equipment.length ? (
            <span className="lineup-equipment-rail" aria-label={`${role.name}推荐携带`}>
              {equipment.map((card) => (
              <span className="lineup-equipment-chip" key={card.id} title={`${card.categoryLabel} · ${card.name}`}>
                {card.originalImage || card.image ? <img src={card.originalImage || card.image || ""} alt="" loading="lazy" /> : null}
              </span>
              ))}
            </span>
          ) : null}
        </span>
        <strong>{role.name}</strong>
        <span>{role.keywords.slice(0, 2).join(" · ") || "角色"}</span>
      </button>
      <div className="lineup-role-popover" role="tooltip">
        {lineupImage ? <img className="lineup-role-card" src={lineupImage} alt={`${role.name}金色卡牌`} loading="lazy" /> : null}
        <div className="lineup-role-details">
          <div className="lineup-role-heading">
            <strong>{role.name}</strong>
            <div className="chip-row">{role.factions.map((faction) => <FactionChip icon={factionIconMap.get(faction)} key={faction} name={faction} />)}</div>
          </div>
          <div className="chip-row">{role.keywords.map((keyword) => <span className="chip strong" key={keyword}>{keyword}</span>)}</div>
          <div className="lineup-role-skills">
            <section>
              <span>基础效果</span>
              {roleEffects.base.map((description, index) => <p key={`${role.id}-base-${index}`}>{description}</p>)}
            </section>
            {roleEffects.upgraded.length ? (
              <section className="upgraded">
                <span>金色升级</span>
                {roleEffects.upgraded.map((description, index) => <p key={`${role.id}-upgraded-${index}`}>{description}</p>)}
              </section>
            ) : null}
          </div>
          <div className="lineup-equipment">
            <span>推荐携带</span>
            <div>
              {equipment.map((card) => (
                <article key={card.id}>
                  {card.originalImage || card.image ? <img src={card.originalImage || card.image || ""} alt="" loading="lazy" /> : null}
                  <p><strong>{card.name}</strong><small>{displayDescriptions(card)[0]}</small></p>
                </article>
              ))}
              {!equipment.length ? <small className="empty-text">优先补充与核心词条匹配的装备</small> : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AiLineupsPage({
  cards,
  maps,
  factionIconMap,
  lineups,
}: {
  cards: CardRecord[];
  maps: MapRecord[];
  factionIconMap: Map<string, string | null>;
  lineups: RecommendedLineup[];
}) {
  const visibleLineups = useMemo(() => lineups.filter((item) => !item.hidden).sort((a, b) => a.order - b.order || a.name.localeCompare(b.name, "zh-Hans-CN")), [lineups]);
  const [selectedId, setSelectedId] = useState("");
  const build = visibleLineups.find((item) => item.id === selectedId) || visibleLineups[0];
  const cardsByName = useMemo(
    () => new Map(cards.filter((card) => !card.hidden && !unavailableLineupRoles.has(card.name) && !card.name.includes("异形")).map((card) => [card.name, card])),
    [cards],
  );
  if (!build) return <section className="content-page"><p className="empty-text">暂无推荐阵容，请在管理后台添加。</p></section>;
  const map = maps.find((item) => item.key === build.mapKey);
  const buffs = build.buffs.map((item) => cards.find((card) => card.category === "buff" && !card.hidden && card.name === item.name && card.quality === item.quality)).filter((card): card is CardRecord => Boolean(card));
  const lineupVideos = build.videos || [];
  return (
    <section className="content-page ai-lineups-page">
      <div className="page-hero ai-lineups-hero">
        <div><span>流派资料</span><h2>推荐阵容</h2><p>由资料库管理员维护的阵容方案，包含站位、装备、地图和增益组合参考。</p></div>
        <Bot size={34} />
      </div>
      <div className="ai-lineups-layout">
        <nav className="lineup-selector" aria-label="流派选择">
          {visibleLineups.map((item) => (
            <button className={classNames(item.id === build.id && "active")} key={item.id} onClick={() => setSelectedId(item.id)} type="button">
              <span>{item.label}</span><strong>{item.name}</strong><small>{item.keywords.join(" · ")}</small>
            </button>
          ))}
        </nav>
        <article className="lineup-detail">
          <header className="lineup-detail-header">
            <div><span>{build.label}</span><h2>{build.name}</h2><p>{build.summary}</p></div>
            <div className="chip-row">{build.keywords.map((keyword) => <span className="chip strong" key={keyword}>{keyword}</span>)}</div>
          </header>
          <div className="lineup-main-grid">
            <section className="lineup-board-section">
              <div className="lineup-section-title"><div><span>推荐站位</span><h3>最多前排 3 · 后排 3</h3></div><Swords size={20} /></div>
              <div className="lineup-board">
                <div className="lineup-lane front">
                  <span className="lineup-row-label"><b>前排</b><small>承伤 · 启动</small></span>
                  <div className="lineup-row">{build.slots.slice(0, 3).map((slot, index) => <LineupRole cardsByName={cardsByName} factionIconMap={factionIconMap} key={`${slot.role || "empty"}-${index}`} slot={slot} />)}</div>
                </div>
                <div className="lineup-lane back">
                  <span className="lineup-row-label"><b>后排</b><small>输出 · 辅助</small></span>
                  <div className="lineup-row">{build.slots.slice(3, 6).map((slot, index) => <LineupRole cardsByName={cardsByName} factionIconMap={factionIconMap} key={`${slot.role || "empty"}-${index}`} slot={slot} />)}</div>
                </div>
              </div>
            </section>
            <section className="lineup-strategy">
              <div className="lineup-section-title"><div><span>运转逻辑</span><h3>构筑要点</h3></div><Target size={20} /></div>
              <ol>{build.strategy.map((item) => <li key={item}>{item}</li>)}</ol>
            </section>
          </div>
          <div className="lineup-support-grid">
            <section className="lineup-map">
              <div className="lineup-section-title"><div><span>推荐地图</span><h3>全局环境</h3></div><MapIcon size={20} /></div>
              {map ? <div className="lineup-map-content">{map.icon ? <img src={map.icon} alt="" loading="lazy" /> : null}<div><strong>{map.name}</strong><p>{map.bonusDescription}</p></div></div> : <p className="empty-text">暂无地图资料</p>}
            </section>
            <section className="lineup-buffs">
              <div className="lineup-section-title"><div><span>推荐增益</span><h3>优先选择 2 项</h3></div><Sparkles size={20} /></div>
              <div className="lineup-buff-list">{buffs.map((buff) => <article key={buff.id}>{buff.image ? <img src={buff.image} alt="" loading="lazy" /> : null}<div><strong>{buff.name}</strong><p>{displayDescriptions(buff)[0]}</p></div></article>)}</div>
            </section>
          </div>
          {lineupVideos.length ? (
            <section className="lineup-videos">
              <div className="lineup-section-title"><div><span>相关视频</span><h3>实战与讲解</h3></div><PlaySquare size={20} /></div>
              <div className="lineup-video-links">
                {lineupVideos.map((video) => (
                  <a href={video.url} key={`${video.platform}-${video.url}`} target="_blank" rel="noreferrer">
                    <span>{video.platform === "douyin" ? "抖音" : video.platform === "kuaishou" ? "快手" : video.platform === "bilibili" ? "B站" : "视频"}</span>
                    <strong>{video.title || "查看视频攻略"}</strong>
                  </a>
                ))}
              </div>
            </section>
          ) : null}
        </article>
      </div>
    </section>
  );
}

function GuideContent({
  wordExplanations,
  onOpenMaps,
  onOpenBuffs,
  onOpenCategory,
}: {
  wordExplanations: WordExplanation[];
  onOpenMaps: () => void;
  onOpenBuffs: () => void;
  onOpenCategory: (category: LibraryCategory) => void;
}) {
  const gameRules = [
    {
      index: "01",
      eyebrow: "对局规则",
      title: "游戏概述与核心目标",
      icon: Shield,
      summary: "8 名玩家通过回合制 1V1 对战竞争最终胜利。合理运营经济、搭配卡牌并持续强化阵容，是存活到决赛的核心。",
      points: [
        "每位玩家初始拥有 30 点生命值。",
        "每回合战败后，会根据敌方剩余战力扣除生命值；生命归零即被淘汰。",
        "坚持到最后并赢得最终 1V1 对决，即可获得第一名。",
      ],
    },
    {
      index: "02",
      eyebrow: "开局阶段",
      title: "战前准备：地图与全局增益",
      icon: MapIcon,
      summary: "开局随机提供 3 张地图，由 8 名玩家共同投票。得票最高的地图将为本局提供全局增益，并影响所有玩家的构筑方向。",
      points: [
        "地图效果可能影响经济、成长、战斗、站位或卡牌获取。",
        "当前资料库已整理 13 张地图，可在“地图资料”中查看具体效果。",
        "地图是全局规则，不只是单个角色或单套阵容的额外加成。",
      ],
    },
    {
      index: "03",
      eyebrow: "运营核心",
      title: "经济、刷新与商店等级",
      icon: Database,
      summary: "金币用于购买卡牌、刷新商店和提升商店等级。利息与连胜、连败收益会影响后续可用资源。",
      points: [
        "刷新一次当前商店需要消耗 1 金币。",
        "升级商店可以提高稀有品质卡牌的出现概率。",
        "存钱获取持续收益，或花钱提升即时战力，是每回合的重要取舍。",
      ],
    },
    {
      index: "04",
      eyebrow: "阵容构筑",
      title: "卡牌系统、站位与装备",
      icon: Boxes,
      summary: "场上最多可配置 6 名角色，分为前排 3 个槽位与后排 3 个槽位。角色是战斗主体，其他卡牌用于改变攻击方式、强化属性或提供即时效果。",
      points: [
        "手牌区最多可持有 15 张卡牌，达到上限后需要先使用、装备、合成或出售卡牌腾出位置。",
        "角色卡显示基础攻击力与生命值，并拥有阵营、技能和词条。",
        "每名角色默认可装备 1 张武器、2 张道具（最多 1 张投掷物）；部分消耗卡或增益可扩充道具槽。",
        "资料库当前收录 127 名角色、64 把武器，并包含道具、投掷物和消耗卡资料。",
        "3 张同名同品质的角色或武器可参与合成，获得大幅强化的金色卡牌。",
        "“分裂者”“KAC-变色龙”等特殊卡具备任意合成能力，可作为对应类型的替代材料。",
      ],
    },
    {
      index: "05",
      eyebrow: "协同机制",
      title: "阵营羁绊与策略构筑",
      icon: Swords,
      summary: "角色分属不同阵营。围绕同阵营角色、关键技能或特定词条组合卡牌，可以形成相互触发的协同体系。",
      points: [
        "阵营效果通常需要特定角色组合或达到相应条件后生效。",
        "当前资料库已整理 12 个有角色归属的阵营及其关联角色。",
        "构筑时可同时参考阵营、词条、装备适配与地图增益，不必只追求单一卡牌品质。",
      ],
    },
    {
      index: "06",
      eyebrow: "特殊回合",
      title: "PVE 发育阶段",
      icon: Bot,
      summary: "对局中会穿插 PVE 人机战斗，为玩家提供调整阵容、积累经济和触发成长效果的发育窗口。",
      points: [
        "PVE 前可检查站位、装备分配和角色强度，降低不必要的战斗损失。",
        "部分角色牌带有 PVE 专属说明，其效果或定位需要结合人机回合判断。",
        "利用相对稳定的 PVE 阶段规划升级与成长，可以为后续玩家对战建立优势。",
      ],
    },
  ];

  const shopOdds = [
    { level: 1, green: 100, blue: 0, purple: 0, gold: 0 },
    { level: 2, green: 60, blue: 40, purple: 0, gold: 0 },
    { level: 3, green: 30, blue: 55, purple: 15, gold: 0 },
    { level: 4, green: 15, blue: 40, purple: 35, gold: 10 },
    { level: 5, green: 5, blue: 20, purple: 45, gold: 30 },
  ];

  const shopQualities = [
    { key: "green", label: "绿色" },
    { key: "blue", label: "蓝色" },
    { key: "purple", label: "紫色" },
    { key: "gold", label: "金色" },
  ] as const;

  return (
    <>
      <section className="game-rules-section">
        <div className="section-heading">
          <div>
            <span>完整规则</span>
            <h2>悠悠牌游戏基础</h2>
          </div>
          <BookOpen size={22} />
        </div>
        <div className="game-rule-stats" aria-label="核心对局数据">
          <span><strong>8</strong>名玩家</span>
          <span><strong>30</strong>初始生命</span>
          <span><strong>6</strong>名上阵角色</span>
          <span><strong>1</strong>名最终胜者</span>
        </div>
        <div className="game-rule-list">
          {gameRules.map((rule) => {
            const Icon = rule.icon;
            return (
              <article className="game-rule-entry" key={rule.index}>
                <div className="game-rule-index">{rule.index}</div>
                <div className="game-rule-icon"><Icon size={20} /></div>
                <div className="game-rule-copy">
                  <span>{rule.eyebrow}</span>
                  <h3>{rule.title}</h3>
                  <p>{rule.summary}</p>
                </div>
                <ul>
                  {rule.points.map((point) => (
                    <li key={point}>
                      {point === "当前资料库已整理 13 张地图，可在“地图资料”中查看具体效果。" ? (
                        <>
                          当前资料库已整理 13 张地图，可在
                          <button className="inline-section-link" onClick={onOpenMaps} type="button">地图资料</button>
                          中查看具体效果。
                        </>
                      ) : point === "每名角色默认可装备 1 张武器、2 张道具（最多 1 张投掷物）；部分消耗卡或增益可扩充道具槽。" ? (
                        <>
                          每名角色默认可装备 1 张武器、2 张道具（最多 1 张投掷物）；部分消耗卡或
                          <button className="inline-section-link" onClick={onOpenBuffs} type="button">增益</button>
                          可扩充道具槽。
                        </>
                      ) : point === "资料库当前收录 127 名角色、64 把武器，并包含道具、投掷物和消耗卡资料。" ? (
                        <>
                          资料库当前收录 127 名
                          <button className="inline-section-link" onClick={() => onOpenCategory("role")} type="button">角色</button>
                          、64 把
                          <button className="inline-section-link" onClick={() => onOpenCategory("weapon")} type="button">武器</button>
                          ，并包含
                          <button className="inline-section-link" onClick={() => onOpenCategory("item")} type="button">道具</button>
                          、
                          <button className="inline-section-link" onClick={() => onOpenCategory("throwable")} type="button">投掷物</button>
                          和
                          <button className="inline-section-link" onClick={() => onOpenCategory("consume")} type="button">消耗卡</button>
                          资料。
                        </>
                      ) : point}
                    </li>
                  ))}
                </ul>
              </article>
            );
          })}
        </div>
      </section>
      <section className="guide-section shop-odds-section">
        <div className="section-heading">
          <div>
            <span>商店机制</span>
            <h2>等级与卡牌刷新概率</h2>
          </div>
          <Database size={22} />
        </div>
        <p className="shop-odds-intro">每个商店卡位独立按当前等级概率刷新。等级越高，紫色和金色卡牌出现的机会越大。</p>
        <div className="shop-odds-legend" aria-label="卡牌品质图例">
          {shopQualities.map((quality) => (
            <span key={quality.key}>
              <i className={`quality-swatch ${quality.key}`} />
              {quality.label}
            </span>
          ))}
        </div>
        <div className="shop-odds-list">
          {shopOdds.map((row) => (
            <article className="shop-odds-row" key={row.level}>
              <strong>{row.level}级</strong>
              <div className="shop-odds-bar" aria-label={`${row.level}级商店刷新概率`}>
                {shopQualities.map((quality) => {
                  const value = row[quality.key];
                  return value ? (
                    <span className={`shop-odds-segment ${quality.key}`} key={quality.key} style={{ width: `${value}%` }}>
                      {value}%
                    </span>
                  ) : null;
                })}
              </div>
              <div className="shop-odds-values">
                {shopQualities.map((quality) => (
                  <span key={quality.key}>
                    <i className={`quality-swatch ${quality.key}`} />
                    <b>{quality.label}</b>
                    {row[quality.key]}%
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="guide-section gameplay-tips-section">
        <div className="section-heading">
          <div>
            <span>对局操作</span>
            <h2>实用技巧</h2>
          </div>
          <Sparkles size={22} />
        </div>
        <div className="gameplay-tip-list">
          <article>
            <span className="gameplay-tip-index">01</span>
            <div>
              <strong>锁定商店卡牌</strong>
              <p>商店卡牌列表支持锁定。金币不足时，可以锁住当前商店，使其中的卡牌保留至下一回合，再继续购买。</p>
            </div>
            <small>适合刷到预期牌但没钱购买</small>
          </article>
          <article>
            <span className="gameplay-tip-index">02</span>
            <div>
              <strong>提前进入准备阶段</strong>
              <p>对战开始后，可将游戏切换至后台等待约 3 秒，再返回游戏，以快速跳过对战过程并提前进入下一回合准备阶段。</p>
            </div>
            <small>可增加下回合调整阵容的时间</small>
          </article>
        </div>
      </section>
      <section className="term-section">
        <div className="section-heading">
          <div>
            <span>{wordExplanations.length} 个常用词条</span>
            <h2>词条解释</h2>
          </div>
          <BookOpen size={22} />
        </div>
        <div className="term-grid">
          {wordExplanations.map((term) => (
            <article className="term-entry" key={term.term}>
              <strong>{term.term}</strong>
              <p>{term.description}</p>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function MapLibrary({ maps }: { maps: MapRecord[] }) {
  const displayBonusDescription = (description: string) => {
    const value = description.trim();
    return value && value !== "加成效果待补全" ? value : "未知";
  };

  return (
    <section className="map-section">
      <div className="section-heading">
        <div>
          <span>{maps.length} 张地图</span>
          <h2>开局地图与加成效果</h2>
        </div>
        <Target size={22} />
      </div>
      <div className="map-grid">
        {maps.map((map) => (
          <article className="map-card" key={map.key}>
            {map.background ? <img className="map-bg" src={map.background} alt="" loading="lazy" /> : null}
            <div className="map-card-content">
              {map.icon ? <img className="map-icon" src={map.icon} alt="" loading="lazy" /> : null}
              <div className="map-text">
                <strong>{map.name}</strong>
                <p>{displayBonusDescription(map.bonusDescription)}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function VideosPage({ videos }: { videos: VideoGuide[] }) {
  const [platform, setPlatform] = useState<"all" | VideoGuide["platform"]>("all");
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");
  const publishedVideos = useMemo(() => videos.filter((video) => !video.hidden), [videos]);
  const categories = useMemo(() => Array.from(new Set(publishedVideos.map((video) => video.category))), [publishedVideos]);
  const filteredVideos = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return publishedVideos
      .filter((video) => {
        if (platform !== "all" && video.platform !== platform) return false;
        if (category !== "all" && video.category !== category) return false;
        if (normalizedQuery && !`${video.title} ${video.author} ${video.category}`.toLowerCase().includes(normalizedQuery)) return false;
        return true;
      })
      .sort((a, b) => a.order - b.order || (b.publishedAt || "").localeCompare(a.publishedAt || ""));
  }, [category, platform, publishedVideos, query]);

  return (
    <section className="content-page video-page">
      <div className="page-hero video-page-hero">
        <div>
          <span>视频攻略</span>
          <h2>CFM 悠悠牌视频精选</h2>
          <p>由资料库后台人工筛选和维护，收录值得参考的玩法教学、阵容流派与卡牌攻略。</p>
        </div>
        <PlaySquare size={34} />
      </div>

      <section className="video-library">
        <div className="video-toolbar">
          <label className="search-box">
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索视频、作者或攻略类型" />
          </label>
          <div className="video-platform-tabs" aria-label="视频平台">
            {([
              ["all", "全部"],
              ["douyin", "抖音"],
              ["kuaishou", "快手"],
            ] as const).map(([value, label]) => (
              <button className={classNames(platform === value && "active")} key={value} onClick={() => setPlatform(value)} type="button">
                {label}
              </button>
            ))}
          </div>
          <label className="video-category-filter">
            <span>攻略类型</span>
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="all">全部类型</option>
              {categories.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        </div>

        <div className="video-section-heading">
          <div>
            <span>{publishedVideos.length} 个已收录视频</span>
            <h2>编辑精选</h2>
          </div>
          <Flame size={22} />
        </div>

        {filteredVideos.length ? (
          <div className="video-grid">
            {filteredVideos.map((video) => (
              <a className={classNames("video-card", video.platform)} href={video.url} key={video.id} target="_blank" rel="noreferrer">
                <div className="video-cover">
                  {video.cover ? <img src={video.cover} alt="" loading="lazy" /> : <PlaySquare size={42} />}
                  <span>{video.platform === "douyin" ? "抖音" : "快手"}</span>
                </div>
                <div className="video-card-body">
                  <span>{video.category}</span>
                  <strong>{video.title}</strong>
                  <p>{video.author}</p>
                  <div className="video-meta">
                    <span><Flame size={14} /> {video.popularityLabel}</span>
                    {video.publishedAt ? <time dateTime={video.publishedAt}>{video.publishedAt}</time> : null}
                  </div>
                </div>
              </a>
            ))}
          </div>
        ) : (
          <div className="video-empty">
            <PlaySquare size={28} />
            <strong>{publishedVideos.length ? "当前筛选下暂无视频" : "暂未发布精选视频"}</strong>
            <p>视频将在后台审核并添加后显示在这里。</p>
          </div>
        )}
      </section>
    </section>
  );
}

function BuffLibrary({ buffs, factionIconMap }: { buffs: CardRecord[]; factionIconMap: Map<string, string | null> }) {
  const [query, setQuery] = useState("");
  const [qualityFilter, setQualityFilter] = useState("all");
  const [selectedBuffId, setSelectedBuffId] = useState<string | null>(buffs[0]?.id || null);
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);
  const qualityList = useMemo(() => buildQualityList(buffs), [buffs]);

  const filteredBuffs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return buffs
      .filter((card) => {
        if (qualityFilter !== "all" && card.quality !== qualityFilter) return false;
        if (normalizedQuery && !searchableText(card).includes(normalizedQuery)) return false;
        return true;
      })
      .sort(compareCardsByQualityDesc);
  }, [buffs, qualityFilter, query]);

  const selectedBuff = useMemo(() => {
    if (!filteredBuffs.length) return null;
    return filteredBuffs.find((card) => card.id === selectedBuffId) || filteredBuffs[0];
  }, [filteredBuffs, selectedBuffId]);

  useEffect(() => {
    if (selectedBuff && selectedBuff.id !== selectedBuffId) {
      setSelectedBuffId(selectedBuff.id);
    }
  }, [selectedBuff, selectedBuffId]);

  useEffect(() => {
    if (qualityFilter !== "all" && !qualityList.includes(qualityFilter)) {
      setQualityFilter("all");
    }
  }, [qualityFilter, qualityList]);

  return (
    <section className="workspace basics-buff-workspace">
        <div className="library-panel">
          <div className="filters buff-filters">
            <label className="buff-search-filter">
              <span>搜索</span>
              <span className="search-box">
                <Search size={18} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索增益名称、词条、描述、资源名" />
              </span>
            </label>
            <div className="filter-grid buff-filter-grid">
              <label>
                <span>品质</span>
                <select value={qualityFilter} onChange={(event) => setQualityFilter(event.target.value)}>
                  <option value="all">全部品质</option>
                  {qualityList.map((quality) => (
                    <option key={quality} value={quality} style={qualityOptionStyle(quality)}>
                      {qualityLabel(quality)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <div className="result-line">
            <span>{filteredBuffs.length} 张增益卡</span>
          </div>

          <div className="card-grid">
            {filteredBuffs.map((card) => (
              <CardTile
                key={card.id}
                card={card}
                selected={selectedBuff?.id === card.id}
                factionIconMap={factionIconMap}
                onSelect={() => {
                  setSelectedBuffId(card.id);
                  setMobileDetailOpen(true);
                }}
              />
            ))}
          </div>
        </div>
        <button
          className={classNames("mobile-detail-backdrop", mobileDetailOpen && "visible")}
          onClick={() => setMobileDetailOpen(false)}
          type="button"
          aria-label="关闭详情"
        />
        <DetailPanel card={selectedBuff} factionIconMap={factionIconMap} mobileOpen={mobileDetailOpen} onClose={() => setMobileDetailOpen(false)} />
    </section>
  );
}

function GameBasicsPage({
  wordExplanations,
  maps,
  buffs,
  factionIconMap,
  onOpenCategory,
  section,
  onSectionChange,
}: {
  wordExplanations: WordExplanation[];
  maps: MapRecord[];
  buffs: CardRecord[];
  factionIconMap: Map<string, string | null>;
  onOpenCategory: (category: LibraryCategory) => void;
  section: BasicsSection;
  onSectionChange: (section: BasicsSection) => void;
}) {
  const basicsSections: Array<{ id: BasicsSection; label: string; icon: typeof GraduationCap }> = [
    { id: "guide", label: "基础教学", icon: GraduationCap },
    { id: "maps", label: "地图资料", icon: MapIcon },
    { id: "buffs", label: "增益资料", icon: Layers },
  ];

  return (
    <section className={classNames("content-page basics-page", `basics-page-${section}`)}>
      <div className="page-hero">
        <div>
          <span>游戏基础</span>
          <h2>理解规则、地图与增益</h2>
          <p>集中查看悠悠牌的基础规则、实战决策、开局地图和增益效果，建立完整的玩法认知。</p>
        </div>
        <GraduationCap size={34} />
      </div>
      <nav className="basics-nav" aria-label="游戏基础分类">
        {basicsSections.map((item) => {
          const Icon = item.icon;
          return (
            <button className={classNames(section === item.id && "active")} key={item.id} onClick={() => onSectionChange(item.id)} type="button">
              <Icon size={17} />
              {item.label}
            </button>
          );
        })}
      </nav>
      {section === "guide" ? (
        <GuideContent
          wordExplanations={wordExplanations}
          onOpenMaps={() => onSectionChange("maps")}
          onOpenBuffs={() => onSectionChange("buffs")}
          onOpenCategory={onOpenCategory}
        />
      ) : section === "maps" ? (
        <MapLibrary maps={maps} />
      ) : (
        <BuffLibrary buffs={buffs} factionIconMap={factionIconMap} />
      )}
    </section>
  );
}

export function App() {
  const initialRoute = useMemo(readAppRoute, []);
  const [cards, setCards] = useState<CardRecord[]>([]);
  const [factions, setFactions] = useState<FactionRecord[]>([]);
  const [maps, setMaps] = useState<MapRecord[]>([]);
  const [wordExplanations, setWordExplanations] = useState<WordExplanation[]>([]);
  const [videoGuides, setVideoGuides] = useState<VideoGuide[]>([]);
  const [recommendedLineups, setRecommendedLineups] = useState<RecommendedLineup[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<SitePage>(initialRoute.page);
  const [view, setView] = useState<ViewMode>(initialRoute.view);
  const [category, setCategory] = useState<LibraryCategory>(initialRoute.category);
  const [basicsSection, setBasicsSection] = useState<BasicsSection>(initialRoute.basicsSection);
  const [aiSection, setAiSection] = useState<AiSection>(initialRoute.aiSection);
  const [query, setQuery] = useState("");
  const [factionFilter, setFactionFilter] = useState("all");
  const [keywordFilter, setKeywordFilter] = useState("all");
  const [qualityFilter, setQualityFilter] = useState("all");
  const [showHiddenCards, setShowHiddenCards] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [selectedFaction, setSelectedFaction] = useState<string>("");
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);

  const applyRoute = (route: AppRoute) => {
    setPage(route.page);
    setView(route.view);
    setCategory(route.category);
    setBasicsSection(route.basicsSection);
    setAiSection(route.aiSection);
    setMobileDetailOpen(false);
  };

  const navigate = (route: AppRoute, replace = false) => {
    const nextHash = appRouteHash(route);
    if (window.location.hash === nextHash) {
      applyRoute(route);
      return;
    }
    if (replace) {
      window.history.replaceState(null, "", nextHash);
      applyRoute(route);
      return;
    }
    window.location.hash = nextHash;
  };

  const navigateToPage = (nextPage: SitePage) => {
    if (nextPage === "guide") {
      navigate({ page: "guide", view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" });
    } else if (nextPage === "library") {
      navigate({ page: "library", view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" });
    } else if (nextPage === "ai") {
      navigate({ page: "ai", view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" });
    } else {
      navigate({ page: nextPage, view: "cards", category: "all", basicsSection: "guide", aiSection: "lineups" });
    }
  };

  const navigateToLibrary = (nextCategory: LibraryCategory) => {
    navigate({ page: "library", view: "cards", category: nextCategory, basicsSection: "guide", aiSection: "lineups" });
  };

  useEffect(() => {
    const syncRoute = () => applyRoute(readAppRoute());
    window.addEventListener("hashchange", syncRoute);
    if (!window.location.hash) {
      navigate(initialRoute, true);
    }
    return () => window.removeEventListener("hashchange", syncRoute);
  }, []);

  useEffect(() => {
    const categoryTitle = categories.find((item) => item.id === category)?.label || "全部";
    const title =
      page === "guide"
        ? basicsSection === "maps"
          ? "地图资料"
          : basicsSection === "buffs"
            ? "增益资料"
            : "基础教学"
        : page === "ai"
          ? "推荐阵容"
          : page === "videos"
            ? "视频攻略"
            : view === "factions"
              ? "阵营资料"
              : `${categoryTitle}卡牌`;
    document.title = `${title} | CF 悠悠牌资料库`;
  }, [basicsSection, category, page, view]);

  useEffect(() => {
    loadSiteData()
      .then((data) => {
        setCards(data.cards);
        setFactions(data.factions);
        setMaps(data.maps);
        setWordExplanations(data.wordExplanations);
        setVideoGuides(data.videoGuides);
        setRecommendedLineups(data.recommendedLineups);
        setSummary(data.summary);
        const firstVisibleCard = data.cards.find((card) => !card.hidden && card.name === "刀锋") || data.cards.find((card) => !card.hidden);
        setSelectedCardId(firstVisibleCard?.id || null);
        const firstVisibleFaction = data.factions.find((faction) => !faction.hidden && faction.name === "山海经") || data.factions.find((faction) => !faction.hidden);
        setSelectedFaction(firstVisibleFaction?.name || "");
      })
      .catch((loadError: Error) => setError(loadError.message))
      .finally(() => setLoading(false));
  }, []);

  const visibleCards = useMemo(() => cards.filter((card) => !card.hidden), [cards]);
  const visibleFactions = useMemo(() => factions.filter((faction) => !faction.hidden), [factions]);
  const libraryCards = useMemo(
    () => cards.filter((card) => card.category !== "buff" && (showHiddenCards || !card.hidden)),
    [cards, showHiddenCards],
  );
  const categoryCounts = useMemo(() => countByCategory(libraryCards), [libraryCards]);
  const buffCards = useMemo(() => visibleCards.filter((card) => card.category === "buff"), [visibleCards]);
  const visibleFactionNames = useMemo(() => new Set(visibleFactions.map((faction) => faction.name)), [visibleFactions]);
  const factionsList = useMemo(() => Array.from(new Set(libraryCards.filter((card) => card.category === "role").flatMap((card) => card.factions))).filter((faction) => visibleFactionNames.has(faction)), [libraryCards, visibleFactionNames]);
  const keywordsList = useMemo(() => Array.from(new Set(libraryCards.flatMap((card) => card.keywords))).filter(Boolean), [libraryCards]);
  const qualityList = useMemo(() => buildQualityList(libraryCards.filter((card) => category === "all" || card.category === category)), [category, libraryCards]);
  const factionIconMap = useMemo(() => new Map(visibleFactions.map((faction) => [faction.name, faction.icon])), [visibleFactions]);
  const factionRoleMap = useMemo(() => {
    const roleMap = new Map<string, CardRecord[]>();
    visibleFactions.forEach((faction) => roleMap.set(faction.name, []));
    cards
      .filter((card) => card.category === "role")
      .forEach((card) => {
        card.factions.forEach((faction) => {
          roleMap.get(faction)?.push(card);
        });
      });
    roleMap.forEach((roleCards) => roleCards.sort(compareCardsByQualityDesc));
    return roleMap;
  }, [cards, visibleFactions]);

  const filteredCards = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return libraryCards
      .filter((card) => {
        if (category !== "all" && card.category !== category) return false;
        if (factionFilter !== "all" && !card.factions.includes(factionFilter)) return false;
        if (keywordFilter !== "all" && !card.keywords.includes(keywordFilter)) return false;
        if (qualityFilter !== "all" && card.quality !== qualityFilter) return false;
        if (normalizedQuery && !searchableText(card).includes(normalizedQuery)) return false;
        return true;
      })
      .sort(compareCardsByQualityDesc);
  }, [libraryCards, category, factionFilter, keywordFilter, qualityFilter, query]);

  const selectedCard = useMemo(() => {
    if (!filteredCards.length) return null;
    return filteredCards.find((card) => card.id === selectedCardId) || filteredCards[0];
  }, [filteredCards, selectedCardId]);

  const selectedFactionData = visibleFactions.find((faction) => faction.name === selectedFaction);

  useEffect(() => {
    if (selectedCard && selectedCard.id !== selectedCardId) {
      setSelectedCardId(selectedCard.id);
    }
  }, [selectedCard, selectedCardId]);

  useEffect(() => {
    if (category !== "all" && category !== "role" && factionFilter !== "all") {
      setFactionFilter("all");
    }
  }, [category, factionFilter]);

  useEffect(() => {
    if (qualityFilter !== "all" && !qualityList.includes(qualityFilter)) {
      setQualityFilter("all");
    }
  }, [qualityFilter, qualityList]);

  useEffect(() => {
    if (selectedFaction && !visibleFactions.some((faction) => faction.name === selectedFaction)) {
      setSelectedFaction(visibleFactions[0]?.name || "");
    }
  }, [selectedFaction, visibleFactions]);

  if (loading) {
    return <main className="app-shell loading-state">正在加载悠悠牌资料库...</main>;
  }

  if (error) {
    return <main className="app-shell loading-state error-state">{error}</main>;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">
            <img src={ladderAssets.cfLogo} alt="" />
          </div>
          <div>
            <h1>CF 悠悠牌资料库</h1>
          </div>
        </div>
        <nav className="main-nav" aria-label="主导航">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button className={classNames(page === item.id && "active")} key={item.id} onClick={() => navigateToPage(item.id)} type="button">
                <Icon size={16} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </header>

      {page === "library" ? (
        <>
          <section className="dashboard">
            <div className="hero-copy">
              <div className="hero-copy-text">
                <h2>专业资料库</h2>
                <p>系统整理角色、武器、投掷、道具、消耗、阵营，为卡牌查询、阵容研究和实战决策提供可靠参考。</p>
              </div>
            </div>
            <div className="stat-grid">
              {categoryCounts.map((item) => {
                const Icon = item.icon;
                return (
                  <button className="stat-card" key={item.id} onClick={() => navigateToLibrary(item.id)} type="button">
                    <Icon size={20} />
                    <span>{item.label}</span>
                    <strong>{item.count}</strong>
                  </button>
                );
              })}
              <button
                className="stat-card"
                onClick={() => navigate({ page: "library", view: "factions", category: "all", basicsSection: "guide", aiSection: "lineups" })}
                type="button"
              >
                <Swords size={20} />
                <span>阵营</span>
                <strong>{visibleFactions.length}</strong>
              </button>
            </div>
          </section>

          {view === "cards" ? (
            <section className="workspace">
              <div className="library-panel">
                <div className="filters">
                  <label className="search-box">
                    <Search size={18} />
                    <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索名称、词条、描述、资源名" />
                  </label>
                  <div className="tabs">
                    {categories.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button className={classNames(category === item.id && "active")} key={item.id} onClick={() => navigateToLibrary(item.id)} type="button">
                      <Icon size={16} />
                      {item.label}
                    </button>
                  );
                    })}
                  </div>
                  <div className="filter-grid">
                    {category === "all" || category === "role" ? (
                      <label>
                        <span><Filter size={14} /> 阵营</span>
                        <select value={factionFilter} onChange={(event) => setFactionFilter(event.target.value)}>
                          <option value="all">全部阵营</option>
                          {factionsList.map((faction) => <option key={faction} value={faction}>{faction}</option>)}
                        </select>
                      </label>
                    ) : null}
                    <label>
                      <span>词条</span>
                      <select value={keywordFilter} onChange={(event) => setKeywordFilter(event.target.value)}>
                        <option value="all">全部词条</option>
                        {keywordsList.map((keyword) => <option key={keyword} value={keyword}>{keyword}</option>)}
                      </select>
                    </label>
                    <label>
                      <span>品质</span>
                      <select value={qualityFilter} onChange={(event) => setQualityFilter(event.target.value)}>
                        <option value="all">全部品质</option>
                        {qualityList.map((quality) => (
                          <option key={quality} value={quality} style={qualityOptionStyle(quality)}>
                            {qualityLabel(quality)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="checkbox-filter">
                      <span><EyeOff size={14} /> 隐藏卡牌</span>
                      <span className="checkbox-control">
                        <input
                          type="checkbox"
                          checked={showHiddenCards}
                          onChange={(event) => setShowHiddenCards(event.target.checked)}
                        />
                        显示隐藏卡牌
                      </span>
                    </label>
                  </div>
                </div>

                <div className="result-line">
                  <span>{filteredCards.length} 张卡牌</span>
                </div>

                <div className="card-grid">
                  {filteredCards.map((card) => (
                    <CardTile
                      key={card.id}
                      card={card}
                      selected={selectedCard?.id === card.id}
                      factionIconMap={factionIconMap}
                      onSelect={() => {
                        setSelectedCardId(card.id);
                        setMobileDetailOpen(true);
                      }}
                    />
                  ))}
                </div>
              </div>
              <button
                className={classNames("mobile-detail-backdrop", mobileDetailOpen && "visible")}
                onClick={() => setMobileDetailOpen(false)}
                type="button"
                aria-label="关闭详情"
              />
              <DetailPanel card={selectedCard} factionIconMap={factionIconMap} mobileOpen={mobileDetailOpen} onClose={() => setMobileDetailOpen(false)} />
            </section>
          ) : (
            <section className="workspace">
              <FactionPanel
                factions={visibleFactions}
                factionRoleMap={factionRoleMap}
                selectedFaction={selectedFaction}
                onSelect={(factionName) => {
                  setSelectedFaction(factionName);
                  setMobileDetailOpen(true);
                }}
              />
              <button
                className={classNames("mobile-detail-backdrop", mobileDetailOpen && "visible")}
                onClick={() => setMobileDetailOpen(false)}
                type="button"
                aria-label="关闭详情"
              />
              <FactionDetail
                faction={selectedFactionData}
                roles={factionRoleMap.get(selectedFaction) || []}
                factionIconMap={factionIconMap}
                mobileOpen={mobileDetailOpen}
                onClose={() => setMobileDetailOpen(false)}
              />
            </section>
          )}
        </>
      ) : page === "guide" ? (
        <GameBasicsPage
          wordExplanations={wordExplanations}
          maps={maps}
          buffs={buffCards}
          factionIconMap={factionIconMap}
          section={basicsSection}
          onSectionChange={(nextSection) => navigate({ page: "guide", view: "cards", category: "all", basicsSection: nextSection, aiSection: "lineups" })}
          onOpenCategory={(nextCategory) => {
            navigateToLibrary(nextCategory);
          }}
        />
      ) : page === "ai" ? (
        <AiLineupsPage cards={cards} maps={maps} factionIconMap={factionIconMap} lineups={recommendedLineups} />
      ) : (
        <VideosPage videos={videoGuides} />
      )}
    </main>
  );
}
