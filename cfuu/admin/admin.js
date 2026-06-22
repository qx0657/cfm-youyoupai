const requestedMode = new URLSearchParams(window.location.search).get("mode");
const state = {
  mode: ["cards", "factions", "videos", "lineups"].includes(requestedMode) ? requestedMode : "cards",
  cards: [],
  factions: [],
  videos: [],
  lineups: [],
  maps: [],
  overrides: {},
  factionOverrides: {},
  selectedId: null,
  // Strategy chips for current lineup being edited
  strategyChips: [],
  lineupSlots: Array.from({ length: 6 }, () => ({})),
  lineupPicker: null,
  lineupDraggedSlotIndex: null,
  // Debounce timer for live preview
  previewTimer: null,
};

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

const elements = {
  cardList: $("cardList"),
  resultCount: $("resultCount"),
  pageTitle: $("pageTitle"),
  pageDesc: $("pageDesc"),
  searchInput: $("searchInput"),
  categoryFilter: $("categoryFilter"),
  qualityFilter: $("qualityFilter"),
  hiddenFilter: $("hiddenFilter"),
  filterRow: $("filterRow"),
  reloadButton: $("reloadButton"),
  addVideoButton: $("addVideoButton"),
  addLineupButton: $("addLineupButton"),
  emptyState: $("emptyState"),
  editorForm: $("editorForm"),
  editorTitle: $("editorTitle"),
  cardMeta: $("cardMeta"),
  resourceText: $("resourceText"),
  cardImage: $("cardImage"),
  qualityBadge: $("qualityBadge"),
  hiddenInput: $("hiddenInput"),
  hiddenLabel: $("hiddenLabel"),
  nameInput: $("nameInput"),
  qualityField: $("qualityField"),
  qualityInput: $("qualityInput"),
  keywordCategoryField: $("keywordCategoryField"),
  keywordCategoryInput: $("keywordCategoryInput"),
  factionsField: $("factionsField"),
  factionsPicker: $("factionsPicker"),
  factionsToggle: $("factionsToggle"),
  factionsMenu: $("factionsMenu"),
  keywordsLabel: $("keywordsLabel"),
  descriptionsLabel: $("descriptionsLabel"),
  descriptionsHint: $("descriptionsHint"),
  keywordsInput: $("keywordsInput"),
  descriptionsInput: $("descriptionsInput"),
  saveButton: $("saveButton"),
  deleteButton: $("deleteButton"),
  duplicateButton: $("duplicateButton"),
  resetButton: $("resetButton"),
  saveStatus: $("saveStatus"),
  videoEditorForm: $("videoEditorForm"),
  videoEditorTitle: $("videoEditorTitle"),
  videoEditorMeta: $("videoEditorMeta"),
  videoIdText: $("videoIdText"),
  videoUrlInput: $("videoUrlInput"),
  parseVideoButton: $("parseVideoButton"),
  deleteVideoButton: $("deleteVideoButton"),
  saveVideoButton: $("saveVideoButton"),
  videoCoverPreview: $("videoCoverPreview"),
  videoPlatformBadge: $("videoPlatformBadge"),
  videoHiddenInput: $("videoHiddenInput"),
  videoPlatformInput: $("videoPlatformInput"),
  videoOrderInput: $("videoOrderInput"),
  videoTitleInput: $("videoTitleInput"),
  videoAuthorInput: $("videoAuthorInput"),
  videoCategoryInput: $("videoCategoryInput"),
  videoPublishedAtInput: $("videoPublishedAtInput"),
  videoDurationInput: $("videoDurationInput"),
  videoPopularityInput: $("videoPopularityInput"),
  videoPopularityLabelInput: $("videoPopularityLabelInput"),
  videoCoverInput: $("videoCoverInput"),
  videoSaveStatus: $("videoSaveStatus"),
  lineupEditorForm: $("lineupEditorForm"),
  lineupEditorTitle: $("lineupEditorTitle"),
  lineupIdText: $("lineupIdText"),
  lineupNameInput: $("lineupNameInput"),
  lineupLabelInput: $("lineupLabelInput"),
  lineupOrderInput: $("lineupOrderInput"),
  lineupHiddenInput: $("lineupHiddenInput"),
  lineupSummaryInput: $("lineupSummaryInput"),
  lineupKeywordsInput: $("lineupKeywordsInput"),
  lineupStrategyAddInput: $("lineupStrategyAddInput"),
  lineupStrategyAddButton: $("lineupStrategyAddButton"),
  lineupStrategyChips: $("lineupStrategyChips"),
  lineupSlotsEditor: $("lineupSlotsEditor"),
  lineupPreviewBoard: $("lineupPreviewBoard"),
  lineupMapInput: $("lineupMapInput"),
  lineupBuff1Input: $("lineupBuff1Input"),
  lineupBuff2Input: $("lineupBuff2Input"),
  lineupVideosEditor: $("lineupVideosEditor"),
  addLineupVideoButton: $("addLineupVideoButton"),
  saveLineupButton: $("saveLineupButton"),
  deleteLineupButton: $("deleteLineupButton"),
  duplicateLineupButton: $("duplicateLineupButton"),
  lineupSaveStatus: $("lineupSaveStatus"),
  sidebarLinks: $$(".sidebar-link"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function listToText(value) {
  return Array.isArray(value) ? value.join("\n") : "";
}

function textToList(value) {
  return value
    .split(/\r?\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function searchable(card) {
  return [card.name, card.resource, card.categoryLabel, card.quality, ...(card.factions || []), ...(card.keywords || []), ...(card.descriptions || [])]
    .join(" ")
    .toLowerCase();
}

const qualityOrder = ["grey", "gray", "green", "blue", "purple", "gold", "red"];

function qualityRank(card) {
  const index = qualityOrder.indexOf(card.quality || "");
  return index === -1 ? -1 : index;
}

function compareCards(a, b) {
  const hiddenDelta = Number(Boolean(a.hidden)) - Number(Boolean(b.hidden));
  if (hiddenDelta !== 0) return hiddenDelta;
  const qualityDelta = qualityRank(b) - qualityRank(a);
  if (qualityDelta !== 0) return qualityDelta;
  return a.categoryLabel.localeCompare(b.categoryLabel, "zh-Hans-CN") || a.name.localeCompare(b.name, "zh-Hans-CN") || a.id.localeCompare(b.id);
}

function filteredCards() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const category = elements.categoryFilter.value;
  const quality = elements.qualityFilter.value;
  const hidden = elements.hiddenFilter.value;
  return state.cards
    .filter((card) => {
      if (category !== "all" && card.category !== category) return false;
      if (quality !== "all" && card.quality !== quality && !(quality === "grey" && card.quality === "gray")) return false;
      if (hidden === "visible" && card.hidden) return false;
      if (hidden === "hidden" && !card.hidden) return false;
      if (query && !searchable(card).includes(query)) return false;
      return true;
    })
    .sort(compareCards);
}

function searchableFaction(faction) {
  return [faction.name, faction.baseName, faction.keywordCategory, faction.description, ...(faction.stageEffects || []), ...(faction.roles || []).map((role) => role.name || "")]
    .join(" ")
    .toLowerCase();
}

function filteredFactions() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const hidden = elements.hiddenFilter.value;
  return state.factions
    .filter((faction) => {
      if (hidden === "visible" && faction.hidden) return false;
      if (hidden === "hidden" && !faction.hidden) return false;
      if (query && !searchableFaction(faction).includes(query)) return false;
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name, "zh-Hans-CN") || a.baseName.localeCompare(b.baseName));
}

function filteredVideos() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const hidden = elements.hiddenFilter.value;
  return state.videos
    .filter((video) => {
      if (hidden === "visible" && video.hidden) return false;
      if (hidden === "hidden" && !video.hidden) return false;
      if (query && ![video.title, video.author, video.category, video.url, video.platform].join(" ").toLowerCase().includes(query)) return false;
      return true;
    })
    .sort((a, b) => Number(a.hidden) - Number(b.hidden) || (a.order || 0) - (b.order || 0) || a.title.localeCompare(b.title, "zh-Hans-CN"));
}

function filteredLineups() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const hidden = elements.hiddenFilter.value;
  return state.lineups
    .filter((lineup) => {
      if (hidden === "visible" && lineup.hidden) return false;
      if (hidden === "hidden" && !lineup.hidden) return false;
      if (query && ![lineup.name, lineup.label, lineup.summary, ...(lineup.keywords || [])].join(" ").toLowerCase().includes(query)) return false;
      return true;
    })
    .sort((a, b) => Number(a.hidden) - Number(b.hidden) || (a.order || 0) - (b.order || 0) || a.name.localeCompare(b.name, "zh-Hans-CN"));
}

function qualityClass(value) {
  return value === "gray" ? "grey" : value || "";
}

function qualityLabel(value) {
  return {
    grey: "灰",
    gray: "灰",
    green: "绿",
    blue: "蓝",
    purple: "紫",
    gold: "金",
    red: "红",
  }[value] || value;
}

function cardTags(card) {
  return [...(card.factions || []), ...(card.keywords || [])].slice(0, 4);
}

function allFactions() {
  const fromFactionData = state.factions.map((faction) => faction.name).filter(Boolean);
  if (fromFactionData.length) {
    return Array.from(new Set(fromFactionData)).sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
  }
  const fallbackFromCards = state.cards.filter((card) => card.category === "role").flatMap((card) => card.factions || []);
  return Array.from(new Set(fallbackFromCards))
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
}

function renderFactionOptions(selected = []) {
  const selectedSet = new Set(selected);
  const factions = allFactions();
  elements.factionsMenu.innerHTML = factions
    .map(
      (faction) => `
        <label class="multi-select-option">
          <input type="checkbox" value="${faction}" ${selectedSet.has(faction) ? "checked" : ""} />
          <span>${faction}</span>
        </label>
      `,
    )
    .join("");
  updateFactionToggle();
}

function selectedFactions() {
  return Array.from(elements.factionsMenu.querySelectorAll("input:checked")).map((input) => input.value);
}

function updateFactionToggle() {
  const selected = selectedFactions();
  elements.factionsToggle.textContent = selected.length ? selected.join("、") : "选择阵营";
  elements.factionsToggle.title = selected.join("、");
}

// ── Page titles ──

const pageTitles = {
  cards: { title: "卡牌管理", desc: "快速定位卡牌或阵营，编辑名称、隐藏状态、词条和描述。" },
  factions: { title: "阵营管理", desc: "编辑阵营名称、关键词分类、阶段效果和隐藏状态。" },
  videos: { title: "视频攻略", desc: "管理抖音和快手视频攻略，粘贴链接即可自动解析。" },
  lineups: { title: "推荐阵容", desc: "管理推荐阵容策略，支持实时预览和拖拽排序。" },
};

// ── Sidebar navigation ──

function setActiveSidebar(page) {
  elements.sidebarLinks.forEach((link) => {
    link.classList.toggle("active", link.dataset.page === page);
  });
}

function setPageHeader(page) {
  const info = pageTitles[page];
  if (info) {
    elements.pageTitle.textContent = info.title;
    elements.pageDesc.textContent = info.desc;
  }
}

function syncModeControls(isLineup) {
  elements.categoryFilter.disabled = isLineup;
  elements.qualityFilter.disabled = isLineup;
  elements.addVideoButton.classList.toggle("hidden", state.mode !== "videos");
  elements.addLineupButton.classList.toggle("hidden", state.mode !== "lineups");
}

// ── Rendering ──

function renderList() {
  if (state.mode === "lineups") {
    renderLineupList();
    return;
  }
  if (state.mode === "videos") {
    renderVideoList();
    return;
  }
  if (state.mode === "factions") {
    renderFactionList();
    return;
  }
  const cards = filteredCards();
  elements.resultCount.textContent = `${cards.length} / ${state.cards.length} 张卡牌`;
  elements.cardList.innerHTML = "";
  for (const card of cards) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = ["card-row", card.id === state.selectedId ? "active" : "", card.hidden ? "hidden-card" : ""].filter(Boolean).join(" ");
    row.innerHTML = `
      <img class="card-thumb" src="${card.image || card.avatar || ""}" alt="" loading="lazy" />
      <span class="card-info">
        <span class="card-title-row">
          <strong>${card.name}${card.hidden ? "（隐藏）" : ""}</strong>
          <span class="quality-pill ${qualityClass(card.quality)}">${qualityLabel(card.quality) || "无"}</span>
        </span>
        <small class="card-meta">${card.categoryLabel}</small>
        <small class="card-resource">${card.resource}</small>
        <span class="card-tags">
          ${cardTags(card)
            .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
            .join("")}
        </span>
      </span>
    `;
    row.addEventListener("click", () => selectCard(card.id));
    elements.cardList.appendChild(row);
  }
}

function renderLineupList() {
  const lineups = filteredLineups();
  elements.resultCount.textContent = `${lineups.length} / ${state.lineups.length} 套阵容`;
  elements.cardList.innerHTML = "";
  for (const lineup of lineups) {
    const slots = lineup.slots || [];
    const thumbs = Array.from({ length: 6 }, (_, index) => {
      const slot = slots[index] || {};
      if (!slot.role) return '<span class="thumb-avatar empty" title="空位"></span>';
      const card = state.cards.find((c) => c.name === slot.role);
      if (!card) return `<span class="thumb-avatar missing" title="资料缺失：${escapeHtml(slot.role)}"></span>`;
      return `<img class="thumb-avatar" src="${card.avatar || card.image || ""}" alt="${escapeHtml(slot.role)}" title="${escapeHtml(index < 3 ? "前排" : "后排")} ${(index % 3) + 1} · ${escapeHtml(slot.role)}" loading="lazy" />`;
    }).join("");

    const row = document.createElement("div");
    row.className = ["card-row", "lineup-row", lineup.id === state.selectedId ? "active" : "", lineup.hidden ? "hidden-card" : ""].filter(Boolean).join(" ");
    row.setAttribute("draggable", "true");
    row.dataset.lineupId = lineup.id;
    row.innerHTML = `
      <span class="drag-handle" title="拖拽排序">⠿</span>
      <span class="card-thumb lineup-preview-thumb">${thumbs}</span>
      <span class="card-info">
        <span class="card-title-row">
          <strong>${escapeHtml(lineup.name)}${lineup.hidden ? "（隐藏）" : ""}</strong>
          <span class="quality-pill">${escapeHtml(lineup.label)}</span>
        </span>
        <span class="card-tags">${(lineup.keywords || []).slice(0, 4).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</span>
      </span>`;

    row.addEventListener("click", (e) => {
      if (e.target.closest(".drag-handle")) return;
      selectLineup(lineup.id);
    });

    // Drag-sort handlers
    row.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", lineup.id);
      e.dataTransfer.effectAllowed = "move";
      row.classList.add("dragging");
    });
    row.addEventListener("dragend", () => {
      row.classList.remove("dragging");
      $$(".card-row").forEach((r) => { r.classList.remove("drag-over-top", "drag-over-bottom"); });
    });
    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      const rect = row.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      row.classList.toggle("drag-over-top", e.clientY < midY);
      row.classList.toggle("drag-over-bottom", e.clientY >= midY);
    });
    row.addEventListener("dragleave", () => {
      row.classList.remove("drag-over-top", "drag-over-bottom");
    });
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over-top", "drag-over-bottom");
      const draggedId = e.dataTransfer.getData("text/plain");
      if (draggedId === lineup.id) return;
      reorderLineup(draggedId, lineup.id);
    });

    elements.cardList.appendChild(row);
  }
}

async function reorderLineup(draggedId, targetId) {
  const lineups = state.lineups;
  const draggedIdx = lineups.findIndex((l) => l.id === draggedId);
  const targetIdx = lineups.findIndex((l) => l.id === targetId);
  if (draggedIdx === -1 || targetIdx === -1) return;
  const [moved] = lineups.splice(draggedIdx, 1);
  lineups.splice(targetIdx, 0, moved);
  // Recalculate orders
  for (let i = 0; i < lineups.length; i++) {
    lineups[i].order = i;
  }
  await saveLineupsToApi(lineups);
  state.lineups = lineups;
  renderLineupList();
}

function renderVideoList() {
  const videos = filteredVideos();
  elements.resultCount.textContent = `${videos.length} / ${state.videos.length} 个视频`;
  elements.cardList.innerHTML = "";
  for (const video of videos) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = ["card-row", video.id === state.selectedId ? "active" : "", video.hidden ? "hidden-card" : ""].filter(Boolean).join(" ");
    row.innerHTML = `
      ${video.cover
        ? `<img class="card-thumb video-thumb" src="${escapeHtml(video.cover)}" alt="" loading="lazy" />`
        : `<span class="card-thumb image-frame">无封面</span>`}
      <span class="card-info">
        <span class="card-title-row">
          <strong>${escapeHtml(video.title)}${video.hidden ? "（隐藏）" : ""}</strong>
          <span class="quality-pill">${video.platform === "kuaishou" ? "快手" : "抖音"}</span>
        </span>
        <small class="card-meta">${escapeHtml(video.author)} · ${escapeHtml(video.category)}</small>
        <small class="card-resource">顺序 ${Number(video.order) || 0}</small>
      </span>
    `;
    row.addEventListener("click", () => selectVideo(video.id));
    elements.cardList.appendChild(row);
  }
}

function renderFactionList() {
  const factions = filteredFactions();
  elements.resultCount.textContent = `${factions.length} / ${state.factions.length} 个阵营`;
  elements.cardList.innerHTML = "";
  for (const faction of factions) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = ["card-row", faction.baseName === state.selectedId ? "active" : "", faction.hidden ? "hidden-card" : ""].filter(Boolean).join(" ");
    row.innerHTML = `
      <img class="card-thumb" src="${faction.icon || ""}" alt="" loading="lazy" />
      <span class="card-info">
        <span class="card-title-row">
          <strong>${faction.name}${faction.hidden ? "（隐藏）" : ""}</strong>
          <span class="quality-pill">${faction.keywordCategory || "无"}</span>
        </span>
        <small class="card-meta">阵营 · ${faction.roles?.filter((role) => role.name).length || 0}/${faction.roles?.length || 0} 角色</small>
        <small class="card-resource">${faction.baseName}</small>
        <span class="card-tags">
          ${(faction.stageEffects || [])
            .slice(0, 3)
            .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
            .join("")}
        </span>
      </span>
    `;
    row.addEventListener("click", () => selectFaction(faction.baseName));
    elements.cardList.appendChild(row);
  }
}

// ── Selection / Editor forms ──

function selectedCard() {
  return state.cards.find((card) => card.id === state.selectedId) || null;
}

function selectedFaction() {
  return state.factions.find((faction) => faction.baseName === state.selectedId) || null;
}

function selectedVideo() {
  return state.videos.find((video) => video.id === state.selectedId) || null;
}

function selectedLineup() {
  return state.lineups.find((lineup) => lineup.id === state.selectedId) || null;
}

function setQualityValue(value) {
  const normalized = value || "";
  const exists = Array.from(elements.qualityInput.options).some((option) => option.value === normalized);
  if (!exists && normalized) {
    const option = document.createElement("option");
    option.value = normalized;
    option.textContent = `当前值：${normalized}`;
    elements.qualityInput.appendChild(option);
  }
  elements.qualityInput.value = normalized;
  updateQualityBadge(normalized);
}

function updateQualityBadge(value) {
  const normalized = value || "";
  elements.qualityBadge.className = "quality-badge";
  if (!normalized) {
    elements.qualityBadge.classList.add("hidden");
    elements.qualityBadge.textContent = "";
    return;
  }
  elements.qualityBadge.classList.add(normalized === "gray" ? "grey" : normalized);
  elements.qualityBadge.textContent = qualityLabel(normalized);
}

function setEditorMode(mode) {
  const isFaction = mode === "factions";
  elements.qualityField.classList.toggle("hidden", isFaction);
  elements.keywordCategoryField.classList.toggle("hidden", !isFaction);
  elements.factionsField.classList.toggle("hidden", isFaction);
  elements.hiddenLabel.textContent = isFaction ? "隐藏这个阵营" : "隐藏这张卡牌";
  elements.keywordsLabel.textContent = isFaction ? "阶段效果" : "词条";
  elements.descriptionsLabel.textContent = isFaction ? "阵营描述" : "描述";
  elements.descriptionsInput.placeholder = isFaction ? "填写阵营描述" : "每行一条描述";
  elements.descriptionsHint.textContent = isFaction ? "用于前台阵营详情页的正文说明。" : "每行一条描述。角色和武器通常第 1 行为基础描述，第 2 行为升级描述。";
  elements.qualityBadge.classList.toggle("hidden", isFaction);
}

function updateDescriptionHelp(card) {
  if (!card) return;
  const isBaseUpgradeCard = card.category === "role" || card.category === "weapon";
  elements.descriptionsLabel.textContent = isBaseUpgradeCard ? "描述（基础 / 升级）" : "描述";
  elements.descriptionsInput.placeholder = isBaseUpgradeCard
    ? "第 1 行：基础描述\n第 2 行：升级描述"
    : "每行一条描述";
  elements.descriptionsHint.textContent = isBaseUpgradeCard
    ? "前台会把第 1 行显示为“基础”，第 2 行及之后显示为“升级”；请按游戏原文顺序录入。"
    : "每行一条描述。";
}

async function switchPage(page) {
  state.mode = page;
  state.selectedId = null;
  elements.searchInput.value = "";
  elements.hiddenFilter.value = "all";
  elements.categoryFilter.value = "all";
  elements.qualityFilter.value = "all";
  setActiveSidebar(page);
  setPageHeader(page);
  syncModeControls(page === "lineups");

  if (page === "factions" && !state.factions.length) {
    await loadData();
    return;
  }
  if (page === "videos" && !state.videos.length) {
    renderList();
    startNewVideo();
    return;
  }
  if (page === "lineups" && !state.lineups.length) {
    renderList();
    startNewLineup();
    return;
  }
  if (page === "cards" && !state.cards.length) {
    await loadData();
    return;
  }

  state.selectedId = page === "factions"
    ? state.factions[0]?.baseName || null
    : page === "videos"
      ? state.videos[0]?.id || null
      : page === "lineups"
        ? filteredLineups()[0]?.id || null
        : state.cards[0]?.id || null;
  renderList();
  if (page === "factions") selectFaction(state.selectedId);
  else if (page === "videos") selectVideo(state.selectedId);
  else if (page === "lineups") selectLineup(state.selectedId);
  else selectCard(state.selectedId);
}

function selectCard(id) {
  state.mode = "cards";
  state.selectedId = id;
  syncModeControls(false);
  const card = selectedCard();
  setEditorMode("cards");
  elements.videoEditorForm.classList.add("hidden");
  elements.lineupEditorForm.classList.add("hidden");
  renderList();
  if (!card) {
    elements.emptyState.classList.remove("hidden");
    elements.editorForm.classList.add("hidden");
    return;
  }
  elements.emptyState.classList.add("hidden");
  elements.editorForm.classList.remove("hidden");
  elements.editorTitle.textContent = card.name;
  elements.cardMeta.textContent = `${card.categoryLabel} · ${card.matchStatus}`;
  elements.resourceText.textContent = card.resource;
  elements.cardImage.src = card.image || card.avatar || "";
  elements.cardImage.alt = card.name;
  elements.hiddenInput.checked = Boolean(card.hidden);
  elements.nameInput.value = card.name || "";
  setQualityValue(card.quality);
  renderFactionOptions(card.factions || []);
  elements.factionsPicker.classList.toggle("disabled", card.category !== "role");
  elements.factionsToggle.disabled = card.category !== "role";
  elements.keywordsInput.value = listToText(card.keywords);
  elements.descriptionsInput.value = listToText(card.descriptions);
  updateDescriptionHelp(card);
  elements.deleteButton.classList.toggle("hidden", !card.raw?.custom_card);
  elements.duplicateButton.classList.toggle("hidden", card.category !== "consume");
  elements.saveStatus.textContent = "";
}

function selectFaction(id) {
  state.mode = "factions";
  state.selectedId = id;
  syncModeControls(false);
  const faction = selectedFaction();
  setEditorMode("factions");
  elements.videoEditorForm.classList.add("hidden");
  elements.lineupEditorForm.classList.add("hidden");
  renderList();
  if (!faction) {
    elements.emptyState.classList.remove("hidden");
    elements.editorForm.classList.add("hidden");
    return;
  }
  elements.emptyState.classList.add("hidden");
  elements.editorForm.classList.remove("hidden");
  elements.editorTitle.textContent = faction.name;
  elements.cardMeta.textContent = `阵营 · ${faction.keywordCategory || "无分类"}`;
  elements.resourceText.textContent = faction.baseName;
  elements.cardImage.src = faction.icon || "";
  elements.cardImage.alt = faction.name;
  elements.hiddenInput.checked = Boolean(faction.hidden);
  elements.nameInput.value = faction.name || "";
  elements.keywordCategoryInput.value = faction.keywordCategory || "";
  elements.keywordsInput.value = listToText(faction.stageEffects);
  elements.descriptionsInput.value = faction.description || "";
  elements.deleteButton.classList.add("hidden");
  elements.duplicateButton.classList.add("hidden");
  elements.saveStatus.textContent = "";
}

function fillVideoForm(video, isNew = false) {
  elements.emptyState.classList.add("hidden");
  elements.editorForm.classList.add("hidden");
  elements.videoEditorForm.classList.remove("hidden");
  elements.lineupEditorForm.classList.add("hidden");
  elements.videoEditorTitle.textContent = isNew ? "添加视频" : video.title;
  elements.videoEditorMeta.textContent = isNew ? "粘贴链接后解析" : `${video.platform === "kuaishou" ? "快手" : "抖音"} · ${video.category}`;
  elements.videoIdText.textContent = video.id || "";
  elements.videoUrlInput.value = video.url || "";
  elements.videoHiddenInput.checked = Boolean(video.hidden);
  elements.videoPlatformInput.value = video.platform || "douyin";
  elements.videoOrderInput.value = String(video.order || 0);
  elements.videoTitleInput.value = video.title || "";
  elements.videoAuthorInput.value = video.author || "";
  elements.videoCategoryInput.value = video.category || "其他攻略";
  elements.videoPublishedAtInput.value = video.publishedAt || "";
  elements.videoDurationInput.value = video.duration || "";
  elements.videoPopularityInput.value = String(video.popularity || 0);
  elements.videoPopularityLabelInput.value = video.popularityLabel || "";
  elements.videoCoverInput.value = video.cover || "";
  elements.videoCoverPreview.src = video.cover || "";
  elements.videoCoverPreview.alt = video.title || "";
  elements.videoPlatformBadge.textContent = video.platform === "kuaishou" ? "快手" : "抖音";
  elements.deleteVideoButton.classList.toggle("hidden", isNew);
  elements.videoSaveStatus.textContent = "";
}

function selectVideo(id) {
  state.mode = "videos";
  state.selectedId = id;
  syncModeControls(false);
  renderList();
  const video = selectedVideo();
  if (!video) {
    startNewVideo();
    return;
  }
  fillVideoForm(video);
}

function startNewVideo() {
  state.mode = "videos";
  state.selectedId = null;
  syncModeControls(false);
  renderList();
  fillVideoForm({
    id: "",
    platform: "douyin",
    title: "",
    author: "",
    url: "",
    category: "其他攻略",
    duration: null,
    popularity: 0,
    popularityLabel: "",
    publishedAt: null,
    cover: null,
    order: state.videos.length,
    hidden: false,
  }, true);
  requestAnimationFrame(() => {
    elements.videoEditorForm.scrollIntoView({ block: "start" });
    elements.videoUrlInput.focus();
    elements.videoSaveStatus.textContent = '请粘贴抖音或快手链接，然后点击"解析链接"。';
  });
}

// ── Autocomplete component ──

function createAutocomplete(container, placeholder, cards, categoryFilter) {
  const wrapper = document.createElement("div");
  wrapper.className = "autocomplete-wrapper";

  const input = document.createElement("input");
  input.placeholder = placeholder;
  input.type = "text";

  const dropdown = document.createElement("div");
  dropdown.className = "autocomplete-dropdown";

  wrapper.append(input, dropdown);

  let selectedIndex = -1;

  function showOptions(options) {
    dropdown.innerHTML = "";
    selectedIndex = -1;
    if (options.length === 0) {
      dropdown.classList.remove("open");
      return;
    }
    for (const opt of options) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "autocomplete-option";
      btn.innerHTML = escapeHtml(opt.name) + (opt.quality ? `<span class="autocomplete-meta">· ${qualityLabel(opt.quality)}</span>` : "");
      btn.addEventListener("click", () => {
        input.value = opt.name;
        dropdown.classList.remove("open");
        container.value = opt.name;
      });
      dropdown.appendChild(btn);
    }
    dropdown.classList.add("open");
  }

  function updateFilter() {
    const q = input.value.trim().toLowerCase();
    const filtered = cards
      .filter((c) => c.category === categoryFilter && !c.hidden)
      .sort((a, b) => a.name.localeCompare(b.name, "zh-Hans-CN"))
      .filter((c) => !q || c.name.toLowerCase().includes(q));
    showOptions(filtered);
  }

  input.addEventListener("input", updateFilter);
  input.addEventListener("focus", () => {
    if (dropdown.children.length === 0) updateFilter();
    else dropdown.classList.add("open");
  });
  input.addEventListener("blur", () => {
    setTimeout(() => dropdown.classList.remove("open"), 150);
  });

  // Keyboard navigation
  input.addEventListener("keydown", (e) => {
    const opts = dropdown.querySelectorAll(".autocomplete-option");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, opts.length - 1);
      opts.forEach((o, i) => o.classList.toggle("selected", i === selectedIndex));
      if (opts[selectedIndex]) opts[selectedIndex].scrollIntoView({ block: "nearest" });
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      opts.forEach((o, i) => o.classList.toggle("selected", i === selectedIndex));
      if (opts[selectedIndex]) opts[selectedIndex].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      opts[selectedIndex].click();
    }
  });

  return { input, container, wrapper };
}

// ── Lineup editor ──

function renderLineupReferenceOptions() {
  elements.lineupMapInput.innerHTML = `<option value="">不指定地图</option>${state.maps.map((map) => `<option value="${escapeHtml(map.key)}">${escapeHtml(map.name)}</option>`).join("")}`;
  const buffs = state.cards
    .filter((card) => card.category === "buff" && !card.hidden)
    .sort((a, b) => a.name.localeCompare(b.name, "zh-Hans-CN"));
  const buffOptions = `<option value="">不指定增益</option>${buffs.map((card) => `<option value="${escapeHtml(`${card.name}|${card.quality || ""}`)}">${escapeHtml(card.name)} · ${qualityLabel(card.quality) || "未知"}</option>`).join("")}`;
  elements.lineupBuff1Input.innerHTML = buffOptions;
  elements.lineupBuff2Input.innerHTML = buffOptions;
}

function platformLabel(platform) {
  return {
    douyin: "抖音",
    kuaishou: "快手",
    bilibili: "B站",
    other: "其他",
  }[platform] || "其他";
}

function normalizeLineupVideos(videos = [], keepEmpty = false) {
  return Array.isArray(videos)
    ? videos.map((video) => ({
      platform: ["douyin", "kuaishou", "bilibili", "other"].includes(video?.platform) ? video.platform : "douyin",
      title: String(video?.title || "").trim(),
      url: String(video?.url || "").trim(),
    })).filter((video) => keepEmpty || video.url || video.title)
    : [];
}

function renderLineupVideos(videos = []) {
  const items = normalizeLineupVideos(videos, true);
  elements.lineupVideosEditor.innerHTML = items.length
    ? items.map((video, index) => renderLineupVideoRow(video, index)).join("")
    : `<p class="lineup-videos-empty">暂无视频链接</p>`;
}

function renderLineupVideoRow(video, index) {
  return `
    <article class="lineup-video-row" data-lineup-video-index="${index}">
      <label>
        <span>平台</span>
        <select class="lineup-video-platform">
          ${["douyin", "kuaishou", "bilibili", "other"].map((platform) => `<option value="${platform}" ${video.platform === platform ? "selected" : ""}>${platformLabel(platform)}</option>`).join("")}
        </select>
      </label>
      <label>
        <span>标题</span>
        <input class="lineup-video-title" value="${escapeHtml(video.title)}" placeholder="例如：遗言消灭流实战讲解" />
      </label>
      <label class="lineup-video-url-field">
        <span>链接</span>
        <input class="lineup-video-url" value="${escapeHtml(video.url)}" placeholder="粘贴视频链接" />
      </label>
      <button class="lineup-video-remove danger" type="button" data-lineup-video-remove="${index}" aria-label="删除视频链接">删除</button>
    </article>
  `;
}

function currentLineupVideos() {
  if (!elements.lineupVideosEditor) return [];
  return Array.from(elements.lineupVideosEditor.querySelectorAll(".lineup-video-row")).map((row) => ({
    platform: row.querySelector(".lineup-video-platform")?.value || "douyin",
    title: row.querySelector(".lineup-video-title")?.value.trim() || "",
    url: row.querySelector(".lineup-video-url")?.value.trim() || "",
  })).filter((video) => video.url || video.title);
}

function addLineupVideo() {
  const videos = currentLineupVideos();
  videos.push({ platform: "douyin", title: "", url: "" });
  renderLineupVideos(videos);
  const lastUrl = elements.lineupVideosEditor.querySelector(".lineup-video-row:last-child .lineup-video-url");
  lastUrl?.focus();
}

function bindLineupVideoEditor() {
  elements.addLineupVideoButton.onclick = addLineupVideo;
  elements.lineupVideosEditor.onclick = (event) => {
    const removeButton = event.target.closest("[data-lineup-video-remove]");
    if (!removeButton) return;
    const index = Number(removeButton.dataset.lineupVideoRemove);
    const videos = currentLineupVideos();
    videos.splice(index, 1);
    renderLineupVideos(videos);
  };
}

function normalizeLineupSlots(slots = []) {
  return Array.from({ length: 6 }, (_, index) => {
    const slot = slots[index] || {};
    return {
      role: slot.role || "",
      weapon: slot.weapon || "",
      items: Array.isArray(slot.items) ? slot.items.filter(Boolean) : [],
    };
  });
}

function visibleCardsByName() {
  return new Map(state.cards.filter((card) => !card.hidden).map((card) => [card.name, card]));
}

function cardArtwork(card, preferred = "image") {
  if (!card) return "";
  if (preferred === "role") return card.goldImage || card.image || card.avatar || "";
  return card.originalImage || card.image || card.avatar || card.goldImage || "";
}

function cardPopoverArtwork(card, preferred = "image") {
  if (!card) return "";
  if (preferred === "role") return card.goldImage || card.image || card.avatar || card.originalImage || "";
  return card.image || card.goldImage || card.avatar || card.originalImage || "";
}

function displayCardDescriptions(card) {
  const descriptions = (card?.descriptions || [])
    .map((description) => String(description || "").trim())
    .filter((description) => description && description !== "数据待补全");
  return descriptions.length ? descriptions : ["未知"];
}

function splitCardUpgradeDescriptions(card) {
  const descriptions = displayCardDescriptions(card);
  if (!card || !["role", "weapon"].includes(card.category) || descriptions.length < 2) {
    return { base: descriptions, upgraded: [] };
  }
  return { base: [descriptions[0]], upgraded: descriptions.slice(1) };
}

function cardEffectText(card) {
  if (!card) return "";
  return [
    card.name,
    ...(card.keywords || []),
    ...(card.descriptions || []),
    ...(card.plain_descriptions || []),
    ...(card.brief_descriptions || []),
  ].join(" ");
}

function lineupSlotStatus(slot, role, cardsByName) {
  const itemCards = (slot.items || []).map((name) => cardsByName.get(name)).filter(Boolean);
  const roleText = cardEffectText(role);
  const itemTexts = itemCards.map(cardEffectText);
  return {
    hasTaunt: roleText.includes("嘲讽") || itemTexts.some((text) => text.includes("嘲讽")),
    cannotAct: itemTexts.some((text) => text.includes("无法行动")),
  };
}

function renderLineupCardPopover(card, preferredImage = "image") {
  if (!card) return "";
  const image = cardPopoverArtwork(card, preferredImage);
  const descriptions = splitCardUpgradeDescriptions(card);
  const detailRows = [
    ...descriptions.base.map((description) => ({ label: descriptions.upgraded.length ? "基础" : "", kind: "base", description })),
    ...descriptions.upgraded.map((description) => ({ label: "升级", kind: "upgraded", description })),
  ];
  const tags = [...(card.factions || []), ...(card.keywords || [])].filter(Boolean).slice(0, 8);

  return `
    <div class="lineup-card-popover" role="tooltip">
      <div class="lineup-card-popover-image">
        ${image ? `<img src="${escapeHtml(image)}" alt="" loading="lazy" />` : `<b>${escapeHtml(card.name.slice(0, 1))}</b>`}
      </div>
      <div class="lineup-card-popover-body">
        <header>
          <span>${escapeHtml(card.categoryLabel || "卡牌")}${card.quality ? ` · ${escapeHtml(qualityLabel(card.quality))}` : ""}</span>
          <strong>${escapeHtml(card.name)}</strong>
        </header>
        ${tags.length ? `<div class="lineup-card-popover-tags">${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
        <div class="lineup-card-popover-effects">
          ${detailRows.map((row) => `
            <p class="${row.kind === "upgraded" ? "upgraded" : ""}">
              ${row.label ? `<small>${escapeHtml(row.label)}</small>` : ""}
              <span>${escapeHtml(row.description)}</span>
            </p>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}

function lineupSlotHasContent(slot = {}) {
  return Boolean(slot.role || slot.weapon || (slot.items || []).length);
}

function renderLineupSlots(slots = []) {
  state.lineupSlots = normalizeLineupSlots(slots);
  renderLineupSlotsDOM();
}

function renderLineupSlotsDOM() {
  const cardsByName = visibleCardsByName();
  elements.lineupSlotsEditor.innerHTML = `
    <div class="lineup-board-editor">
      <div class="lineup-editor-lane front">
        <span class="lineup-editor-row-label"><b>前排</b><small>承伤 · 启动</small></span>
        <div class="lineup-editor-row">
          ${state.lineupSlots.slice(0, 3).map((slot, index) => renderLineupSlotEditor(slot, index, cardsByName)).join("")}
        </div>
      </div>
      <div class="lineup-editor-lane back">
        <span class="lineup-editor-row-label"><b>后排</b><small>输出 · 辅助</small></span>
        <div class="lineup-editor-row">
          ${state.lineupSlots.slice(3, 6).map((slot, index) => renderLineupSlotEditor(slot, index + 3, cardsByName)).join("")}
        </div>
      </div>
    </div>
  `;
  elements.lineupSlotsEditor.onclick = handleLineupBoardClick;
  bindLineupSlotDragEvents();
  renderLineupPreview();
}

function renderLineupSlotEditor(slot, index, cardsByName) {
  const hasContent = lineupSlotHasContent(slot);
  const role = slot.role ? cardsByName.get(slot.role) : null;
  const roleImage = role ? cardArtwork(role, "role") : "";
  const status = lineupSlotStatus(slot, role, cardsByName);
  const statusIcons = [
    status.hasTaunt ? `<img class="lineup-editor-status-icon" src="/assets/effects/taunt.png" alt="嘲讽" title="嘲讽" loading="lazy" />` : "",
    status.cannotAct ? `<img class="lineup-editor-status-icon" src="/assets/effects/stop.png" alt="无法行动" title="无法行动" loading="lazy" />` : "",
  ].filter(Boolean);
  const statusIconMarkup = statusIcons.length
    ? `<span class="lineup-editor-status-icons ${statusIcons.length > 1 ? "multiple" : ""}">${statusIcons.join("")}</span>`
    : "";
  const slotLabel = `${index < 3 ? "前排" : "后排"} ${(index % 3) + 1}`;
  const roleContent = slot.role
    ? `
      <button class="lineup-editor-role-card" type="button" data-lineup-action="pick-role" data-slot-index="${index}">
        <span class="lineup-editor-card-image">
          <span class="lineup-editor-card-art">
            ${roleImage ? `<img src="${escapeHtml(roleImage)}" alt="" loading="lazy" />` : `<span class="lineup-editor-fallback">${escapeHtml(slot.role.slice(0, 1))}</span>`}
            ${statusIconMarkup}
          </span>
        </span>
        <strong>${escapeHtml(role?.name || slot.role)}</strong>
      </button>
      ${role ? renderLineupCardPopover(role, "role") : ""}
      <button class="lineup-slot-clear" type="button" data-lineup-action="clear-slot" data-slot-index="${index}" aria-label="清空${slotLabel}">×</button>
    `
    : `
      <button class="lineup-editor-add-role" type="button" data-lineup-action="pick-role" data-slot-index="${index}">
        <span>+</span><b>添加角色</b><small>${slotLabel}</small>
      </button>
    `;

  const equipment = [];
  if (slot.weapon) {
    const weapon = cardsByName.get(slot.weapon);
    equipment.push(renderEquipmentChip("weapon", slot.weapon, weapon, index, 0));
  }
  for (let i = 0; i < slot.items.length; i++) {
    const itemName = slot.items[i];
    equipment.push(renderEquipmentChip("item", itemName, cardsByName.get(itemName), index, i));
  }

  return `
    <article class="lineup-slot-editor ${hasContent ? "filled" : "empty"}" data-slot-index="${index}"${hasContent ? ` draggable="true" title="拖拽换位"` : ""}>
      <div class="lineup-editor-role-area">${roleContent}</div>
      <div class="lineup-editor-equipment">
        ${equipment.join("")}
        ${slot.weapon ? "" : `<button class="lineup-editor-equipment-add weapon" type="button" data-lineup-action="pick-weapon" data-slot-index="${index}" title="添加武器">+</button>`}
        <button class="lineup-editor-equipment-add" type="button" data-lineup-action="pick-item" data-slot-index="${index}" title="添加道具或投掷物">+</button>
      </div>
    </article>
  `;
}

function clearLineupSlotDragState() {
  state.lineupDraggedSlotIndex = null;
  elements.lineupSlotsEditor.classList.remove("lineup-slot-dragging");
  $$(".lineup-slot-editor").forEach((slot) => {
    slot.classList.remove("dragging", "drag-over");
  });
}

function bindLineupSlotDragEvents() {
  elements.lineupSlotsEditor.querySelectorAll(".lineup-slot-editor").forEach((slotElement) => {
    const toIndex = Number(slotElement.dataset.slotIndex);

    slotElement.addEventListener("dragstart", (event) => {
      if (!lineupSlotHasContent(state.lineupSlots[toIndex])) {
        event.preventDefault();
        return;
      }
      state.lineupDraggedSlotIndex = toIndex;
      event.dataTransfer.setData("application/x-cfuu-lineup-slot", String(toIndex));
      event.dataTransfer.setData("text/plain", `lineup-slot:${toIndex}`);
      event.dataTransfer.effectAllowed = "move";
      elements.lineupSlotsEditor.classList.add("lineup-slot-dragging");
      slotElement.classList.add("dragging");
    });

    slotElement.addEventListener("dragend", clearLineupSlotDragState);

    slotElement.addEventListener("dragover", (event) => {
      const fromIndex = state.lineupDraggedSlotIndex;
      if (!Number.isInteger(fromIndex) || fromIndex === toIndex) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      slotElement.classList.add("drag-over");
    });

    slotElement.addEventListener("dragleave", () => {
      slotElement.classList.remove("drag-over");
    });

    slotElement.addEventListener("drop", (event) => {
      const fromIndex = state.lineupDraggedSlotIndex;
      if (!Number.isInteger(fromIndex) || fromIndex === toIndex) return;
      event.preventDefault();
      [state.lineupSlots[fromIndex], state.lineupSlots[toIndex]] = [state.lineupSlots[toIndex], state.lineupSlots[fromIndex]];
      state.lineupSlots = normalizeLineupSlots(state.lineupSlots);
      clearLineupSlotDragState();
      renderLineupSlotsDOM();
      schedulePreviewUpdate();
    });
  });
}

function renderEquipmentChip(kind, name, card, slotIndex, itemIndex) {
  const image = cardArtwork(card);
  const action = kind === "weapon" ? "remove-weapon" : "remove-item";
  const meta = kind === "weapon" ? "武器" : card?.categoryLabel || "装备";
  const itemIndexAttr = kind === "item" ? ` data-item-index="${itemIndex}"` : "";
  return `
    <span class="lineup-editor-equipment-chip ${kind}" aria-label="${escapeHtml(meta)} · ${escapeHtml(card?.name || name)}">
      ${image ? `<img src="${escapeHtml(image)}" alt="" loading="lazy" />` : `<b>${escapeHtml(name.slice(0, 1))}</b>`}
      <button type="button" data-lineup-action="${action}" data-slot-index="${slotIndex}"${itemIndexAttr} aria-label="移除${escapeHtml(name)}">×</button>
      ${card ? renderLineupCardPopover(card) : ""}
    </span>
  `;
}

function handleLineupBoardClick(event) {
  const button = event.target.closest("[data-lineup-action]");
  if (!button) return;
  const slotIndex = Number(button.dataset.slotIndex);
  const action = button.dataset.lineupAction;
  const slot = state.lineupSlots[slotIndex];
  if (!slot) return;

  if (action === "pick-role") {
    openLineupCardPicker("role", slotIndex);
  } else if (action === "pick-weapon") {
    openLineupCardPicker("weapon", slotIndex);
  } else if (action === "pick-item") {
    openLineupCardPicker("item", slotIndex);
  } else if (action === "clear-slot") {
    state.lineupSlots[slotIndex] = { role: "", weapon: "", items: [] };
    renderLineupSlotsDOM();
    schedulePreviewUpdate();
  } else if (action === "remove-weapon") {
    slot.weapon = "";
    renderLineupSlotsDOM();
    schedulePreviewUpdate();
  } else if (action === "remove-item") {
    slot.items.splice(Number(button.dataset.itemIndex), 1);
    renderLineupSlotsDOM();
    schedulePreviewUpdate();
  }
}

function pickerCards(kind) {
  const categories = kind === "item" ? ["item", "throwable"] : [kind];
  return state.cards
    .filter((card) => categories.includes(card.category) && !card.hidden)
    .sort(compareCards);
}

// Build the filter dimensions (quality / faction / keyword) available in a picker pool.
function pickerFilterOptions(kind) {
  const cards = pickerCards(kind);
  const qualities = qualityOrder.filter((quality, index) => {
    if (qualityOrder.indexOf(quality) !== index && quality === "gray") return false;
    return cards.some((card) => (card.quality === quality) || (quality === "grey" && card.quality === "gray"));
  });
  const factions = Array.from(new Set(cards.flatMap((card) => card.factions || []).filter(Boolean)))
    .sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
  const keywords = Array.from(new Set(cards.flatMap((card) => card.keywords || []).filter(Boolean)))
    .sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
  return { qualities, factions, keywords };
}

function openLineupCardPicker(kind, slotIndex) {
  closeLineupCardPicker();
  const { qualities, factions, keywords } = pickerFilterOptions(kind);
  const filterSelect = (name, label, options, renderOption) =>
    options.length
      ? `<label class="lineup-picker-filter">
          <span>${label}</span>
          <select data-picker-filter="${name}">
            <option value="all">全部</option>
            ${options.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(renderOption ? renderOption(value) : value)}</option>`).join("")}
          </select>
        </label>`
      : "";
  const filtersHtml = [
    filterSelect("quality", "品质", qualities, (value) => qualityLabel(value)),
    filterSelect("faction", "阵营", factions),
    filterSelect("keyword", "标签", keywords),
  ].join("");
  const picker = document.createElement("div");
  picker.className = "lineup-card-picker";
  picker.setAttribute("role", "dialog");
  picker.setAttribute("aria-modal", "true");
  picker.innerHTML = `
    <div class="lineup-picker-panel${filtersHtml ? " has-filters" : ""}">
      <header>
        <div><span>${kind === "role" ? "选择角色" : kind === "weapon" ? "选择武器" : "选择装备"}</span><strong>${slotIndex < 3 ? "前排" : "后排"} ${(slotIndex % 3) + 1}</strong></div>
        <button class="lineup-picker-close" type="button" data-picker-close aria-label="关闭">×</button>
      </header>
      <input class="lineup-picker-search" placeholder="搜索名称、品质或标签" autocomplete="off" />
      ${filtersHtml ? `<div class="lineup-picker-filters">${filtersHtml}</div>` : ""}
      <div class="lineup-picker-results"></div>
    </div>
  `;
  document.body.appendChild(picker);
  state.lineupPicker = { kind, slotIndex, picker, filters: { quality: "all", faction: "all", keyword: "all" } };

  const searchInput = picker.querySelector(".lineup-picker-search");
  const render = () => renderLineupPickerResults(kind, slotIndex, searchInput.value);
  picker.addEventListener("click", (event) => {
    if (event.target === picker || event.target.closest("[data-picker-close]")) closeLineupCardPicker();
  });
  picker.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeLineupCardPicker();
  });
  searchInput.addEventListener("input", render);
  picker.querySelectorAll("[data-picker-filter]").forEach((select) => {
    select.addEventListener("change", () => {
      if (state.lineupPicker) state.lineupPicker.filters[select.dataset.pickerFilter] = select.value;
      render();
    });
  });
  render();
  searchInput.focus();
}

function closeLineupCardPicker() {
  if (!state.lineupPicker) return;
  state.lineupPicker.picker.remove();
  state.lineupPicker = null;
}

function renderLineupPickerResults(kind, slotIndex, query = "") {
  if (!state.lineupPicker) return;
  const results = state.lineupPicker.picker.querySelector(".lineup-picker-results");
  const q = query.trim().toLowerCase();
  const filters = state.lineupPicker.filters || {};
  const cards = pickerCards(kind)
    .filter((card) => {
      if (q && !searchable(card).includes(q)) return false;
      if (filters.quality && filters.quality !== "all") {
        const matchQuality = card.quality === filters.quality || (filters.quality === "grey" && card.quality === "gray");
        if (!matchQuality) return false;
      }
      if (filters.faction && filters.faction !== "all" && !(card.factions || []).includes(filters.faction)) return false;
      if (filters.keyword && filters.keyword !== "all" && !(card.keywords || []).includes(filters.keyword)) return false;
      return true;
    })
    .slice(0, 80);
  if (!cards.length) {
    results.innerHTML = `<p class="lineup-picker-empty">没有找到匹配卡牌</p>`;
    return;
  }
  results.innerHTML = cards.map((card) => {
    const image = cardPopoverArtwork(card, kind === "role" ? "role" : "image");
    const isSelected = kind === "role"
      ? state.lineupSlots[slotIndex].role === card.name
      : kind === "weapon"
        ? state.lineupSlots[slotIndex].weapon === card.name
        : state.lineupSlots[slotIndex].items.includes(card.name);
    return `
      <button class="lineup-picker-card ${isSelected ? "selected" : ""}" type="button" data-card-name="${escapeHtml(card.name)}">
        <span class="lineup-picker-image">${image ? `<img src="${escapeHtml(image)}" alt="" loading="lazy" />` : `<b>${escapeHtml(card.name.slice(0, 1))}</b>`}</span>
        <span><strong>${escapeHtml(card.name)}</strong><small>${escapeHtml(card.categoryLabel || "")}${card.quality ? ` · ${escapeHtml(qualityLabel(card.quality))}` : ""}</small></span>
      </button>
    `;
  }).join("");
  results.querySelectorAll(".lineup-picker-card").forEach((button) => {
    button.addEventListener("click", () => {
      applyLineupPickerChoice(kind, slotIndex, button.dataset.cardName);
    });
  });
}

function applyLineupPickerChoice(kind, slotIndex, name) {
  const slot = state.lineupSlots[slotIndex];
  if (!slot || !name) return;
  if (kind === "role") {
    slot.role = name;
  } else if (kind === "weapon") {
    slot.weapon = name;
  } else if (!slot.items.includes(name)) {
    slot.items.push(name);
  }
  closeLineupCardPicker();
  renderLineupSlotsDOM();
  schedulePreviewUpdate();
}

// ── Strategy chips ──

function renderStrategyChips(strategies = []) {
  state.strategyChips = strategies.map((item) => String(item || "").trim()).filter(Boolean);
  renderStrategyChipsDOM();
}

function renderStrategyChipsDOM(focusIndex = -1) {
  elements.lineupStrategyChips.innerHTML = "";
  for (let i = 0; i < state.strategyChips.length; i++) {
    const chip = document.createElement("span");
    chip.className = "chip-item strategy-chip-item";
    chip.dataset.index = i;

    const dragHandle = document.createElement("button");
    dragHandle.type = "button";
    dragHandle.className = "chip-drag-handle";
    dragHandle.draggable = true;
    dragHandle.title = "拖拽排序";
    dragHandle.setAttribute("aria-label", "拖拽排序");

    const input = document.createElement("input");
    input.className = "strategy-chip-edit";
    input.value = state.strategyChips[i];
    input.placeholder = "构筑要点";
    input.setAttribute("aria-label", `构筑要点 ${i + 1}`);

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "chip-remove";
    removeButton.textContent = "×";
    removeButton.setAttribute("aria-label", "删除构筑要点");

    input.addEventListener("input", () => {
      state.strategyChips[i] = input.value;
      schedulePreviewUpdate();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        input.blur();
      }
    });

    input.addEventListener("blur", () => {
      const trimmed = input.value.trim();
      if (!trimmed) {
        state.strategyChips.splice(i, 1);
        renderStrategyChipsDOM();
      } else {
        state.strategyChips[i] = trimmed;
        input.value = trimmed;
      }
      schedulePreviewUpdate();
    });

    removeButton.addEventListener("click", () => {
      state.strategyChips.splice(i, 1);
      renderStrategyChipsDOM();
      schedulePreviewUpdate();
    });

    // Drag events for reordering
    dragHandle.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      e.dataTransfer.effectAllowed = "move";
      chip.classList.add("dragging");
    });
    dragHandle.addEventListener("dragend", () => {
      chip.classList.remove("dragging");
      $$(".chip-item").forEach((c) => c.classList.remove("drag-over-top", "drag-over-bottom"));
    });
    chip.addEventListener("dragover", (e) => {
      e.preventDefault();
      const rect = chip.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      chip.classList.toggle("drag-over-top", e.clientY < midY);
      chip.classList.toggle("drag-over-bottom", e.clientY >= midY);
    });
    chip.addEventListener("dragleave", () => {
      chip.classList.remove("drag-over-top", "drag-over-bottom");
    });
    chip.addEventListener("drop", (e) => {
      e.preventDefault();
      chip.classList.remove("drag-over-top", "drag-over-bottom");
      const fromIdx = Number(e.dataTransfer.getData("text/plain"));
      if (fromIdx === i) return;
      const [moved] = state.strategyChips.splice(fromIdx, 1);
      state.strategyChips.splice(i, 0, moved);
      renderStrategyChipsDOM();
      schedulePreviewUpdate();
    });

    chip.append(dragHandle, input, removeButton);
    elements.lineupStrategyChips.appendChild(chip);
    if (i === focusIndex) {
      input.focus();
      input.select();
    }
  }
}

function addStrategyChip() {
  const val = elements.lineupStrategyAddInput.value.trim();
  if (!val) return;
  state.strategyChips.push(val);
  elements.lineupStrategyAddInput.value = "";
  renderStrategyChipsDOM(state.strategyChips.length - 1);
  schedulePreviewUpdate();
}

// ── Lineup preview ──

function schedulePreviewUpdate() {
  clearTimeout(state.previewTimer);
  state.previewTimer = setTimeout(renderLineupPreview, 200);
}

function renderLineupPreview() {
  if (!elements.lineupPreviewBoard) return;
  const name = elements.lineupNameInput.value.trim() || "未命名阵容";
  const mapKey = elements.lineupMapInput.value;
  const map = state.maps.find((m) => m.key === mapKey);
  const buff1Val = elements.lineupBuff1Input.value;
  const buff2Val = elements.lineupBuff2Input.value;
  const slots = normalizeLineupSlots(state.lineupSlots);

  // Parse buffs
  const buffs = [];
  if (buff1Val) {
    const [bn, bq] = buff1Val.split("|");
    if (bn) buffs.push({ name: bn.trim(), quality: bq || "gold" });
  }
  if (buff2Val) {
    const [bn, bq] = buff2Val.split("|");
    if (bn) buffs.push({ name: bn.trim(), quality: bq || "gold" });
  }

  const cardsByName = visibleCardsByName();

  let html = `<div class="lineup-preview-board">`;
  html += `<div class="lineup-preview-lane-label"><b>前排</b> · 承伤 · 启动</div>`;
  html += `<div class="lineup-preview-row">`;
  for (let i = 0; i < 3; i++) {
    const slot = slots[i] || {};
    html += renderPreviewSlot(slot, cardsByName);
  }
  html += `</div>`;
  html += `<div class="lineup-preview-lane-label"><b>后排</b> · 输出 · 辅助</div>`;
  html += `<div class="lineup-preview-row">`;
  for (let i = 3; i < 6; i++) {
    const slot = slots[i] || {};
    html += renderPreviewSlot(slot, cardsByName);
  }
  html += `</div>`;

  // Map & buffs
  html += `<div class="lineup-preview-support">`;
  if (map) {
    html += `<div class="lineup-preview-map"><strong>${escapeHtml(map.name)}</strong></div>`;
  } else if (mapKey) {
    html += `<div class="lineup-preview-map"><strong>${escapeHtml(mapKey)}</strong></div>`;
  }
  for (const buff of buffs) {
    const buffCard = cardsByName.get(buff.name);
    html += `<div class="lineup-preview-buffs">`;
    html += `<strong>${escapeHtml(buff.name)}</strong>`;
    if (buffCard?.image) {
      html += `<img src="${escapeHtml(buffCard.image)}" alt="${escapeHtml(buff.name)}" style="width:24px;height:24px;border-radius:3px;border:1px solid #263a51;" />`;
    }
    html += `</div>`;
  }
  html += `</div>`;

  html += `</div>`;
  elements.lineupPreviewBoard.innerHTML = html;
}

function renderPreviewSlot(slot, cardsByName) {
  const role = slot.role || "";
  const weapon = slot.weapon || "";
  const items = slot.items || [];

  if (!role && !weapon && items.length === 0) {
    return `<div class="lineup-preview-slot empty-slot"><span class="preview-role-empty">空位</span></div>`;
  }

  let cls = "lineup-preview-slot";
  let content = "";

  if (role) {
    const card = cardsByName.get(role);
    if (card) {
      content += `<span class="preview-role-name">${escapeHtml(card.name)}</span>`;
      const image = cardArtwork(card, "role");
      if (image) {
        content += `<img src="${escapeHtml(image)}" alt="" style="width:32px;height:42px;border-radius:3px;border:1px solid #263a51;margin:2px auto;object-fit:cover;display:block;" />`;
      }
    } else {
      content += `<span class="preview-role-missing">${escapeHtml(role)}</span>`;
    }
  } else {
    content += `<span class="preview-role-empty">空位</span>`;
  }

  if (weapon) {
    const wCard = cardsByName.get(weapon);
    content += `<div class="preview-items">`;
    if (wCard?.image) {
      content += `<img src="${escapeHtml(wCard.image)}" alt="" style="width:20px;height:20px;border-radius:2px;border:1px solid #5c4a1a;" title="${escapeHtml(wCard.name)}" />`;
    }
    content += `<span class="preview-weapon-chip">${escapeHtml(wCard ? wCard.name : weapon)}</span>`;
    content += `</div>`;
  }

  if (items.length > 0) {
    content += `<div class="preview-items">`;
    for (const itemName of items) {
      const ic = cardsByName.get(itemName);
      if (ic?.image) {
        content += `<img src="${escapeHtml(ic.image)}" alt="" style="width:20px;height:20px;border-radius:2px;border:1px solid #2e4660;" title="${escapeHtml(ic.name)}" />`;
      }
      content += `<span class="preview-item-chip">${escapeHtml(ic ? ic.name : itemName)}</span>`;
    }
    content += `</div>`;
  }

  return `<div class="${cls}">${content}</div>`;
}

function buffSelectValue(buff) {
  return buff?.name ? `${buff.name}|${buff.quality || "gold"}` : "";
}

function fillLineupForm(lineup, isNew = false) {
  elements.emptyState.classList.add("hidden");
  elements.editorForm.classList.add("hidden");
  elements.videoEditorForm.classList.add("hidden");
  elements.lineupEditorForm.classList.remove("hidden");
  elements.lineupEditorTitle.textContent = isNew ? "添加推荐阵容" : lineup.name;
  elements.lineupIdText.textContent = lineup.id || "";
  elements.lineupNameInput.value = lineup.name || "";
  elements.lineupLabelInput.value = lineup.label || "";
  elements.lineupOrderInput.value = String(lineup.order || 0);
  elements.lineupHiddenInput.checked = Boolean(lineup.hidden);
  elements.lineupSummaryInput.value = lineup.summary || "";
  elements.lineupKeywordsInput.value = listToText(lineup.keywords);
  renderStrategyChips(lineup.strategy || []);
  renderLineupSlots(lineup.slots);
  elements.lineupMapInput.value = lineup.mapKey || "";
  elements.lineupBuff1Input.value = buffSelectValue(lineup.buffs?.[0]);
  elements.lineupBuff2Input.value = buffSelectValue(lineup.buffs?.[1]);
  renderLineupVideos(lineup.videos || []);
  bindLineupVideoEditor();
  elements.deleteLineupButton.classList.toggle("hidden", isNew);
  elements.duplicateLineupButton.classList.toggle("hidden", isNew);
  elements.lineupSaveStatus.textContent = "";

  // Start listening for live preview updates
  bindLineupLivePreview();
}

function selectLineup(id) {
  state.mode = "lineups";
  state.selectedId = id;
  syncModeControls(true);
  renderList();
  const lineup = selectedLineup();
  if (!lineup) {
    startNewLineup();
    return;
  }
  fillLineupForm(lineup);
}

function startNewLineup() {
  state.mode = "lineups";
  state.selectedId = null;
  syncModeControls(true);
  renderList();
  fillLineupForm({
    id: "",
    name: "",
    label: "自定义阵容",
    summary: "",
    strategy: [],
    keywords: [],
    slots: Array.from({ length: 6 }, () => ({})),
    mapKey: "",
    buffs: [],
    videos: [],
    order: state.lineups.length,
    hidden: false,
  }, true);
}

function bindLineupLivePreview() {
  // Remove old listeners by cloning
  const inputs = elements.lineupEditorForm.querySelectorAll("input, select, textarea");
  // We rely on schedulePreviewUpdate which is already debounced
  // Just bind to key events
  elements.lineupNameInput.oninput = schedulePreviewUpdate;
  elements.lineupSummaryInput.oninput = schedulePreviewUpdate;
  elements.lineupMapInput.onchange = schedulePreviewUpdate;
  elements.lineupBuff1Input.onchange = schedulePreviewUpdate;
  elements.lineupBuff2Input.onchange = schedulePreviewUpdate;
  // Strategy add
  elements.lineupStrategyAddInput.onkeydown = (e) => {
    if (e.key === "Enter") { e.preventDefault(); addStrategyChip(); }
  };
  elements.lineupStrategyAddButton.onclick = addStrategyChip;
  // Trigger initial preview
  schedulePreviewUpdate();
}

function parseBuffValue(value) {
  const [name, quality] = String(value || "").split("|");
  return name ? { name, quality: quality || "gold" } : null;
}

function buildCurrentLineup() {
  const current = selectedLineup();
  const slots = normalizeLineupSlots(state.lineupSlots);
  return {
    id: current?.id || elements.lineupIdText.textContent.trim(),
    name: elements.lineupNameInput.value.trim(),
    label: elements.lineupLabelInput.value.trim(),
    summary: elements.lineupSummaryInput.value.trim(),
    strategy: state.strategyChips.map((item) => String(item || "").trim()).filter(Boolean),
    keywords: textToList(elements.lineupKeywordsInput.value),
    slots,
    mapKey: elements.lineupMapInput.value,
    buffs: [parseBuffValue(elements.lineupBuff1Input.value), parseBuffValue(elements.lineupBuff2Input.value)].filter(Boolean),
    videos: currentLineupVideos().filter((video) => video.url),
    order: current ? Math.max(0, Number(current.order) || 0) : Math.max(0, Number(elements.lineupOrderInput.value) || state.lineups.length),
    hidden: elements.lineupHiddenInput.checked,
  };
}

async function saveLineupsToApi(lineups) {
  // Use PUT to update each lineup's order individually
  await Promise.all(lineups.map((l) =>
    fetch(`/api/lineups/${encodeURIComponent(l.id)}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(l),
    }),
  ));
}

async function saveLineup(event) {
  event.preventDefault();
  const current = selectedLineup();
  const lineup = buildCurrentLineup();
  if (!lineup.name) {
    elements.lineupSaveStatus.textContent = "请填写阵容名称。";
    return;
  }
  elements.saveLineupButton.disabled = true;
  elements.lineupSaveStatus.textContent = "保存中...";
  const response = await fetch(current ? `/api/lineups/${encodeURIComponent(current.id)}` : "/api/lineups", {
    method: current ? "PUT" : "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(lineup),
  });
  elements.saveLineupButton.disabled = false;
  if (!response.ok) {
    elements.lineupSaveStatus.textContent = await response.text();
    return;
  }
  const result = await response.json();
  state.selectedId = current?.id || result.id;
  await loadData();
  elements.lineupSaveStatus.textContent = "已保存，推荐阵容页面已刷新。";
}

async function duplicateLineup() {
  const lineup = selectedLineup();
  if (!lineup) return;
  const response = await fetch(`/api/lineups/${encodeURIComponent(lineup.id)}/duplicate`, { method: "POST" });
  if (!response.ok) {
    elements.lineupSaveStatus.textContent = await response.text();
    return;
  }
  const result = await response.json();
  state.selectedId = result.id;
  await loadData();
}

async function deleteLineup() {
  const lineup = selectedLineup();
  if (!lineup || !window.confirm(`确定删除"${lineup.name}"吗？`)) return;
  const response = await fetch(`/api/lineups/${encodeURIComponent(lineup.id)}`, { method: "DELETE" });
  if (!response.ok) {
    elements.lineupSaveStatus.textContent = await response.text();
    return;
  }
  state.selectedId = null;
  await loadData();
}

// ── Video helpers ──

function buildCurrentVideo() {
  return {
    id: selectedVideo()?.id || elements.videoIdText.textContent.trim(),
    platform: elements.videoPlatformInput.value,
    title: elements.videoTitleInput.value.trim(),
    author: elements.videoAuthorInput.value.trim(),
    url: elements.videoUrlInput.value.trim(),
    category: elements.videoCategoryInput.value.trim(),
    duration: elements.videoDurationInput.value.trim() || null,
    popularity: Number(elements.videoPopularityInput.value) || 0,
    popularityLabel: elements.videoPopularityLabelInput.value.trim(),
    publishedAt: elements.videoPublishedAtInput.value || null,
    cover: elements.videoCoverInput.value.trim() || null,
    order: Number(elements.videoOrderInput.value) || 0,
    hidden: elements.videoHiddenInput.checked,
  };
}

async function parseVideo() {
  const url = elements.videoUrlInput.value.trim();
  if (!url) {
    elements.videoSaveStatus.textContent = "请先粘贴视频链接或分享文本。";
    return;
  }
  elements.parseVideoButton.disabled = true;
  elements.videoSaveStatus.textContent = "正在解析平台页面...";
  const response = await fetch("/api/videos/parse", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ url }),
  });
  elements.parseVideoButton.disabled = false;
  if (!response.ok) {
    elements.videoSaveStatus.textContent = await response.text();
    return;
  }
  const parsed = await response.json();
  const currentOrder = elements.videoOrderInput.value;
  fillVideoForm({ ...parsed, order: Number(currentOrder) || state.videos.length }, !selectedVideo());
  elements.videoSaveStatus.textContent = parsed.warning || "解析完成，请检查信息后保存。";
}

async function saveVideo(event) {
  event.preventDefault();
  const current = selectedVideo();
  const guide = buildCurrentVideo();
  if (!guide.url || !guide.title) {
    elements.videoSaveStatus.textContent = "视频链接和标题不能为空。";
    return;
  }
  elements.saveVideoButton.disabled = true;
  elements.videoSaveStatus.textContent = "保存中...";
  const response = await fetch(current ? `/api/videos/${encodeURIComponent(current.id)}` : "/api/videos", {
    method: current ? "PUT" : "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(guide),
  });
  elements.saveVideoButton.disabled = false;
  if (!response.ok) {
    elements.videoSaveStatus.textContent = await response.text();
    return;
  }
  const result = await response.json();
  state.selectedId = current?.id || result.id;
  await loadData();
  elements.videoSaveStatus.textContent = "已保存，视频攻略页面已刷新。";
}

async function deleteVideo() {
  const video = selectedVideo();
  if (!video || !window.confirm(`确定删除"${video.title}"吗？`)) return;
  elements.deleteVideoButton.disabled = true;
  elements.videoSaveStatus.textContent = "删除中...";
  const response = await fetch(`/api/videos/${encodeURIComponent(video.id)}`, { method: "DELETE" });
  elements.deleteVideoButton.disabled = false;
  if (!response.ok) {
    elements.videoSaveStatus.textContent = await response.text();
    return;
  }
  state.selectedId = null;
  await loadData();
  startNewVideo();
  elements.videoSaveStatus.textContent = "视频已删除。";
}

// ── Card / Faction helpers ──

function buildCurrentOverride(card) {
  return {
    id: card.id,
    resource: card.resource,
    category: card.category,
    name: elements.nameInput.value.trim(),
    quality: elements.qualityInput.value,
    factions: selectedFactions(),
    keywords: textToList(elements.keywordsInput.value),
    descriptions: textToList(elements.descriptionsInput.value),
    hidden: elements.hiddenInput.checked,
  };
}

function buildCurrentFactionOverride(faction) {
  return {
    baseName: faction.baseName,
    name: elements.nameInput.value.trim(),
    keywordCategory: elements.keywordCategoryInput.value.trim(),
    description: elements.descriptionsInput.value.trim(),
    stageEffects: textToList(elements.keywordsInput.value),
    hidden: elements.hiddenInput.checked,
  };
}

async function persistCurrent(successText) {
  if (state.mode === "factions") {
    return persistCurrentFaction(successText);
  }
  const card = selectedCard();
  if (!card) return false;
  const override = buildCurrentOverride(card);
  elements.saveButton.disabled = true;
  elements.saveStatus.textContent = "保存中...";
  const response = await fetch(`/api/cards/${encodeURIComponent(card.id)}/override`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(override),
  });
  elements.saveButton.disabled = false;
  if (!response.ok) {
    elements.saveStatus.textContent = await response.text();
    return false;
  }
  await loadData();
  elements.saveStatus.textContent = successText;
  return true;
}

async function persistCurrentFaction(successText) {
  const faction = selectedFaction();
  if (!faction) return false;
  const override = buildCurrentFactionOverride(faction);
  elements.saveButton.disabled = true;
  elements.saveStatus.textContent = "保存中...";
  const response = await fetch(`/api/factions/${encodeURIComponent(faction.baseName)}/override`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(override),
  });
  elements.saveButton.disabled = false;
  if (!response.ok) {
    elements.saveStatus.textContent = await response.text();
    return false;
  }
  await loadData();
  elements.saveStatus.textContent = successText;
  return true;
}

async function saveCurrent(event) {
  event.preventDefault();
  await persistCurrent("已保存，网页数据已刷新。");
}

async function resetCurrent() {
  if (state.mode === "factions") {
    const faction = selectedFaction();
    if (!faction) return;
    const response = await fetch(`/api/factions/${encodeURIComponent(faction.baseName)}/override`, {
      method: "DELETE",
    });
    if (!response.ok) {
      elements.saveStatus.textContent = await response.text();
      return;
    }
    elements.saveStatus.textContent = "已恢复默认。";
    await loadData();
    return;
  }
  const card = selectedCard();
  if (!card) return;
  const response = await fetch(`/api/cards/${encodeURIComponent(card.id)}/override`, {
    method: "DELETE",
  });
  if (!response.ok) {
    elements.saveStatus.textContent = await response.text();
    return;
  }
  elements.saveStatus.textContent = "已恢复默认。";
  await loadData();
}

async function duplicateCurrent() {
  const card = selectedCard();
  if (!card || card.category !== "consume") return;
  elements.duplicateButton.disabled = true;
  elements.saveStatus.textContent = "复制中...";
  const response = await fetch(`/api/cards/${encodeURIComponent(card.id)}/duplicate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(buildCurrentOverride(card)),
  });
  elements.duplicateButton.disabled = false;
  if (!response.ok) {
    elements.saveStatus.textContent = await response.text();
    return;
  }
  const result = await response.json();
  await loadData();
  selectCard(result.id);
  elements.saveStatus.textContent = "已复制，可继续修改并保存。";
}

async function deleteCurrent() {
  const card = selectedCard();
  if (!card?.raw?.custom_card) return;
  if (!window.confirm(`确定删除"${card.name}"吗？此操作会删除这张复制卡牌。`)) return;
  elements.deleteButton.disabled = true;
  elements.saveStatus.textContent = "删除中...";
  const response = await fetch(`/api/custom-cards/${encodeURIComponent(card.id)}`, {
    method: "DELETE",
  });
  elements.deleteButton.disabled = false;
  if (!response.ok) {
    elements.saveStatus.textContent = await response.text();
    return;
  }
  state.selectedId = null;
  await loadData();
  elements.saveStatus.textContent = "复制卡牌已删除。";
}

// ── Data loading ──

async function loadStaticFactions() {
  const response = await fetch("/data/factions-normalized.json");
  if (!response.ok) return [];
  return response.json();
}

async function loadData() {
  const [response, videoResponse, lineupResponse, mapsResponse] = await Promise.all([
    fetch("/api/cards"),
    fetch("/api/videos"),
    fetch("/api/lineups"),
    fetch("/data/maps-normalized.json"),
  ]);
  if (!response.ok) throw new Error(await response.text());
  if (!videoResponse.ok) throw new Error(await videoResponse.text());
  if (!lineupResponse.ok) throw new Error(await lineupResponse.text());
  const [payload, videoPayload, lineupPayload, mapsPayload] = await Promise.all([
    response.json(),
    videoResponse.json(),
    lineupResponse.json(),
    mapsResponse.ok ? mapsResponse.json() : [],
  ]);
  state.cards = payload.cards;
  state.factions = payload.factions || (await loadStaticFactions());
  state.videos = videoPayload.videos || [];
  state.lineups = lineupPayload.lineups || [];
  state.maps = mapsPayload || [];
  state.overrides = payload.overrides;
  state.factionOverrides = payload.factionOverrides || {};
  renderLineupReferenceOptions();
  syncModeControls(state.mode === "lineups");
  if (!state.selectedId) {
    state.selectedId = state.mode === "factions"
      ? state.factions[0]?.baseName || null
      : state.mode === "videos"
        ? state.videos[0]?.id || null
        : state.mode === "lineups"
          ? filteredLineups()[0]?.id || null
        : state.cards[0]?.id || null;
  }
  renderList();
  if (state.mode === "factions") selectFaction(state.selectedId);
  else if (state.mode === "videos") selectVideo(state.selectedId);
  else if (state.mode === "lineups") selectLineup(state.selectedId);
  else selectCard(state.selectedId);
}

// ── Event wiring ──

elements.editorForm.addEventListener("submit", saveCurrent);
elements.videoEditorForm.addEventListener("submit", saveVideo);
elements.lineupEditorForm.addEventListener("submit", saveLineup);
elements.parseVideoButton.addEventListener("click", parseVideo);
elements.deleteVideoButton.addEventListener("click", deleteVideo);
elements.addVideoButton.addEventListener("click", startNewVideo);
elements.addLineupButton.addEventListener("click", startNewLineup);
elements.deleteLineupButton.addEventListener("click", deleteLineup);
elements.duplicateLineupButton.addEventListener("click", duplicateLineup);
elements.deleteButton.addEventListener("click", deleteCurrent);
elements.duplicateButton.addEventListener("click", duplicateCurrent);
elements.resetButton.addEventListener("click", resetCurrent);
elements.reloadButton.addEventListener("click", loadData);

// Sidebar link clicks
elements.sidebarLinks.forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const page = link.dataset.page;
    switchPage(page).catch((error) => {
      elements.emptyState.innerHTML = `<h2>加载失败</h2><p>${error.message}</p>`;
    });
  });
});

// Search & filter
elements.searchInput.addEventListener("input", renderList);
elements.categoryFilter.addEventListener("change", renderList);
elements.qualityFilter.addEventListener("change", renderList);
elements.hiddenFilter.addEventListener("change", renderList);

// Quality badge
elements.qualityInput.addEventListener("change", () => updateQualityBadge(elements.qualityInput.value));

// Factions picker
elements.factionsToggle.addEventListener("click", () => {
  if (elements.factionsToggle.disabled) return;
  elements.factionsMenu.classList.toggle("hidden");
});
elements.factionsMenu.addEventListener("change", updateFactionToggle);

// Close factions menu on outside click
document.addEventListener("click", (event) => {
  if (!elements.factionsPicker.contains(event.target)) {
    elements.factionsMenu.classList.add("hidden");
  }
});

// Hidden toggle
elements.hiddenInput.addEventListener("change", () => {
  persistCurrent(elements.hiddenInput.checked ? "已隐藏，网页数据已刷新。" : "已取消隐藏，网页数据已刷新。");
});

// Video cover preview
elements.videoCoverInput.addEventListener("input", () => {
  elements.videoCoverPreview.src = elements.videoCoverInput.value.trim();
});
elements.videoPlatformInput.addEventListener("change", () => {
  elements.videoPlatformBadge.textContent = elements.videoPlatformInput.value === "kuaishou" ? "快手" : "抖音";
});

// ── Init ──

loadData().catch((error) => {
  elements.emptyState.innerHTML = `<h2>加载失败</h2><p>${error.message}</p>`;
});

// Handle initial page
switchPage(state.mode).catch((error) => {
  elements.emptyState.innerHTML = `<h2>加载失败</h2><p>${error.message}</p>`;
});
