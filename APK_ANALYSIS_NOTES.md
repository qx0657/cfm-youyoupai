# CFM 悠悠牌 APK 解析记录

本文档整理目前对腾讯手游模拟器内《穿越火线手游》APK 的静态解析结果，重点是“悠悠牌/小小牌手”相关数据。当前结论基于本地 APK、UnityPy、AssetStudio CLI、字符串扫描和资源包测试。

## 基本结论

- APK 内已经包含大量悠悠牌相关表数据。
- 可稳定抽取的主要是文字、规则、词条、阵营、资源名映射等数据。
- 这些表数据主要位于 APK 内的 `assets/bin/Data/*` 无扩展名文件。
- 图片资源名可以从表中拿到，但实际图片暂时没有从 APK 内 `.unity3d` 资源包导出成功。
- APK 内 `.unity3d` 包外层看起来是 UnityFS，但 UnityPy 和 AssetStudio 都无法解析出 Texture2D/Sprite/Unity 对象。

## APK 路径

```text
F:\GameAssistData\app\7AD1C3736F7CF7FD2E77C77CCECB6744_840_com.tencent.tmgp.cf_840.apk
```

APK 特征：

```text
Unity / IL2CPP
Unity version: 5.6.4p4
libunity.so
libil2cpp.so
global-metadata.dat
assets/bin/Data/*
assets/Assets/UIResource/*.unity3d
```

## 已生成的解析输出

解析脚本：

```text
parse_autochess_unity.py
```

运行命令：

```powershell
python parse_autochess_unity.py --scan --out autochess_dump
```

输出目录：

```text
autochess_dump
```

主要输出文件：

```text
autochess_dump/summary.json
autochess_dump/autochess_table_scan.json
autochess_dump/all_target_table_strings.tsv
autochess_dump/AutoChessResourceDataTable.resource_name_guesses.json
```

每张表还会生成：

```text
AutoChessXXX.json
AutoChessXXX.strings.txt
AutoChessXXX.strings.tsv
```

说明：当前这些 `assets/bin/Data/<hash>` 表文件不是 UnityPy 可直接反序列化的标准 Unity 对象容器，所以 `object_count` 为 0；但表内容字符串可读，已导出到 `strings.txt` / `strings.tsv`。

## 关键表文件

### 角色卡

```text
assets/bin/Data/f5979883009ec504db5e581b43fb9f5a
AutoChessRoleDataTable
```

输出：

```text
autochess_dump/AutoChessRoleDataTable.strings.txt
autochess_dump/AutoChessRoleDataTable.strings.tsv
```

能看到的内容示例：

```text
刀锋
斯薇特
关小雨
烛九阴
龙妹
杨玉凝
九尾狐
斯沃特
灵动武士
```

能抽到的字段类型：

```text
角色名
定位，如坦克/输出/辅助
词条，如成长/快手/护盾/遗言
技能描述
属性变化文本，如获得+1+1、获得+2+4
部分参数串，如 1,1 / 2,2 / 4,0,0,0,1,1,0
```

### 武器卡

```text
assets/bin/Data/a6df50c4d4344cc47865956c67bf8948
AutoChessWeaponDataTable
```

输出：

```text
autochess_dump/AutoChessWeaponDataTable.strings.txt
autochess_dump/AutoChessWeaponDataTable.strings.tsv
```

能看到的内容示例：

```text
沙漠之鹰-游骑兵
CZS2-善财童子
斯泰尔-恶魔
MK5-机械纪元
汤姆逊-烈龙
P90-突突兔
AWM-天龙
M200-幻神
M1216-血月
KSG-黑骑士
```

能抽到的字段类型：

```text
武器名
词条
技能描述
伤害/加成描述
部分参数串
```

### 道具、投掷物、消耗、增益、地图类

```text
assets/bin/Data/fc4c92104a7fac64a98d7dcde6b940c0
AutoChessItemDataTable
```

输出：

```text
autochess_dump/AutoChessItemDataTable.strings.txt
autochess_dump/AutoChessItemDataTable.strings.tsv
```

能看到的内容示例：

```text
运输船
沙漠灰
黑色城镇
王者之翼手雷
雷霆王者闪光弹
王者之势烟雾弹
烛九阴燃烧弹
肾上腺素
医疗枪
枪口补偿器
垂直握把
八倍镜
```

能抽到的字段类型：

```text
地图名
投掷物名称
道具/消耗/增益名称
效果描述
属性变化
部分参数串
```

### 技能/词条底层配置

```text
assets/bin/Data/82b167d047887ba4a9b00c25af8dbee1
AutoChessSkillConfigDataTable
```

输出：

```text
autochess_dump/AutoChessSkillConfigDataTable.strings.txt
autochess_dump/AutoChessSkillConfigDataTable.strings.tsv
```

能看到的内容示例：

```text
直接伤害
回复生命
叠加护甲
反击
反射
死亡召唤
召唤
道具伤害
成长：增加自己生命
```

用途：

```text
解释技能 ID 或参数含义
辅助理解角色/武器/道具表中的参数串
```

### 阵营/羁绊

```text
assets/bin/Data/ab6131e64f68b25458a3b454727b102a
AutoChessTrammelsDataTable
```

输出：

```text
autochess_dump/AutoChessTrammelsDataTable.strings.txt
autochess_dump/AutoChessTrammelsDataTable.strings.tsv
```

能看到的内容示例：

```text
隐袭
保卫者
幽灵
山海经
HeartShot
潜伏者
葫芦娃
谍报特工
审判之眼
铠甲勇士
鸿运星光
核心兵器
```

能抽到的字段类型：

```text
阵营名
羁绊类型
羁绊描述
羁绊触发效果
关联角色 ID 列表
```

示例：

```text
山海经
山海经角色获得成长技能
成长：永久获得+1+2
成长：永久获得+2+4
```

### 资源名映射

```text
assets/bin/Data/906e57ae4e4dee34c88cc9611379e93e
AutoChessResourceDataTable
```

输出：

```text
autochess_dump/AutoChessResourceDataTable.strings.txt
autochess_dump/AutoChessResourceDataTable.strings.tsv
autochess_dump/AutoChessResourceDataTable.resource_name_guesses.json
```

能看到的内容示例：

```text
Icon_ZiZouQi_JueSe_DaoFeng_BWZ
Icon_ZiZouQi_JueSe_DaoFeng_BWZ_S
刀锋
Icon_ZiZouQi_JueSe_YunYouYou_BWZ
Icon_ZiZouQi_JueSe_YunYouYou_BWZ_S
云悠悠
```

用途：

```text
建立资源名 -> 中文名的候选映射
后续如果能导出图片，可用资源名匹配卡牌头像/卡图
```

注意：当前只能拿到资源名和中文名，实际图片文件尚未导出。

### 词条解释

```text
assets/bin/Data/044447c884d8c504f8e67a89c07ab5de
AutoChessWordExplanationDataTable
```

输出：

```text
autochess_dump/AutoChessWordExplanationDataTable.strings.txt
autochess_dump/AutoChessWordExplanationDataTable.strings.tsv
```

能看到的内容示例：

```text
成长
在战斗前触发的永久效果
快手
战斗开始时触发的效果
遗言
```

用途：

```text
用于词条解释表
可和角色/武器/道具表中的 <KeyWord> 标签对应
```

### 其他表

```text
assets/bin/Data/d603c8793c8a4a34b9af03173033853c
AutoChessSimpleConfigDataTable
基础规则配置，如升级消耗、卡牌最高等级、玩家人数等

assets/bin/Data/ec5dec5a96ac9fb42a74898cf3384e04
AutoChessSeasonInfoDataTable
赛季信息，包含“小小牌手”

assets/bin/Data/bfc6f50a27551bd439aaf4cbe60417a9
AutoChessVideoInfoDataTable
攻击动画/视频信息

assets/bin/Data/0dffa01da2db8364aa51a24784ace3c2
AutoChessMapConfigDataTable
地图相关配置

assets/bin/Data/b68a49db9007ac648a489169485accda
AutoChessRecommendCardDataTable
推荐卡牌相关

assets/bin/Data/f4b8f146de77826409c03be9fae7433f
AutoChessCombinationShowDataTable
组合展示相关
```

## 目前可整理出的数据类型

现阶段可从 APK 静态解析得到：

```text
角色卡名称
角色卡部分定位
角色卡词条和技能描述
武器卡名称
武器卡词条和技能描述
投掷物/道具/消耗/增益卡名称
投掷物/道具/消耗/增益卡效果描述
阵营/羁绊名称
阵营/羁绊效果
词条解释
资源名与中文名候选映射
赛季/基础规则/地图/视频信息
```

还不能稳定整理出的内容：

```text
完整结构化字段边界
每张卡的完整 ID/品质/攻击/生命等字段
实际头像/卡图 PNG
资源名到具体 .unity3d 包的确认映射
```

原因：当前导出主要基于二进制表中的可读字符串序列，还没有完全反序列化表结构。

## 图片资源现状

APK 内 `.unity3d` 分布：

```text
assets/Assets/UIResource/*.unity3d     500 个，约 1.27GB
assets/Assets/ShaderAB/*.unity3d       2 个
assets/Assets/Config/*.unity3d         1 个
assets/Assets/Resource/*.unity3d       1 个
```

已测试：

```text
UnityPy 扫描全部 504 个 .unity3d：positive 0
AssetStudio CLI 测试 Normal/UnityCN/FakeHeader/NetEase 等模式：0 assets
AssetStudio AssetMap：0 assets
```

结论：

```text
.unity3d 外层可识别为 UnityFS
内层 CAB 数据不能被 UnityPy/AssetStudio 当作标准 Unity serialized asset 解析
图片暂时不能直接导出
```

推测：

```text
资源包可能经过腾讯自定义封装/加密/改格式
实际解密资源可能在运行时缓存或热更目录中
```

## Icon_ZiZouQi_ 资源名专项分析

后续对 `Icon_ZiZouQi_` 前缀做了专项探测，新增了几类有价值的输出。

新增文件：

```text
autochess_dump/icon_zizouqi_occurrences.json
autochess_dump/atlas_sprite_list.json
autochess_dump/icon_zizouqi_sprite_to_atlas.json
autochess_dump/icon_zizouqi_atlas_to_uiresource_hits.json
autochess_dump/icon_zizouqi_asset_config_entries.json
```

### 出现位置

`Icon_ZiZouQi_` 不只出现在 `AutoChessResourceDataTable`，也出现在若干 UIResource 包和资源索引表中。

少量 UIResource 命中：

```text
assets/Assets/UIResource/ua_248.unity3d
assets/Assets/UIResource/ua_249.unity3d
assets/Assets/UIResource/ua_260.unity3d
assets/Assets/UIResource/ua_270.unity3d
assets/Assets/UIResource/ua_283.unity3d
assets/Assets/UIResource/ua_300.unity3d
assets/Assets/UIResource/ua_335.unity3d
assets/Assets/UIResource/ua_355.unity3d
```

大量索引/表命中：

```text
assets/bin/Data/22aed9551f1bb54488c006fd2bad8281
assets/bin/Data/cf9554583c7265d49bab4130c9587e55
assets/bin/Data/2260245957d34804297d9c1c44ac564d
assets/bin/Data/906e57ae4e4dee34c88cc9611379e93e
```

### Sprite 到 Atlas 的映射

`assets/bin/Data/22aed9551f1bb54488c006fd2bad8281` 包含可读的 `AtlasSpriteList` 结构，可提取：

```text
atlasAssetId
atlasAssetName
spriteList
atlasType
```

已生成：

```text
autochess_dump/atlas_sprite_list.json
autochess_dump/icon_zizouqi_sprite_to_atlas.json
```

示例：

```text
Icon_ZiZouQi_JueSe_DaoFeng_BWZ
-> Icon_Pvp_ZiZouQi_Role_01
-> atlasAssetId 400992853

Icon_ZiZouQi_JueSe_DaoFeng_BWZ_S
-> Icon_Pvp_ZiZouQi_Avatar_01
-> atlasAssetId 400992842

Icon_ZiZouQi_JueSe_GuLang_QFZ
-> Icon_Pvp_ZiZouQi_Role_02
-> atlasAssetId 400992854

Icon_ZiZouQi_JueSe_GuLang_QFZ_S
-> Icon_Pvp_ZiZouQi_Avatar_01
-> atlasAssetId 400992842
```

说明：

```text
无 _S 的角色资源多为角色大图/卡图图集
带 _S 的资源多为小头像图集
```

### Atlas 到 UIResource 的部分定位

对所有 ZiZouQi atlas 名称和 500 个 UIResource 包做了明文交叉匹配，已生成：

```text
autochess_dump/icon_zizouqi_atlas_to_uiresource_hits.json
```

部分直接命中：

```text
Icon_Pvp_ZiZouQi_Avatar_01 -> assets/Assets/UIResource/ua_248.unity3d
Icon_Pvp_ZiZouQi_Avatar_02 -> assets/Assets/UIResource/ua_248.unity3d
Icon_Pvp_ZiZouQi_Spells_01 -> assets/Assets/UIResource/ua_249.unity3d
Icon_Pvp_ZiZouQi_Spells_02 -> assets/Assets/UIResource/ua_249.unity3d
Icon_Pvp_ZiZouQi_Weapon_Enemy_01 -> assets/Assets/UIResource/ua_260.unity3d
Icon_Pvp_ZiZouQi_Weapon_We_01 -> assets/Assets/UIResource/ua_260.unity3d
Icon_Pvp_ZiZouQi_Avatar_03 -> assets/Assets/UIResource/ua_300.unity3d
```

注意：

```text
不是所有 atlas 都能在 UIResource 中明文定位
例如 Icon_Pvp_ZiZouQi_Role_01 / Role_02 暂未在 UIResource 明文命中
```

### AssetId 到 Unity 工程路径

`assets/bin/Data/2260245957d34804297d9c1c44ac564d` 包含资源配置条目，可提取：

```text
ID
Path
Key
LoadMode
BuildAB
Merge2UI
```

已生成：

```text
autochess_dump/icon_zizouqi_asset_config_entries.json
```

示例：

```text
400992842
Assets/Textures/UI/2020UI/Icon/Pvp/ZiZouQi/Avatar/Icon_Pvp_ZiZouQi_Avatar_01.prefab
Key: Icon_Pvp_ZiZouQi_Avatar_01

400992853
Assets/Textures/UI/2020UI/Icon/Pvp/ZiZouQi/Card/Role/Icon_Pvp_ZiZouQi_Role_01.prefab
Key: Icon_Pvp_ZiZouQi_Role_01

400992854
Assets/Textures/UI/2020UI/Icon/Pvp/ZiZouQi/Card/Role/Icon_Pvp_ZiZouQi_Role_02.prefab
Key: Icon_Pvp_ZiZouQi_Role_02
```

这意味着目前已经可以建立如下链路：

```text
卡牌中文名
-> Icon_ZiZouQi_* 资源名
-> atlasAssetName / atlasAssetId
-> Unity 工程资源路径
-> 部分 atlas 可定位到 ua_*.unity3d
```

仍未完成：

```text
从 ua_*.unity3d 导出实际纹理图片
从 atlas 中裁剪具体 sprite
定位所有 atlas 对应的具体 UIResource 包
```

## 运行时数据探索状态

模拟器配置显示：

```text
ADB_PORT: 127.0.0.1:15120 -> guest 5555
SSHFS_PORT: 127.0.0.1:22222 -> guest 22
```

尝试结果：

```text
ADB 端口可连通，但设备 offline
SSH 端口可连通，但需要密钥
```

当前数据盘：

```text
F:\GameAssist\Image\data.vhd
约 20.8 GB
```

它很可能包含 Android `/data` 分区。模拟器运行时该 VHD 被锁定，Windows 只读挂载失败。后续若需要查运行时缓存，可关闭模拟器后只读挂载该 VHD。

目标目录：

```text
/data/data/com.tencent.tmgp.cf/
/data/media/0/Android/data/com.tencent.tmgp.cf/
/sdcard/Android/data/com.tencent.tmgp.cf/
```

## 建议的下一步

### 短期：先清洗文字数据

优先从以下文件做半结构化清洗：

```text
AutoChessRoleDataTable.strings.tsv
AutoChessWeaponDataTable.strings.tsv
AutoChessItemDataTable.strings.tsv
AutoChessTrammelsDataTable.strings.tsv
AutoChessWordExplanationDataTable.strings.tsv
AutoChessResourceDataTable.resource_name_guesses.json
```

可先产出：

```text
cards_raw.json
roles_raw.json
weapons_raw.json
items_raw.json
trammels_raw.json
keywords.json
resource_names.json
```

### 中期：补表结构解析

观察 `strings.tsv` 中名称、描述、参数串的顺序，按表类型写专门解析器。目标是把连续字符串和参数串还原为对象：

```json
{
  "type": "role",
  "name": "刀锋",
  "keywords": ["成长"],
  "description": "成长：友方+1+1，本局每次触发后，提升此效果",
  "upgrade_description": "成长：友方+2+2，本局每次触发后，提升此效果",
  "resource_name": "Icon_ZiZouQi_JueSe_DaoFeng_BWZ"
}
```

### 后期：再处理图片

图片先暂停。后续可选路线：

```text
关闭模拟器后只读挂载 data.vhd，找解密后的热更资源
修复模拟器 ADB offline 后直接 adb 查目录
分析 .unity3d 内层 CAB 的自定义封装
结合资源名表定位图片资源
```

## 当前最有价值的文件

```text
parse_autochess_unity.py
APK_ANALYSIS_NOTES.md
autochess_dump/summary.json
autochess_dump/autochess_table_scan.json
autochess_dump/all_target_table_strings.tsv
autochess_dump/AutoChessRoleDataTable.strings.tsv
autochess_dump/AutoChessWeaponDataTable.strings.tsv
autochess_dump/AutoChessItemDataTable.strings.tsv
autochess_dump/AutoChessTrammelsDataTable.strings.tsv
autochess_dump/AutoChessResourceDataTable.resource_name_guesses.json
```

## 追加：ID -> Bundle 与 CAB 内层尝试

本轮继续搜索了 APK 内 `assets/bin/Data/*`：

- 新增扫描结果：`autochess_dump/id_bundle_candidate_scan.json`
- 暂未发现明文 `400992853 -> ua_xxx` 或 `Icon_Pvp_ZiZouQi_Role_01 -> ua_xxx` 映射。
- `49ffba6bc3160b54fa46faf4022bd856` 仍确认是 `AssetStore_Bin` 风格资源清单，只能到 `ID / Path / Key`。
- `623fed95677da6549aea2f387018bace` 的 `abName` 命中是误报，实际主要是 `tabName`。
- `4b561d7cbac939949aa8b8e0723ca9b3` 更像脚本/元信息，能看到 `GetABNameByHash`、`GetInnerABNames_ByAllCfg`、`GetAssetBundlePath` 等函数名，但本身不是映射数据表。

因此，`ID -> Bundle` 可能不在 APK 的明文 Data 表里，而是在运行时代码按资源路径或 ID hash 计算、运行时补丁/缓存目录里，或 AssetBundleCfg/其他配置经过自定义二进制格式保存。

### 内层 CAB 进展

对 `autochess_dump/icon_zizouqi_cabs/ua_248__CAB-8280bb93b84ebd14bfd115695c8d50f1` 做了修头试验：

- 原 CAB 头不是标准 Unity serialized header，开头类似 `36 39 xx xx ... 5.6.4p4`。
- 对 header 里的 size/offset 字段去掉固定高位 `0x36390000` 后，数值变得接近 Unity serialized file。
- 试验产物在：`autochess_dump/cab_header_patch_tests/`
- 最有用的样本：`xor_swap_actual_size.assets`

AssetStudio 使用 `--game FakeHeader` 读取 `xor_swap_actual_size.assets` 时有部分突破：

- 能识别出约 31 个对象；
- map 输出：`autochess_dump/cab_header_patch_tests/assetstudio_out/patched_map.json`
- 对象类型包括 `Texture2D`、`Material`、`GameObject`、`AssetBundle`；
- 但对象数据偏移仍不完全正确，导出 Texture2D 时名称/尺寸等字段会错位，暂不能稳定导出 PNG。

CAB metadata 中已经能看到 Unity TypeTree 字段，例如 `m_Width`、`m_Height`、`m_TextureFormat`、`m_CompleteImageSize`。对象数据区也能找到明文纹理名，例如 `Icon_Pvp_ZiZouQi_BG_06`、`Icon_Pvp_ZiZouQi_BG_02`。

当前判断：这批 `.unity3d` 不是完全加密。UnityFS 外层可解，内层 CAB 主要是 serialized header / metadata / object offset 做了自定义扰动。继续方向应是反推对象表里的 offset/size 编码规则，而不是继续盲扫普通 AssetStudio 模式。

## 追加：CAB 纹理解析已打通

新增脚本：

```text
extract_cf_cab_textures.py
```

用途：对已经从 UnityFS 外层拆出来的内层 CAB 文件，手工解析 Unity serialized metadata/object table，再提取 `Texture2D` 的 ETC2_RGBA8 atlas 并导出 PNG。

本轮对以下目录批量解析：

```text
autochess_dump/icon_zizouqi_cabs/
```

输出目录：

```text
autochess_dump/cab_texture_extract/
autochess_dump/cab_texture_extract/manifest.json
autochess_dump/cab_texture_extract/contact.png
```

最新 manifest 统计：

```text
ua_248: 16 / 16
ua_249: 11 / 11
ua_260: 16 / 16
ua_270: 13 / 13
ua_283:  8 / 16
ua_300:  4 / 16
ua_335: 14 / 16
ua_355: 16 / 16
合计：98 / 120
```

关键规则：

- 每个 CAB 的 type table 顺序不同，不能固定认为 `typeID=2` 是 Texture2D；必须按 type table 找 `classID=28`。
- CAB 里真实 object table 可直接按小端读取：`pathID:int64 / offset:uint32 / size:uint32 / typeID:int32`。
- `dataOffset` 不能直接信 CAB 头，需要结合 object table 和对象区内的资源名推断。
- 这些 UI atlas 多为 ETC2_RGBA8，Unity TextureFormat 值为 `47`。
- 某些 CAB 的 Texture2D 头被截短，脚本会 fallback 搜 `image_len`：`0x100000`、`0x40000`、`0x10000`，再按 ETC2_RGBA8 推断 `1024x1024`、`512x512`、`256x256`。
- 输出 PNG 是整张 atlas，不是单个 sprite。后续若要得到单卡图片，需要结合 `AtlasSpriteList` 里的 sprite 坐标/名称继续裁剪。

目前已经能看到角色、武器、技能/词条、地图、羁绊等 atlas，说明 APK 内的图片资源解析路线可行。

## 追加：单个 sprite/卡牌图片裁剪

新增脚本：

```text
crop_zizouqi_sprites.py
build_zizouqi_card_image_index.py
```

当前输出：

```text
autochess_dump/zizouqi_sprite_crops/
autochess_dump/zizouqi_sprite_crops/manifest.json
autochess_dump/zizouqi_sprite_crops/card_related_contact.png
autochess_dump/zizouqi_card_image_index.json
autochess_dump/zizouqi_image_summary.json
```

关键修正：

- `MonoBehaviour/UIAtlas` 中可以读出 sprite 名称与 `x/y/w/h`。
- `UIAtlas -> Material -> Texture2D` 引用链可以通过 pathID 反解，不能只靠 atlas 文件名猜。
- UIAtlas 坐标使用左下原点；导出的 PNG 使用左上原点，裁剪时要翻转 y。
- 部分 atlas 解出为 512，但坐标基准仍按 1024 写，裁剪时需要按 0.5/0.25 缩放 fallback。
- 角色类 `Icon_ZiZouQi_JueSe_*` 裁剪后需要旋转 180 度，才能得到游戏中正常方向。

当前裁剪统计：

```text
总 sprite: 1017
成功裁剪: 985
缺失: 32
```

`zizouqi_card_image_index.json` 已把资源名、中文名猜测、图片类型、atlas 信息、裁剪 PNG 路径整理到一起。角色卡面、角色头像、道具、支援、词条/羁绊等大部分图片已经可直接按资源名查找。
