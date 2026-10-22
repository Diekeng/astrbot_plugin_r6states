# AstrBot-Plugin-R6States

基于 [nonebot-plugin-R6States](https://github.com/Siornya/nonebot-plugin-R6States) 的 AstrBot 移植强化版，用于查询《彩虹六号：围攻》(Rainbow Six Siege) 的玩家战绩、干员/地图/武器百科、实时在线人数以及职业赛事信息。

数据全部来自公开 API，不含 Playwright / BeautifulSoup 爬虫逻辑。

> **v1.1.0 起数据源迁移至 [r6.arenyze.com](https://r6.arenyze.com/)**。旧站 `r6data.eu` 已停用，旧 Key 同时失效，请按下方说明重新申请。

## 功能特性

- **玩家战绩**：排位 / 标准 / 休闲三种模式的 KD、胜率、击杀死亡、场次，以及当前段位与赛季最高段位。
- **常用干员**：按局数排序展示生涯最常用的 3 名干员及其胜率。
- **排位变动**：查看最近的 RP 增减记录与对应段位。
- **战术百科**：干员、地图、武器详细数据，地图支持中文名搜索。
- **实时在线**：Steam / Ubisoft Connect / 主机平台的在线人数估算与注册用户统计。
- **电竞赛事**：通过 PandaScore 查询战队或赛区的近期赛程与比分。
- **LLM 函数调用**：已接入 AstrBot Function Calling，可直接用自然语言查询，例如"查一下 MacieJay 的战绩"。
- **批量查询**：一次最多查询 5 名玩家。

## 准备工作

使用前需要申请以下 API 密钥：

1. **R6Data API Key（必需）**
   - 前往 [r6.arenyze.com](https://r6.arenyze.com/) 注册并生成免费 Key。
   - Key 有效期约为 **1 个月**，过期后需重新生成，否则请求会返回 401。
2. **PandaScore Token（可选）**
   - 前往 [PandaScore](https://www.pandascore.co/) 注册开发者账号并获取免费 Token。
   - 不配置时仅赛事查询不可用，不影响战绩与百科功能。

## 安装

环境要求：AstrBot `>= 4.0.0`。

1. 将本仓库放入 AstrBot 的插件目录：

   ```text
   AstrBot/data/plugins/astrbot_plugin_r6states/
   ```

2. 安装依赖（AstrBot 通常会在加载插件时自动安装）：

   ```bash
   pip install -r requirements.txt
   ```

3. 重启 AstrBot，在 WebUI 的插件列表中确认本插件已加载。

## 配置

**方式一：WebUI（推荐）**

进入 AstrBot WebUI → 插件 → 彩六战绩查询 → 配置，填写：

| 配置项 | 说明 |
| :--- | :--- |
| `api_key` | R6Data API Key，用于战绩、百科与在线人数 |
| `pandascore_api_key` | PandaScore Token，用于电竞赛事查询（可选） |

**方式二：指令绑定**

```bash
/R6DAPI <你的 R6Data Key>
```

> 通过指令写入的配置在部分部署方式下可能不会持久化，建议同时在 WebUI 中固化。

## 指令列表

### 玩家战绩

| 指令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `/R6 <玩家ID>` | 查询单名玩家的赛季战绩概览 | `/R6 MacieJay` |
| `/R6 -g <ID1> <ID2> ...` | 批量查询，最多 5 人 | `/R6 -g MacieJay Beaulo` |
| `/R6 -h [指令\|all]` | 查看帮助：默认显示常用指令，`all` 显示全部，或指定指令查看详情 | `/R6 -h`、`/R6 -h all`、`/R6 -h r6h` |
| `/R6H <玩家ID>` | 查看最近的排位 RP 变动记录 | `/R6H MacieJay` |

### 百科与工具

| 指令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `/r6op <干员名>` | 干员属性、定位、组织与背景信息 | `/r6op Ash` |
| `/r6map <地图名>` | 地图详情，支持中文名 | `/r6map 俄勒冈` |
| `/r6w <武器名>` | 武器伤害、射速、弹匣与配件 | `/r6w R4-C` |
| `/r6s` | 全平台实时在线人数 | `/r6s` |

### 职业赛事

| 指令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `/R6M <队伍名>` | 查询战队最近 5 场比赛 | `/R6M G2`、`/R6M w7m` |
| `/R6M <赛区简称>` | 查询赛区最新赛程 | `/R6M NAL`、`/R6M EU` |

支持的赛区简称：`EU` / `EML`、`NA` / `NAL`、`CN` / `CNL`、`BR`、`LATAM`、`KR`、`JP`、`ASIA`、`APL`、`SAL`、`SA`、`OCE`、`MENA`。

> 建议直接使用自然语言，由 AstrBot 自动调用对应工具，体验更好。

## 数据来源

| 数据 | 接口 |
| :--- | :--- |
| 玩家档案与排位变动 | `https://public-api.arenyze.com/r6/api/v2/profile` |
| 干员战绩 | `https://public-api.arenyze.com/r6/api/v2/operators` |
| 实时在线人数 | `https://public-api.arenyze.com/r6/api/v2/gamestats` |
| 干员 / 地图 / 武器百科 | `https://public-api.arenyze.com/r6/api/{operators\|maps\|weapons}` |
| 电竞赛事 | `https://api.pandascore.co` |

所有 R6Data 请求通过请求头 `api-key` 鉴权。

## 常见问题

**返回"API 密钥无效或权限被拒绝"**
Key 已过期或填写有误。前往 [r6.arenyze.com](https://r6.arenyze.com/) 重新生成，Key 有效期约 1 个月。

**提示"未找到对应数据"**
确认玩家 ID 拼写正确。当前只支持 Ubisoft Connect（`uplay`）平台 ID，不支持 Steam 昵称或邮箱。

**提示"上游统计服务暂时繁忙"或 HTTP 503**
这是 R6Data 上游统计服务限流，不是插件或 Key 的问题。服务端会在响应里给出建议重试时间，按提示稍后再试即可；热门玩家通常已有缓存，可以直接查询。免费 Key 的额度约为 **40 次/分钟、200 次/小时、400 次/天**，`/R6` 每查询一名玩家消耗 2 次请求。

**百科查不到**
干员、地图、武器请使用英文名；地图指令支持常见中文名自动转换。

**赛事查询无结果**
检查 `pandascore_api_key` 是否配置；部分赛区（如 CN）可能尚未开赛，可改用队伍名查询。

**排位变动为空**
玩家本赛季可能还没有排位记录，或 API 暂未返回历史数据。

## 更新日志

### v1.1.0

- 数据源迁移至 `https://public-api.arenyze.com/r6/api`，适配 v2 接口。
- 玩家战绩改用 `/v2/profile`，干员数据改用 `/v2/operators`。
- `/R6H` 改为读取 `/v2/profile` 的 `history`，响应更快。
- 适配新版返回结构：战绩位于 `stats` 下，干员为扁平数组，板块新增 `casual` / `event` / `warmup`。
- 干员百科适配新字段（移除已下线的背景传记，补充出生地、年龄、生日）。
- 重构 `/R6 -h` 帮助：默认只显示常用指令，`/R6 -h all` 查看全部，`/R6 -h <指令>` 查看单条详情。
- 优化 401 / 404 / 429 / 503 错误提示，透出服务端错误码与建议重试时间。
- 移除未使用的 `beautifulsoup4`、`pyyaml` 依赖。

### v1.0.0

- 首个 AstrBot 移植版本。

## 致谢

- [nonebot-plugin-R6States](https://github.com/Siornya/nonebot-plugin-R6States)：原项目与数据结构参考。
- [R6Data / Arenyze](https://r6.arenyze.com/)：玩家战绩、百科与在线数据。
- [PandaScore](https://www.pandascore.co/)：电竞赛事数据。

## 支持与反馈

- 作者主页：[Bilibili](https://space.bilibili.com/290347024)
- 项目仓库：[GitHub](https://github.com/Diekeng/astrbot_plugin_r6states)

## License

[AGPL-3.0](LICENSE)

本项目为第三方工具，与 Ubisoft 无关；Rainbow Six Siege 及相关素材归 Ubisoft 所有。
