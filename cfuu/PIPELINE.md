# CFM 悠悠牌数据流水线

这套流程用于把新的 CF Mobile APK 重新解析成 `cfuu` 网页可用的数据和图片资源。

## 一键更新

在 `cfuu` 目录运行：

```powershell
npm run pipeline -- --apk "F:\path\to\com.tencent.tmgp.cf.apk" --clean
```

也可以从项目根目录调用同一个脚本：

```powershell
python .\cfuu\scripts\rebuild-from-apk.py --apk "F:\path\to\com.tencent.tmgp.cf.apk" --clean
```

常用参数：

- `--apk <path>`：新 APK 路径。
- `--clean`：先删除旧的 `autochess_dump` 和网页生成数据，再完整重建。
- `--scan`：额外扫描 APK 内 `assets/bin/Data`，用于排查新版本表结构变化。
- `--from-existing-dump`：不读取 APK，只用现有 `autochess_dump` 重新整理数据并生成网页资源。
- `--skip-build`：只生成 `public/data` 与 `public/assets/cards`，不执行生产构建。

## 流程阶段

1. `parse_autochess_unity.py`
   从 APK 的 Unity Data 表里提取 AutoChess/悠悠牌文本表、资源名猜测和字符串索引。

2. `prepare_zizouqi_cabs.py`
   从 APK 的 `assets/Assets/UIResource/ua_*.unity3d` 提取内层 CAB 包。

3. `extract_cf_cab_textures.py`
   从 CAB 包里导出 Texture2D 图集，写入 `autochess_dump/cab_texture_extract`。

4. `crop_zizouqi_sprites.py`
   根据 sprite 到 atlas 的关系裁出角色、武器、道具、地图、阵营等图标。

5. `extract_ua257_texture10_slices.py`
   裁出商店卡牌框、品质底、职业图标等 UI 层。

6. `build_zizouqi_card_image_index.py`
   把表资源名与裁出的图片建立索引。

7. `organize_zizouqi_*.py`
   把角色、武器、投掷物、道具、消耗、增益、阵营、地图资源分组整理。

8. `build_zizouqi_*_card_previews.py`
   生成角色、武器、投掷物、道具的卡牌预览图。

9. `serialize_zizouqi_*_data.py`
   结合表数据、图片和预览图，生成网页消费的结构化数据。

10. `cfuu/scripts/prepare-data.mjs`
    复制整理后的数据和图片到 `cfuu/public`，并生成：
    - `public/data/cards.json`
    - `public/data/buffs.json`
    - `public/data/factions-normalized.json`
    - `public/data/maps-normalized.json`
    - `public/data/summary.json`

11. `npm run build`
    执行 TypeScript 与 Vite 构建。

## 新版本维护点

- 新增或变化的 UIResource 包：更新 `../prepare_zizouqi_cabs.py` 的 `DEFAULT_UA_IDS`。
- 新增 atlas/sprite 对应关系：更新 `../crop_zizouqi_sprites.py` 的 atlas 处理逻辑或手动补录项。
- 地图名称和效果：更新 `scripts/prepare-data.mjs` 里的 `mapDisplayNames` 和 `mapBonusDescriptions`。
- 增益误解析过滤：更新 `scripts/prepare-data.mjs` 里的 `misparsedBuffResourceStems`。
- 卡牌名、词条和描述解析：优先更新 `../serialize_zizouqi_*_data.py`，不要在前端页面里硬编码修正。

## 验证

完整更新后至少运行：

```powershell
npm.cmd run build
```

如果只想检查数据生成：

```powershell
npm run pipeline -- --from-existing-dump --skip-build
```
