import { createServer } from "node:http";
import { spawnSync } from "node:child_process";
import { timingSafeEqual } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const projectRoot = resolve(__dirname, "..");
const adminRoot = join(projectRoot, "admin");
const publicRoot = join(projectRoot, "public");
const dataRoot = join(projectRoot, "data");
const cardsPath = join(publicRoot, "data", "cards.json");
const factionsPath = join(publicRoot, "data", "factions-normalized.json");
const overridesPath = join(dataRoot, "card-overrides.json");
const customCardsPath = join(dataRoot, "custom-cards.json");
const factionOverridesPath = join(dataRoot, "faction-overrides.json");
const videoGuidesPath = join(dataRoot, "video-guides.json");
const recommendedLineupsPath = join(dataRoot, "recommended-lineups.json");
const overrideBackupsRoot = join(dataRoot, "override-backups");
const port = Number(process.env.CFUU_ADMIN_PORT || 5174);
const adminUser = process.env.CFUU_ADMIN_USER || "";
const adminPassword = process.env.CFUU_ADMIN_PASSWORD || "";
const adminNoIndexHeaders = {
  "cache-control": "no-store, max-age=0",
  "x-robots-tag": "noindex, nofollow, noarchive",
};

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

function readJson(path, fallback) {
  if (!existsSync(path)) return fallback;
  return JSON.parse(readFileSync(path, "utf8"));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function backupOverrides(path = overridesPath, prefix = "card-overrides") {
  if (!existsSync(path)) return;
  mkdirSync(overrideBackupsRoot, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  copyFileSync(path, join(overrideBackupsRoot, `${prefix}-${stamp}.json`));
}

function rebuildPreparedData() {
  const result = spawnSync(process.execPath, ["scripts/prepare-data.mjs"], {
    cwd: projectRoot,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || "prepare-data failed");
  }
}

function applyOverrides(cards, overrides) {
  return cards.map((card) => {
    const override = overrides[card.id] || overrides[card.resource];
    if (!override) return { ...card, hidden: Boolean(card.hidden) };
    return {
      ...card,
      name: typeof override.name === "string" && override.name.trim() ? override.name.trim() : card.name,
      quality: typeof override.quality === "string" && override.quality.trim() ? override.quality.trim() : card.quality,
      factions: Array.isArray(override.factions) ? override.factions : card.factions,
      keywords: Array.isArray(override.keywords) ? override.keywords : card.keywords,
      descriptions: Array.isArray(override.descriptions) ? override.descriptions : card.descriptions,
      hidden: Boolean(override.hidden),
    };
  });
}

function cleanStringList(value) {
  return Array.isArray(value) ? value.map(String).map((item) => item.trim()).filter(Boolean) : [];
}

function cleanVideoGuide(value, id = "") {
  const platform = value.platform === "kuaishou" ? "kuaishou" : "douyin";
  return {
    id: id || String(value.id || "").trim(),
    platform,
    title: String(value.title || "").trim() || "未命名视频",
    author: String(value.author || "").trim() || "未知作者",
    url: String(value.url || "").trim(),
    category: String(value.category || "").trim() || "其他攻略",
    duration: String(value.duration || "").trim() || null,
    popularity: Math.max(0, Number(value.popularity) || 0),
    popularityLabel: String(value.popularityLabel || "").trim(),
    publishedAt: String(value.publishedAt || "").trim() || null,
    cover: String(value.cover || "").trim() || null,
    order: Math.max(0, Number(value.order) || 0),
    hidden: Boolean(value.hidden),
  };
}

function cleanLineupSlot(value) {
  return {
    ...(String(value?.role || "").trim() ? { role: String(value.role).trim() } : {}),
    ...(String(value?.weapon || "").trim() ? { weapon: String(value.weapon).trim() } : {}),
    ...(cleanStringList(value?.items).length ? { items: cleanStringList(value.items) } : {}),
  };
}

function cleanLineupVideo(value) {
  const platform = ["douyin", "kuaishou", "bilibili", "other"].includes(value?.platform) ? value.platform : "douyin";
  const url = String(value?.url || "").trim();
  const title = String(value?.title || "").trim();
  return {
    platform,
    title: title || (platform === "kuaishou" ? "快手攻略" : platform === "bilibili" ? "B站攻略" : platform === "douyin" ? "抖音攻略" : "视频攻略"),
    url,
  };
}

function cleanRecommendedLineup(value, id = "") {
  const slots = Array.from({ length: 6 }, (_, index) => cleanLineupSlot(value.slots?.[index]));
  return {
    id: id || String(value.id || "").trim() || `lineup-${Date.now()}`,
    name: String(value.name || "").trim() || "未命名阵容",
    label: String(value.label || "").trim() || "自定义阵容",
    summary: String(value.summary || "").trim(),
    strategy: cleanStringList(value.strategy),
    keywords: cleanStringList(value.keywords),
    slots,
    mapKey: String(value.mapKey || "").trim(),
    buffs: Array.from({ length: 2 }, (_, index) => ({
      name: String(value.buffs?.[index]?.name || "").trim(),
      quality: String(value.buffs?.[index]?.quality || "gold").trim() || "gold",
    })).filter((buff) => buff.name),
    videos: Array.isArray(value.videos) ? value.videos.map(cleanLineupVideo).filter((video) => video.url) : [],
    order: Math.max(0, Number(value.order) || 0),
    hidden: Boolean(value.hidden),
  };
}

function extractUrl(value) {
  const match = String(value || "").match(/https?:\/\/[^\s]+/i);
  return match ? match[0].replace(/[，。；、）)\]}>"']+$/u, "") : "";
}

function videoPlatform(url) {
  const hostname = new URL(url).hostname.toLowerCase();
  if (hostname.includes("kuaishou.com") || hostname.includes("gifshow.com")) return "kuaishou";
  if (hostname.includes("douyin.com") || hostname.includes("iesdouyin.com")) return "douyin";
  throw new Error("目前仅支持抖音和快手视频链接");
}

function decodeHtml(value) {
  return String(value || "")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)));
}

function readMeta(html, names) {
  for (const name of names) {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const patterns = [
      new RegExp(`<meta[^>]+(?:property|name)=["']${escaped}["'][^>]+content=["']([^"']*)["'][^>]*>`, "i"),
      new RegExp(`<meta[^>]+content=["']([^"']*)["'][^>]+(?:property|name)=["']${escaped}["'][^>]*>`, "i"),
    ];
    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match?.[1]) return decodeHtml(match[1]).trim();
    }
  }
  return "";
}

function videoToken(url, platform) {
  const patterns = platform === "douyin"
    ? [/\/(?:video|shipin)\/(\d+)/, /modal_id=(\d+)/]
    : [/\/short-video\/([^/?#]+)/, /\/photo\/([^/?#]+)/, /photoId=([^&#]+)/];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match?.[1]) return match[1];
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function parseVideoLink(input) {
  const sharedUrl = extractUrl(input);
  if (!sharedUrl) throw new Error("没有识别到有效链接");
  const initialPlatform = videoPlatform(sharedUrl);
  let finalUrl = sharedUrl;
  let html = "";
  let warning = "";
  try {
    const result = await fetch(sharedUrl, {
      redirect: "follow",
      signal: AbortSignal.timeout(12_000),
      headers: {
        "accept-language": "zh-CN,zh;q=0.9",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
      },
    });
    finalUrl = result.url || sharedUrl;
    html = await result.text();
  } catch (error) {
    warning = `平台页面解析失败，可手工补充信息：${error.message}`;
  }
  const platform = videoPlatform(finalUrl) || initialPlatform;
  const title = readMeta(html, ["og:title", "twitter:title"]) || decodeHtml(html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1] || "");
  const author = readMeta(html, ["author", "og:site_name"]);
  const cover = readMeta(html, ["og:image", "twitter:image"]);
  const description = readMeta(html, ["og:description", "description"]);
  const token = videoToken(finalUrl, platform);
  return {
    id: `${platform}-${token}`,
    platform,
    title: title.replace(/\s*[-_｜|]\s*(抖音|快手).*$/i, "").trim(),
    author,
    url: finalUrl,
    category: "其他攻略",
    duration: null,
    popularity: 0,
    popularityLabel: "",
    publishedAt: null,
    cover: cover || null,
    order: 0,
    hidden: false,
    description,
    warning,
  };
}

function applyFactionOverrides(factions, overrides) {
  return factions.map((faction) => {
    const override = overrides[faction.baseName] || overrides[faction.name];
    if (!override) return { ...faction, hidden: Boolean(faction.hidden) };
    return {
      ...faction,
      name: typeof override.name === "string" && override.name.trim() ? override.name.trim() : faction.name,
      keywordCategory: typeof override.keywordCategory === "string" && override.keywordCategory.trim() ? override.keywordCategory.trim() : faction.keywordCategory,
      description: typeof override.description === "string" && override.description.trim() ? override.description.trim() : faction.description,
      stageEffects: Array.isArray(override.stageEffects) ? cleanStringList(override.stageEffects) : faction.stageEffects,
      hidden: Boolean(override.hidden),
    };
  });
}

function send(response, status, body, contentType = "text/plain; charset=utf-8", headers = {}) {
  response.writeHead(status, { "content-type": contentType, ...headers });
  response.end(body);
}

function timingSafeEqualString(left, right) {
  const leftBuffer = Buffer.from(String(left));
  const rightBuffer = Buffer.from(String(right));
  if (leftBuffer.length !== rightBuffer.length) return false;
  return timingSafeEqual(leftBuffer, rightBuffer);
}

function isAuthenticated(request) {
  if (!adminUser || !adminPassword) return false;
  const header = request.headers.authorization || "";
  if (!header.startsWith("Basic ")) return false;
  let decoded = "";
  try {
    decoded = Buffer.from(header.slice(6), "base64").toString("utf8");
  } catch {
    return false;
  }
  const separator = decoded.indexOf(":");
  if (separator === -1) return false;
  const user = decoded.slice(0, separator);
  const password = decoded.slice(separator + 1);
  return timingSafeEqualString(user, adminUser) && timingSafeEqualString(password, adminPassword);
}

function requireAdminAuth(request, response) {
  if (isAuthenticated(request)) return true;
  send(response, 401, "Authentication required", "text/plain; charset=utf-8", {
    ...adminNoIndexHeaders,
    "www-authenticate": 'Basic realm="CFUU Admin", charset="UTF-8"',
  });
  return false;
}

function readBody(request) {
  return new Promise((resolveBody, reject) => {
    let body = "";
    request.setEncoding("utf8");
    request.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        reject(new Error("Request body too large"));
        request.destroy();
      }
    });
    request.on("end", () => resolveBody(body));
    request.on("error", reject);
  });
}

function safeStaticPath(root, pathname) {
  const relative = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, "");
  const resolved = resolve(root, relative.replace(/^[/\\]/, ""));
  return resolved.startsWith(resolve(root)) ? resolved : null;
}

function serveFile(response, root, pathname) {
  const filePath = safeStaticPath(root, pathname);
  if (!filePath || !existsSync(filePath)) {
    send(response, 404, "Not found");
    return;
  }
  send(
    response,
    200,
    readFileSync(filePath),
    contentTypes[extname(filePath)] || "application/octet-stream",
    root === adminRoot ? adminNoIndexHeaders : {},
  );
}

async function handleApi(request, response, url) {
  if (url.pathname === "/api/cards" && request.method === "GET") {
    const cards = readJson(cardsPath, []);
    const factions = readJson(factionsPath, []);
    const overrides = readJson(overridesPath, {});
    const factionOverrides = readJson(factionOverridesPath, {});
    send(response, 200, JSON.stringify({ cards: applyOverrides(cards, overrides), factions: applyFactionOverrides(factions, factionOverrides), overrides, factionOverrides }), "application/json; charset=utf-8");
    return;
  }

  if (url.pathname === "/api/videos" && request.method === "GET") {
    send(response, 200, JSON.stringify({ videos: readJson(videoGuidesPath, []) }), "application/json; charset=utf-8");
    return;
  }

  if (url.pathname === "/api/lineups" && request.method === "GET") {
    send(response, 200, JSON.stringify({ lineups: readJson(recommendedLineupsPath, []) }), "application/json; charset=utf-8");
    return;
  }

  if (url.pathname === "/api/lineups" && request.method === "POST") {
    const body = JSON.parse(await readBody(request) || "{}");
    const lineups = readJson(recommendedLineupsPath, []);
    const lineup = cleanRecommendedLineup(body);
    if (lineups.some((item) => item.id === lineup.id)) {
      send(response, 409, "阵容 ID 已存在");
      return;
    }
    backupOverrides(recommendedLineupsPath, "recommended-lineups");
    lineups.push(lineup);
    writeJson(recommendedLineupsPath, lineups);
    rebuildPreparedData();
    send(response, 201, JSON.stringify({ ok: true, id: lineup.id }), "application/json; charset=utf-8");
    return;
  }

  const lineupDuplicateMatch = url.pathname.match(/^\/api\/lineups\/(.+)\/duplicate$/);
  if (lineupDuplicateMatch && request.method === "POST") {
    const id = decodeURIComponent(lineupDuplicateMatch[1]);
    const lineups = readJson(recommendedLineupsPath, []);
    const source = lineups.find((item) => item.id === id);
    if (!source) {
      send(response, 404, "阵容不存在");
      return;
    }
    const duplicate = cleanRecommendedLineup({
      ...source,
      id: `lineup-${Date.now()}`,
      name: `${source.name}（复制）`,
      order: lineups.length,
    });
    backupOverrides(recommendedLineupsPath, "recommended-lineups");
    lineups.push(duplicate);
    writeJson(recommendedLineupsPath, lineups);
    rebuildPreparedData();
    send(response, 201, JSON.stringify({ ok: true, id: duplicate.id }), "application/json; charset=utf-8");
    return;
  }

  const lineupMatch = url.pathname.match(/^\/api\/lineups\/(.+)$/);
  if (lineupMatch) {
    const id = decodeURIComponent(lineupMatch[1]);
    const lineups = readJson(recommendedLineupsPath, []);
    const index = lineups.findIndex((item) => item.id === id);
    if (index === -1) {
      send(response, 404, "阵容不存在");
      return;
    }
    if (request.method === "PUT") {
      const body = JSON.parse(await readBody(request) || "{}");
      backupOverrides(recommendedLineupsPath, "recommended-lineups");
      lineups[index] = cleanRecommendedLineup(body, id);
      writeJson(recommendedLineupsPath, lineups);
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }
    if (request.method === "DELETE") {
      backupOverrides(recommendedLineupsPath, "recommended-lineups");
      writeJson(recommendedLineupsPath, lineups.filter((item) => item.id !== id));
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }
    send(response, 405, "Method not allowed");
    return;
  }

  if (url.pathname === "/api/videos/parse" && request.method === "POST") {
    const body = JSON.parse(await readBody(request) || "{}");
    const parsed = await parseVideoLink(body.url);
    send(response, 200, JSON.stringify(parsed), "application/json; charset=utf-8");
    return;
  }

  if (url.pathname === "/api/videos" && request.method === "POST") {
    const body = JSON.parse(await readBody(request) || "{}");
    const videos = readJson(videoGuidesPath, []);
    const guide = cleanVideoGuide(body, String(body.id || "").trim() || `${body.platform || "video"}-${Date.now()}`);
    if (!guide.url) {
      send(response, 400, "视频链接不能为空");
      return;
    }
    if (videos.some((video) => video.id === guide.id || video.url === guide.url)) {
      send(response, 409, "该视频已经存在");
      return;
    }
    backupOverrides(videoGuidesPath, "video-guides");
    videos.push(guide);
    writeJson(videoGuidesPath, videos);
    rebuildPreparedData();
    send(response, 201, JSON.stringify({ ok: true, id: guide.id }), "application/json; charset=utf-8");
    return;
  }

  const videoMatch = url.pathname.match(/^\/api\/videos\/(.+)$/);
  if (videoMatch) {
    const id = decodeURIComponent(videoMatch[1]);
    const videos = readJson(videoGuidesPath, []);
    const index = videos.findIndex((video) => video.id === id);
    if (index === -1) {
      send(response, 404, "Video not found");
      return;
    }
    if (request.method === "PUT") {
      const body = JSON.parse(await readBody(request) || "{}");
      const guide = cleanVideoGuide(body, id);
      if (!guide.url) {
        send(response, 400, "视频链接不能为空");
        return;
      }
      backupOverrides(videoGuidesPath, "video-guides");
      videos[index] = guide;
      writeJson(videoGuidesPath, videos);
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }
    if (request.method === "DELETE") {
      backupOverrides(videoGuidesPath, "video-guides");
      writeJson(videoGuidesPath, videos.filter((video) => video.id !== id));
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }
    send(response, 405, "Method not allowed");
    return;
  }

  const duplicateMatch = url.pathname.match(/^\/api\/cards\/(.+)\/duplicate$/);
  if (duplicateMatch && request.method === "POST") {
    const sourceId = decodeURIComponent(duplicateMatch[1]);
    const cards = readJson(cardsPath, []);
    const source = cards.find((card) => card.id === sourceId);
    if (!source || source.category !== "consume") {
      send(response, 400, "Only consume cards can be duplicated");
      return;
    }

    const body = await readBody(request);
    const requested = body ? JSON.parse(body) : {};
    const stamp = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const id = `consume-custom-${stamp}`;
    const resource = `Custom_Consume_${stamp}`;
    const customCards = readJson(customCardsPath, []);
    const overrides = readJson(overridesPath, {});
    const baseSourceId = source.raw?.custom_card?.sourceId || sourceId;

    customCards.push({
      id,
      sourceId: baseSourceId,
      resource,
      category: "consume",
      name: `${String(requested.name || source.name).trim() || source.name}（复制）`,
      createdAt: new Date().toISOString(),
    });
    overrides[id] = {
      id,
      resource,
      category: "consume",
      name: `${String(requested.name || source.name).trim() || source.name}（复制）`,
      quality: String(requested.quality || source.quality || "").trim(),
      factions: [],
      keywords: cleanStringList(requested.keywords ?? source.keywords),
      descriptions: cleanStringList(requested.descriptions ?? source.descriptions),
      hidden: Boolean(requested.hidden),
    };

    backupOverrides(customCardsPath, "custom-cards");
    backupOverrides();
    writeJson(customCardsPath, customCards);
    writeJson(overridesPath, overrides);
    rebuildPreparedData();
    send(response, 201, JSON.stringify({ ok: true, id }), "application/json; charset=utf-8");
    return;
  }

  const customCardMatch = url.pathname.match(/^\/api\/custom-cards\/(.+)$/);
  if (customCardMatch && request.method === "DELETE") {
    const id = decodeURIComponent(customCardMatch[1]);
    const customCards = readJson(customCardsPath, []);
    const customCard = customCards.find((card) => card.id === id);
    if (!customCard) {
      send(response, 404, "Custom card not found");
      return;
    }
    const overrides = readJson(overridesPath, {});
    backupOverrides(customCardsPath, "custom-cards");
    backupOverrides();
    writeJson(
      customCardsPath,
      customCards
        .filter((card) => card.id !== id)
        .map((card) => card.sourceId === id ? { ...card, sourceId: customCard.sourceId } : card),
    );
    delete overrides[id];
    writeJson(overridesPath, overrides);
    rebuildPreparedData();
    send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
    return;
  }

  const factionMatch = url.pathname.match(/^\/api\/factions\/(.+)\/override$/);
  if (factionMatch) {
    const id = decodeURIComponent(factionMatch[1]);
    const overrides = readJson(factionOverridesPath, {});

    if (request.method === "PUT") {
      const body = await readBody(request);
      const override = JSON.parse(body);
      overrides[id] = {
        baseName: id,
        name: String(override.name || "").trim(),
        keywordCategory: String(override.keywordCategory || "").trim(),
        description: String(override.description || "").trim(),
        stageEffects: cleanStringList(override.stageEffects),
        hidden: Boolean(override.hidden),
      };
      backupOverrides(factionOverridesPath, "faction-overrides");
      writeJson(factionOverridesPath, overrides);
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }

    if (request.method === "DELETE") {
      delete overrides[id];
      backupOverrides(factionOverridesPath, "faction-overrides");
      writeJson(factionOverridesPath, overrides);
      rebuildPreparedData();
      send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
      return;
    }

    send(response, 405, "Method not allowed");
    return;
  }

  const match = url.pathname.match(/^\/api\/cards\/(.+)\/override$/);
  if (!match) {
    send(response, 404, "Unknown API");
    return;
  }

  const id = decodeURIComponent(match[1]);
  const overrides = readJson(overridesPath, {});

  if (request.method === "PUT") {
    const body = await readBody(request);
    const override = JSON.parse(body);
    overrides[id] = {
      id,
      resource: String(override.resource || ""),
      category: String(override.category || ""),
      name: String(override.name || "").trim(),
      quality: String(override.quality || "").trim(),
      factions: cleanStringList(override.factions),
      keywords: cleanStringList(override.keywords),
      descriptions: cleanStringList(override.descriptions),
      hidden: Boolean(override.hidden),
    };
    backupOverrides();
    writeJson(overridesPath, overrides);
    rebuildPreparedData();
    send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
    return;
  }

  if (request.method === "DELETE") {
    delete overrides[id];
    backupOverrides();
    writeJson(overridesPath, overrides);
    rebuildPreparedData();
    send(response, 200, JSON.stringify({ ok: true }), "application/json; charset=utf-8");
    return;
  }

  send(response, 405, "Method not allowed");
}

createServer((request, response) => {
  const url = new URL(request.url || "/", `http://${request.headers.host || "127.0.0.1"}`);
  handleRequest(request, response, url).catch((error) => {
    send(response, 500, error.stack || error.message);
  });
}).listen(port, "127.0.0.1", () => {
  console.log(`CFUU local admin: http://127.0.0.1:${port}/admin/`);
});

async function handleRequest(request, response, url) {
  if (url.pathname.startsWith("/api/")) {
    if (!requireAdminAuth(request, response)) return;
    await handleApi(request, response, url);
    return;
  }
  if (url.pathname === "/" || url.pathname === "/admin") {
    if (!requireAdminAuth(request, response)) return;
    response.writeHead(302, { location: "/admin/", "x-robots-tag": adminNoIndexHeaders["x-robots-tag"] });
    response.end();
    return;
  }
  if (url.pathname === "/admin/") {
    if (!requireAdminAuth(request, response)) return;
    serveFile(response, adminRoot, "index.html");
    return;
  }
  if (url.pathname.startsWith("/admin/")) {
    if (!requireAdminAuth(request, response)) return;
    serveFile(response, adminRoot, url.pathname.replace(/^\/admin\//, ""));
    return;
  }
  serveFile(response, publicRoot, url.pathname);
}
