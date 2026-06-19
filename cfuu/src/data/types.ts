export type CardCategory = "role" | "weapon" | "throwable" | "item" | "consume" | "buff";

export type CardRecord = {
  id: string;
  category: CardCategory;
  categoryLabel: string;
  name: string;
  image: string | null;
  goldImage: string | null;
  originalImage: string | null;
  avatar: string | null;
  quality: string | null;
  factions: string[];
  keywords: string[];
  descriptions: string[];
  resource: string;
  matchStatus: string;
  hidden: boolean;
  raw: Record<string, unknown>;
};

export type FactionRole = {
  role_id: number;
  name: string | null;
  name_source: string | null;
};

export type FactionRecord = {
  baseName: string;
  name: string;
  keywordCategory: string;
  description: string;
  stageEffects: string[];
  roles: FactionRole[];
  icon: string | null;
  hidden: boolean;
  raw: Record<string, unknown> | null;
};

export type MapRecord = {
  key: string;
  name: string;
  bonusDescription: string;
  icon: string | null;
  background: string | null;
  iconResource: string | null;
  backgroundResource: string | null;
  raw: Array<Record<string, unknown>>;
};

export type WordExplanation = {
  term: string;
  description: string;
  sourceIndex: number;
};

export type VideoGuide = {
  id: string;
  platform: "douyin" | "kuaishou";
  title: string;
  author: string;
  url: string;
  category: string;
  duration: string | null;
  popularity: number;
  popularityLabel: string;
  publishedAt: string | null;
  cover: string | null;
  order: number;
  hidden: boolean;
};

export type LineupVideoLink = {
  platform: "douyin" | "kuaishou" | "bilibili" | "other";
  title: string;
  url: string;
};

export type RecommendedLineup = {
  id: string;
  name: string;
  label: string;
  summary: string;
  strategy: string[];
  keywords: string[];
  slots: Array<{ role?: string; weapon?: string; items?: string[] }>;
  mapKey: string;
  buffs: Array<{ name: string; quality: string }>;
  videos: LineupVideoLink[];
  order: number;
  hidden: boolean;
};

export type Summary = {
  generatedAt: string;
  counts: {
    roles: number;
    weapons: number;
    throwables: number;
    items: number;
    consumes: number;
    buffs: number;
    factions: number;
    maps: number;
    cards: number;
  };
};
