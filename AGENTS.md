# AGENTS.md

本文件给 Codex 和其他自动化协作者提供工程约定。修改代码前请先阅读本文件、`README.md`、`cfuu/PIPELINE.md`，涉及 APK 解析时再参考 `APK_ANALYSIS_NOTES.md`。

## 项目概览

**CF 悠悠牌资料库** 是一个静态 React/Vite 单页应用，用来展示 CF Mobile 悠悠牌/自走棋模式的卡牌、阵营、地图、增益、阵容和攻略数据。原始数据来自 APK 解析流水线，最终以 `cfuu/public/data/*.json` 和 `cfuu/public/assets/**` 供前端读取。

根目录职责：

- `cfuu/`：前端应用、管理端、数据准备脚本和部署脚本。
- `*.py`：APK/Unity 资源解析、图片裁切、卡牌组织、序列化脚本。
- `Maps/`：地图原始二进制文件。
- `autochess_dump/`：流水线中间目录，本地生成，不提交。
- `APK_ANALYSIS_NOTES.md`：APK 逆向与资源定位记录。

## 常用命令

```powershell
cd .\cfuu

npm install
npm run dev
npm run build
npm run preview

npm run admin
npm run prepare:data

npm run pipeline -- --apk "F:\path\to\com.tencent.tmgp.cf.apk" --clean
npm run pipeline -- --from-existing-dump --skip-build
```

命令含义：

- `npm run dev`：启动 Vite 开发服务器，监听 `0.0.0.0`。
- `npm run build`：执行 `tsc -b && vite build`，是前端修改后的最低验证。
- `npm run admin`：启动本地管理端，端口 `5174`。
- `npm run prepare:data`：应用 `cfuu/data/` 覆盖数据并重建 `public/data/`。
- `npm run pipeline`：从 APK 或已有 dump 重建网页数据和图片。

## 前端架构

所有主要 UI 目前集中在 `cfuu/src/App.tsx`。这是既有架构，除非任务明确要求拆分，否则优先做局部、低风险修改。

关键文件：

- `cfuu/src/main.tsx`：应用入口。
- `cfuu/src/App.tsx`：页面、筛选、hash 路由和主要交互。
- `cfuu/src/data/loaders.ts`：加载 `/data/` 下的静态 JSON。
- `cfuu/src/data/types.ts`：数据模型类型。
- `cfuu/src/styles/main.css`：手写深色主题 CSS。
- `cfuu/admin/`：独立的本地管理端页面。

路由采用 `window.location.hash`，不要引入 router 库。站点生产形态是纯静态部署，不要把运行时功能绑定到本地 admin server。

## 数据模型与资源

卡牌分类固定为：

```text
role, weapon, throwable, item, consume, buff
```

品质排序固定为：

```text
grey -> green -> blue -> purple -> gold -> red
```

站点运行资源位置：

- `cfuu/public/data/cards.json`
- `cfuu/public/data/buffs.json`
- `cfuu/public/data/factions-normalized.json`
- `cfuu/public/data/maps-normalized.json`
- `cfuu/public/data/summary.json`
- `cfuu/public/assets/cards/{category}/`
- `cfuu/public/assets/cards/fetters/`

人工维护数据位置：

- `cfuu/data/card-overrides.json`
- `cfuu/data/custom-cards.json`
- `cfuu/data/faction-overrides.json`
- `cfuu/data/recommended-lineups.json`
- `cfuu/data/video-guides.json`

`cfuu/data/override-backups/` 是管理端生成的本地备份，不提交。

## 流水线约定

完整流水线由 `cfuu/scripts/rebuild-from-apk.py` 编排，根目录 Python 脚本按阶段顺序执行：

| 阶段 | 脚本 |
| --- | --- |
| 提取 | `parse_autochess_unity.py`, `prepare_zizouqi_cabs.py`, `extract_cf_cab_textures.py` |
| 裁切 | `crop_zizouqi_sprites.py`, `extract_ua257_texture10_slices.py`, `extract_ladder_icons.py` |
| 索引 | `build_zizouqi_card_image_index.py` |
| 组织 | `organize_zizouqi_{roles,weapons,throwables,items,consume_buffs,fetters,maps,zhiyuan}.py` |
| 预览图 | `build_zizouqi_{role,weapon,throwable,item,consume}_card_previews.py`, `compose_zizouqi_card_preview.py` |
| 序列化 | `serialize_zizouqi_role_data.py`, `serialize_zizouqi_weapon_data.py`, `serialize_zizouqi_item_like_data.py`, `serialize_zizouqi_faction_data.py` |
| Web 生成 | `cfuu/scripts/prepare-data.mjs` |

维护原则：

- 卡牌名称、词条和描述解析优先在序列化脚本修正，不要在前端页面硬编码。
- 地图展示名和地图效果维护在 `cfuu/scripts/prepare-data.mjs`。
- 新 APK 资源包变化时，先更新 `prepare_zizouqi_cabs.py` 的资源包列表，再检查裁切脚本。
- `autochess_dump/` 可随时重建，视为本地工作区。

## 样式与交互约定

- 所有用户可见文本使用中文。
- 继续使用手写 CSS，不引入 Tailwind、Bootstrap 等框架。
- 保持深色主题基调，现有背景基色为 `#070b11`。
- 筛选、标签、卡片、详情面板优先沿用 `main.css` 里的现有类名和布局。
- 图标按钮优先使用项目已有的 `lucide-react`。
- 修改响应式布局时至少检查 360px 宽度下文本不溢出、不重叠。

## 验证要求

前端代码修改后至少运行：

```powershell
cd .\cfuu
npm run build
```

只修改数据准备或覆盖数据时，优先运行：

```powershell
cd .\cfuu
npm run prepare:data
npm run build
```

流水线修改后，如没有 APK，可用现有 dump 做轻量验证：

```powershell
cd .\cfuu
npm run pipeline -- --from-existing-dump --skip-build
```

若因缺少 APK、缺少依赖或本地数据过大无法验证，必须在最终说明里明确写出。

## Git 与私有资料

本项目应保持私有仓库。不要提交：

- `autochess_dump/`
- `node_modules/`
- `cfuu/dist/`
- `cfuu/.deploy/`
- `.env*`、`cfuu/.env*` 中的私有配置
- `*.log`
- `cfuu/data/override-backups/`
- `.codex/`
- `.claude/settings.local.json`

可以提交站点运行需要的 `cfuu/public/data/` 和 `cfuu/public/assets/`。这些是静态部署输入，不是临时构建产物。

如果工作区已有用户改动，不要回滚。只编辑当前任务相关文件，并在最终说明里区分文档修改、数据修改和上传状态。
