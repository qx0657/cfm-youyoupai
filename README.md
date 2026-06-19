# CF 悠悠牌资料库

面向 CF Mobile 悠悠牌/自走棋模式的静态资料库。项目把 APK 中解析出的卡牌、阵营、地图、增益和攻略数据整理成 JSON 与图片资源，再由 React/Vite 单页应用展示。

## 功能概览

- 卡牌资料库：角色、武器、投掷物、道具、消耗品、增益卡统一检索与筛选。
- 阵营与羁绊：展示阵营说明、阶段效果和关联角色。
- 基础资料：规则指南、商店概率、术语解释、地图效果。
- 阵容推荐：内置阵容方案，并支持通过本地管理端维护扩展阵容。
- 视频攻略：维护抖音、快手等平台视频链接快照，静态站点不依赖平台 API。
- 本地管理端：用于维护覆盖数据、自定义卡牌、阵容和视频条目。

## 目录结构

```text
.
├── cfuu/                       # React 19 + Vite 6 前端项目
│   ├── admin/                  # 本地管理端页面
│   ├── data/                   # 人工覆盖与扩展数据
│   ├── public/                 # 静态 JSON 和图片资源
│   ├── scripts/                # 数据准备、管理端、部署脚本
│   └── src/                    # 单页应用源码
├── Maps/                       # 地图原始二进制文件
├── autochess_dump/             # APK 解析中间产物，本地生成，不提交
├── *.py                        # 根目录数据抽取与整理脚本
├── AGENTS.md                   # Codex/自动化协作者工程约定
└── APK_ANALYSIS_NOTES.md       # APK 逆向分析记录
```

## 环境要求

- Node.js 20+，npm
- Python 3.10+
- Windows PowerShell 可直接运行现有命令；其他系统需要按路径分隔符自行调整
- 如需完整重建数据，需要准备 CF Mobile APK 文件

## 快速开始

```powershell
cd .\cfuu
npm install
npm run dev
```

开发服务器默认监听 `0.0.0.0`，Vite 会在终端输出本地访问地址。

常用命令：

```powershell
npm run build          # TypeScript 检查 + Vite 生产构建
npm run preview        # 预览 dist 构建结果
npm run admin          # 启动本地管理端，端口 5174
npm run prepare:data   # 用 cfuu/data 覆盖数据重新生成 public/data
```

## 数据流水线

完整流程由 `cfuu/scripts/rebuild-from-apk.py` 编排：

```powershell
cd .\cfuu
npm run pipeline -- --apk "F:\path\to\com.tencent.tmgp.cf.apk" --clean
```

常用参数：

- `--clean`：清理旧的 `autochess_dump` 和生成数据后重建。
- `--from-existing-dump`：跳过 APK 解析，基于已有中间产物重新整理。
- `--skip-build`：只生成 `public/data` 与 `public/assets/cards`，不执行前端构建。
- `--scan`：额外扫描 APK Unity Data，排查新版表结构变化。

更多细节见 [cfuu/PIPELINE.md](cfuu/PIPELINE.md)。

## 人工覆盖数据

管理端和数据准备脚本主要读取 `cfuu/data/`：

- `card-overrides.json`：卡牌名称、阵营、关键词、描述等覆盖。
- `custom-cards.json`：人工新增卡牌。
- `faction-overrides.json`：阵营展示名、描述、关键词覆盖。
- `recommended-lineups.json`：推荐阵容扩展数据。
- `video-guides.json`：视频攻略条目。

运行管理端：

```powershell
cd .\cfuu
npm run admin
```

管理端会在写入前生成本地备份到 `cfuu/data/override-backups/`，该目录不提交。

## 前端架构

- 入口：`cfuu/src/main.tsx`
- 主应用：`cfuu/src/App.tsx`
- 数据加载：`cfuu/src/data/loaders.ts`
- 类型定义：`cfuu/src/data/types.ts`
- 样式：`cfuu/src/styles/main.css`

应用采用 hash 路由，不引入路由库。所有页面均为静态资源驱动，生产部署不需要后端服务。

主要路由：

| 路由 | 内容 |
| --- | --- |
| `#/library/all` | 全部卡牌与仪表盘 |
| `#/library/role` | 角色卡 |
| `#/library/weapon` | 武器卡 |
| `#/library/throwable` | 投掷物 |
| `#/library/item` | 道具 |
| `#/library/consume` | 消耗品 |
| `#/library/factions` | 阵营/羁绊 |
| `#/basics/guide` | 基础指南 |
| `#/basics/maps` | 地图资料 |
| `#/basics/buffs` | 增益卡 |
| `#/ai` | 推荐阵容 |
| `#/videos` | 视频攻略 |

## 部署

`cfuu/scripts/deploy.mjs` 会读取 `cfuu/.env.deploy`，执行构建、打包并通过 SCP 上传。

```powershell
cd .\cfuu
Copy-Item .\.env.deploy.example .\.env.deploy
# 填写 DEPLOY_HOST、DEPLOY_USER、DEPLOY_SSH_KEY 等配置
npm run deploy
```

`.env.deploy` 包含私有部署信息，不提交到 Git。

## 提交约定

建议提交：

- `cfuu/src/`、`cfuu/admin/`、`cfuu/scripts/`
- `cfuu/data/` 中当前有效的人工维护数据
- `cfuu/public/data/` 与 `cfuu/public/assets/` 中站点运行需要的静态数据和图片
- 根目录 Python 流水线脚本、`Maps/`、工程文档

不要提交：

- `autochess_dump/`
- `node_modules/`
- `cfuu/dist/`
- `.env.deploy`、密钥、日志、管理端备份

项目包含从游戏客户端解析出的资源，仓库应保持私有。
