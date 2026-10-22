import argparse
import shlex
import asyncio

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

from .fetcher import fetch_player_profile, fetch_player_operators, fetch_pandascore_matches, fetch_player_seasonal_stats, fetch_r6_wiki, fetch_game_online_stats
from .formatter import format_new_overview, format_match_history
from .formatter3 import format_pandascore_matches
from . import formatter_wiki as wiki_fmt

HELP_TEXT = (
    "🎮 彩虹六号 · 常用指令\n"
    "\n"
    "/r6 <玩家ID>      查战绩\n"
    "/r6h <玩家ID>     查排位变动\n"
    "/r6op <干员>      查干员百科\n"
    "\n"
    "📖 全部指令：/r6 -h all\n"
    "🔍 单条详情：/r6 -h r6h\n"
    "💬 也可以直接说：“查一下 MacieJay 的战绩”\n"
    "🔑 Key 申请：https://r6.arenyze.com/"
)

HELP_ALL = (
    "🎮 彩虹六号 · 全部指令\n"
    "\n"
    "【战绩】\n"
    "/r6 <玩家ID>          赛季战绩概览\n"
    "/r6 -g <ID1> <ID2>…   批量查询，最多 5 人\n"
    "/r6h <玩家ID>         最近排位 RP 变动\n"
    "\n"
    "【百科】\n"
    "/r6op <干员>          属性、定位与背景\n"
    "/r6map <地图>         地图详情，支持中文\n"
    "/r6w <武器>           伤害、射速与配件\n"
    "/r6s                  全平台实时在线人数\n"
    "\n"
    "【赛事】\n"
    "/r6m <队伍/赛区>      近期赛程与比分\n"
    "赛区：EU/EML、NA/NAL、CN/CNL、BR、LATAM、\n"
    "      KR、JP、ASIA/APL、SAL、OCE、MENA\n"
    "\n"
    "【配置】\n"
    "/r6dapi <Key>         绑定 R6Data API Key\n"
    "\n"
    "🔍 单条详情：/r6 -h <指令>"
)

TOPIC_HELP = {
    "r6": "🔎 /r6 <玩家ID>\n查询排位/标准/休闲的 KD、胜率、场次、段位与常用干员。\n示例：/r6 MacieJay",
    "r6g": "🔎 /r6 -g <ID1> <ID2> …\n批量查询多名玩家，最多 5 人。\n示例：/r6 -g MacieJay Beaulo",
    "r6h": "🔎 /r6h <玩家ID>\n查看最近的排位 RP 增减记录（最近 3 次变动）。\n示例：/r6h MacieJay",
    "r6m": "🔎 /r6m <队伍名/赛区>\n查询战队或赛区最近 5 场比赛。\n示例：/r6m G2、/r6m NAL\n赛区：EU/EML、NA/NAL、CN/CNL、BR、LATAM、KR、JP、ASIA/APL、SAL、OCE、MENA",
    "r6op": "🔎 /r6op <干员名>\n查询干员属性、定位、组织与背景。\n示例：/r6op Ash",
    "r6map": "🔎 /r6map <地图名>\n查询地图详情，支持中文名。\n示例：/r6map 俄勒冈、/r6map Bank",
    "r6w": "🔎 /r6w <武器名>\n查询武器伤害、射速、弹匣与配件。\n示例：/r6w R4-C",
    "r6s": "🔎 /r6s\n查看全平台实时在线人数与注册用户统计。\n示例：/r6s",
    "r6dapi": "🔎 /r6dapi <Key>\n绑定 R6Data API Key，Key 有效期内无需重复绑定。\nKey 申请：https://r6.arenyze.com/（有效期约 1 个月）",
}

TOPIC_ALIASES = {
    "g": "r6g",
    "group": "r6g",
    "组队": "r6g",
    "批量": "r6g",
    "op": "r6op",
    "map": "r6map",
    "w": "r6w",
    "s": "r6s",
    "m": "r6m",
}


def help_for(topic: str = "") -> str:
    """按指令名返回详情；all/空 返回完整列表；未知指令回退到常用指令"""
    key = (topic or "").strip().lower().lstrip("/")
    key = TOPIC_ALIASES.get(key, key)
    if key in ("all", "全部", "help", "帮助"):
        return HELP_ALL
    if not key:
        return HELP_TEXT
    if key in TOPIC_HELP:
        return TOPIC_HELP[key]
    return f"没有找到「{topic}」这条指令。\n\n{HELP_TEXT}"


class R6StatesPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    def create_parser(self):
        parser = argparse.ArgumentParser(prog="R6", add_help=False)
        parser.add_argument("-g", "--group", action="store_true")
        parser.add_argument("ids", nargs="*")
        parser.add_argument("-h", "--help", action="store_true")
        return parser

    async def query_player_overview(self, player_id: str) -> str:
        try:
            api_key = self.config.get("api_key", "")
            
            # 新版 API：/v2/profile 一次返回战绩，干员数据走独立接口
            stats_task = fetch_player_profile(player_id, api_key)
            ops_task = fetch_player_operators(player_id, api_key)
            
            stats_data, ops_data = await asyncio.gather(stats_task, ops_task)
            
            if "error" in stats_data and stats_data["error"]:
                return f"获取 {player_id} 错误: {stats_data['error']}"
            return format_new_overview(player_id, stats_data, ops_data)
        except Exception as e:
            logger.error(f"查询玩家 {player_id} 失败: {type(e).__name__}: {e}")
            return f"❌ 查询玩家 {player_id} 失败，可能是由于ID错误、网络延迟或 API 维护中。"

    @filter.command("r6")
    async def r6_command(self, event: AstrMessageEvent, message: str = ""):
        '''查询 R6S 玩家战绩。用法：/r6 <玩家ID>；批量：/r6 -g <ID1> <ID2>；帮助：/r6 -h [指令|all]'''
        parser = self.create_parser()
        
        if message:
            args_list = shlex.split(message)
        else:
            parts = shlex.split(event.message_str)
            args_list = parts[1:] if len(parts) > 1 else []
            
        if not args_list:
            yield event.plain_result(HELP_TEXT)
            return

        try:
            parsed_args = parser.parse_args(args_list)
        except SystemExit:
            yield event.plain_result("参数解析错误喵。用法: /R6 [-g] [-h] [ids...]喵")
            return

        if parsed_args.help:
            topic = parsed_args.ids[0] if parsed_args.ids else ""
            yield event.plain_result(help_for(topic))
            return

        ids = parsed_args.ids
        is_group = parsed_args.group

        if not ids:
            yield event.plain_result("未提供ID喵，使用/R6 -h 查看用法喵")
            return

        if is_group:
            if len(ids) > 5:
                yield event.plain_result("组队模式最多只能查询5个ID喵")
                return
            tasks = [self.query_player_overview(idx) for idx in ids]
            results = await asyncio.gather(*tasks)
            for res in results:
                yield event.plain_result(res)
            yield event.plain_result("查询完毕喵！")
        else:
            if len(ids) != 1:
                yield event.plain_result("单人模式只能查询1个ID喵，多ID请使用 -g 参数喵：/R6 -g id1 id2")
                return
            res = await self.query_player_overview(ids[0])
            yield event.plain_result(res)

    @filter.command("r6dapi")
    async def set_api_key(self, event: AstrMessageEvent, message: str = ""):
        '''配置 R6Data API Key。用法：/r6dapi <Key>；Key 可在 https://r6.arenyze.com/ 获取'''
        key = message.strip()
        if not key:
            parts = event.message_str.split(maxsplit=1)
            if len(parts) > 1:
                key = parts[1].strip()
            
        if not key:
            yield event.plain_result("请在命令中输入 API Key喵")
            return
        
        self.config["api_key"] = key
        self.config.save_config()
        yield event.plain_result("✅ API Key 已更新，建议在 WebUI 固化配置以免重启失效喵")

    @filter.command("r6m")
    async def r6m_command(self, event: AstrMessageEvent, message: str = ""):
        '''查询 R6S 电竞赛程与比分。用法：/r6m <队伍名或赛区简称>'''
        query = message.strip()
        if not query:
            parts = event.message_str.split(maxsplit=1)
            if len(parts) > 1:
                query = parts[1].strip()
                
        if not query:
            yield event.plain_result("请在命令后输入队伍名 (如 G2) 或赛区简称 (如 EU, CNL)。用法: /R6M <队伍名/赛区>")
            return
            
        api_key = self.config.get("pandascore_api_key", "")
        if not api_key:
            yield event.plain_result("❌ 未配置 pandascore_api_key，请在 WebUI 或 _conf_schema.json 中配置。")
            return
            
        data = await fetch_pandascore_matches(query, api_key)
        res = format_pandascore_matches(data)
        yield event.plain_result(res)

    @filter.command("r6h")
    async def r6h_command(self, event: AstrMessageEvent, player_id: str):
        '''查询玩家最近排位 RP 变动。用法：/r6h <玩家ID>'''
        api_key = self.config.get("api_key", "")
        data = await fetch_player_seasonal_stats(player_id, api_key)
        yield event.plain_result(format_match_history(player_id, data))

    @filter.command("r6op")
    async def r6op_command(self, event: AstrMessageEvent, name: str):
        '''查询干员百科。用法：/r6op <干员名>'''
        api_key = self.config.get("api_key", "")
        data = await fetch_r6_wiki("operators", api_key, params={"name": name})
        yield event.plain_result(wiki_fmt.format_operator_info(data, name))

    @filter.command("r6map")
    async def r6map_command(self, event: AstrMessageEvent, name: str):
        '''查询地图百科。用法：/r6map <地图名>，支持中文名'''
        api_key = self.config.get("api_key", "")
        # 尝试将中文翻译回英文
        eng_name = wiki_fmt.translate_map_query(name)
        data = await fetch_r6_wiki("maps", api_key, params={"name": eng_name})
        yield event.plain_result(wiki_fmt.format_map_info(data, eng_name))

    @filter.command("r6w")
    async def r6w_command(self, event: AstrMessageEvent, name: str):
        '''查询武器数据。用法：/r6w <武器名>'''
        api_key = self.config.get("api_key", "")
        data = await fetch_r6_wiki("weapons", api_key, params={"name": name})
        yield event.plain_result(wiki_fmt.format_weapon_info(data, name))


    @filter.command("r6s")
    async def r6s_online_command(self, event: AstrMessageEvent):
        '''查询全平台实时在线人数。用法：/r6s'''
        api_key = self.config.get("api_key", "")
        data = await fetch_game_online_stats(api_key)
        yield event.plain_result(wiki_fmt.format_game_stats(data))

    @filter.llm_tool(name="query_r6_player_stats")

    async def query_r6_player_stats(self, event: AstrMessageEvent, player_id: str):
        '''查询获取彩虹六号(Rainbow Six Siege, R6S)玩家的最新战绩、当前排位分数以及最常用干员数据喵。

        Args:
            player_id(string): 玩家的育碧(Ubisoft)游戏ID
        '''
        res = await self.query_player_overview(player_id)
        yield event.plain_result(res)

    @filter.llm_tool(name="query_r6_esports_matches")
    async def query_r6_esports_matches(self, event: AstrMessageEvent, query: str):
        '''查询彩虹六号(Rainbow Six Siege, R6S)的电竞战队或赛区/联赛的近期比赛排期和比分结果。

        Args:
            query(string): 队伍名(如 G2, W7M) 或者是赛区简称(如 eu, cn, apl, na, Europe)
        '''
        api_key = self.config.get("pandascore_api_key", "")
        if not api_key:
            yield event.plain_result("❌ 未配置 pandascore_api_key。")
            return
        data = await fetch_pandascore_matches(query, api_key)
        res = format_pandascore_matches(data)
        yield event.plain_result(res)

    @filter.llm_tool(name="query_r6_operator_info")
    async def query_r6_operator_info(self, event: AstrMessageEvent, operator_name: str):
        '''获取彩虹六号(R6S)指定干员的详细百科信息，包括属性、背景组织、侧翼等。

        Args:
            operator_name(string): 干员名称(如 Ash, Jäger)
        '''
        api_key = self.config.get("api_key", "")
        data = await fetch_r6_wiki("operators", api_key, params={"name": operator_name})
        yield event.plain_result(wiki_fmt.format_operator_info(data, operator_name))


    @filter.llm_tool(name="query_r6_game_online_status")
    async def query_r6_game_online_status(self, event: AstrMessageEvent):
        '''查看彩虹六号当前全球各平台的实时在线人数和注册用户统计。'''
        api_key = self.config.get("api_key", "")
        data = await fetch_game_online_stats(api_key)
        yield event.plain_result(wiki_fmt.format_game_stats(data))

