# AstrBot-Plugin-R6States

本项目是基于 [nonebot-plugin-R6States](https://github.com/Siornya/nonebot-plugin-R6States) 的 AstrBot 框架移植强化版。专为 AstrBot 生态与现代网络响应需求进行了深度重构与优化。

## Features | 核心特性

* **删除了爬虫**
    完全移除了原版的 Playwright 与 BeautifulSoup 抓取逻辑。所有玩家数据（战绩、胜率、最高段位、常用主力干员等）均由原生高并发 API 驱动，响应时间缩短至毫秒级。
* **支持LLM调用函数查询**
    原生接入 AstrBot 的 Function Calling 能力。您或您的群友可以直接使用自然语言（例如：“查一下某人的战绩”或“某支战队最近的比赛是什么情况”），AI 将自动调用内置工具并生成易读的回复。
* **电竞赛程与比分追踪**
    除个人战绩外，额外接入了职业电竞赛事的工具数据库。通过指令或大语言模型的自然交流，可随时跟踪各大赛区与参赛战队的最新赛程与实时比分。

---

## Prerequisites | 准备工作

为了正常使用本插件的所有功能，您需要提前申请相关的第三方 API 密钥（均为免费服务）：

1.  **R6Data API Key (必需，用于玩家战绩查询)**
    * 前往 [R6Data API](https://r6data.eu/) 注册并获取免费 API Key。
2.  **PandaScore API Key (可选，用于赛事数据查询)**
    * 前往 [PandaScore](https://www.pandascore.co/) 注册开发者账号并获取免费 Token。
    * > **注：** 若不配置此项，电竞查询功能将不可用，但不影响常规玩家战绩查询。

---

## Configuration | 配置指南

获取密钥后，您可以通过以下两种方式完成插件配置：

**方式一：WebUI 配置（推荐）**
进入 AstrBot 的 WebUI 插件配置中心，找到本插件并分别填入 `api_key` (R6Data) 和 `pandascore_api_key` (PandaScore)。

**方式二：指令快速绑定**
直接向机器人发送以下指令完成 R6Data 密钥的快速绑定：
```bash
/R6DAPI <您的密钥>
```

---

## Usage | 指令列表

除了使用自然语言与 AI 直接交流外，您也可以使用以下精确指令触发功能：

### 玩家战绩查询 (Player Stats)

| 指令 | 参数说明 | 示例 |
| :--- | :--- | :--- |
| `/R6` | `<玩家ID>`：查询单一玩家的本赛季详细战绩。 | `/R6 MacieJay` |
| `/R6 -g` | `<玩家ID1> <ID2>...`：批量查询多名玩家数据（最多支持 5 个）。 | `/R6 -g playerA playerB` |
| `/R6 -h` | 打印相关的战绩查询全部分支选项与帮助信息。 | `/R6 -h` |
**注意：cn赛区还未开赛，无法查询到具体赛事信息，可以查询队伍,比如tyloo、kz、AllGamers等，建议使用全称**

### 职业赛事查询 (Esports Matches)

| 指令 | 参数说明 | 示例 |
| :--- | :--- | :--- |
| `/R6M` | `<队伍名>`：查询指定职业队伍近期的 5 场比赛赛程或具体比分。 | `/R6M G2` 或 `/R6M w7m` |
| `/R6M` | `<赛区简称>`：查询该联赛赛区的最新排位赛（支持 NAL, EU, CN, APL 等）。 | `/R6M NAL` |

```bash
    "eu": "Europe MENA League",
    "eml": "Europe MENA League",
    "na": "North America League",
    "nal": "North America League",
    "cn": "China",
    "cnl": "China",
    "br": "Brazil",
    "latam": "Latin America",
    "kr": "South Korea",
    "jp": "Japan",
    "asia": "Asia",
    "apl": "Asia-Pacific",
    "sal": "South America League",
    "sa": "South America League",
    "oce": "Oceania",
    "mena": "MENA"
```

> **💡 提示：** 强烈建议利用 AstrBot 的 AI 特性，直接以自然语言驱动以上功能，获得最佳的使用体验。

# Supports

- [AstrBot Repo](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot Plugin Development Docs (Chinese)](https://docs.astrbot.app/dev/star/plugin-new.html)
- [AstrBot Plugin Development Docs (English)](https://docs.astrbot.app/en/dev/star/plugin-new.html)
