import type { CardRecord, FactionRecord, MapRecord, RecommendedLineup, Summary, VideoGuide, WordExplanation } from "./types";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`无法加载数据：${path}`);
  }
  return response.json() as Promise<T>;
}

export async function loadSiteData() {
  const [cards, factions, maps, wordExplanations, videoGuides, recommendedLineups, summary] = await Promise.all([
    fetchJson<CardRecord[]>("/data/cards.json"),
    fetchJson<FactionRecord[]>("/data/factions-normalized.json"),
    fetchJson<MapRecord[]>("/data/maps-normalized.json"),
    fetchJson<WordExplanation[]>("/data/word-explanations.json"),
    fetchJson<VideoGuide[]>("/data/video-guides.json"),
    fetchJson<RecommendedLineup[]>("/data/recommended-lineups.json"),
    fetchJson<Summary>("/data/summary.json"),
  ]);
  return { cards, factions, maps, wordExplanations, videoGuides, recommendedLineups, summary };
}
