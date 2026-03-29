import argparse
import shlex
import asyncio
from typing import List

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger, AstrBotConfig

from .fetcher import fetch_player_data, fetch_player_stats, fetch_pandascore_matches
from .formatter import format_new_overview
from .formatter2 import format_operator_stats
from .formatter3 import format_pandascore_matches

class R6StatesPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    def create_parser(self):
        parser = argparse.ArgumentParser(prog="R6", add_help=False)
        parser.add_argument("-g", "--group", action="store_true")
        parser.add_argument("ids", nargs="*")
        parser.add_argument("-m", "--map")
        parser.add_argument("-f", "--full", action="store_true")
        parser.add_argument("-h", "--help", action="store_true")
        return parser

    async def query_player_overview(self, player_id: str) -> str:
        try:
            api_key = self.config.get("api_key", "")
            
            # Fetch parallel data pure API
            stats_task = fetch_player_stats(player_id, api_key)
            ops_task = fetch_player_data(player_id, api_key)
            
            stats_data, ops_data = await asyncio.gather(stats_task, ops_task)
            
            if "error" in stats_data and stats_data["error"]:
                return f"获取 {player_id} 错误喵: {stats_data['error']}"
                
            return format_new_overview(player_id, stats_data, ops_data)
        except Exception as e:
            logger.error(f"查询玩家 {player_id} 出错喵: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 查询玩家 {player_id} 失败喵，可能是由于ID错误或网络延迟喵: {e}"

    @filter.command("R6")
    async def r6_command(self, event: AstrMessageEvent, message: str = ""):
        '''查询 R6S 战绩: /R6 [-g] [-h] <id1> <id2>'''
        parser = self.create_parser()
        
        if message:
            args_list = shlex.split(message)
        else:
            parts = shlex.split(event.message_str)
            args_list = parts[1:] if len(parts) > 1 else []
            
        if not args_list:
            yield event.plain_result(
                "/R6 [options] <id1> <id2> ...\n"
                "-g, --group    开启组队模式喵 (最多5个喵)\n"
                "-m, --map      指定地图喵\n"
                "-h, --help     查看完整帮助喵\n"
                "/R6M <队伍名/赛区>   查询赛区排期与比分\n"
            )
            return

        try:
            parsed_args = parser.parse_args(args_list)
        except SystemExit:
            yield event.plain_result("参数解析错误喵。用法: /R6 [-g] [-h] [ids...]喵")
            return

        if parsed_args.help:
            yield event.plain_result(
                "/R6 [options] <id1> <id2> ...\n"
                "-g, --group    开启组队模式 (最多5个)喵\n"
                "-m, --map      指定地图喵\n"
                "-h, --help     查看完整帮助喵\n"
                "/R6M <队伍名/赛区>   查询赛区排期与比分喵\n"
            )
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
            for idx in ids:
                res = await self.query_player_overview(idx)
                yield event.plain_result(res)
            yield event.plain_result("全开了喵！")
        else:
            if len(ids) != 1:
                yield event.plain_result("单人模式只能查询1个ID喵，多ID请使用 -g 参数喵：/R6 -g id1 id2")
                return
            res = await self.query_player_overview(ids[0])
            yield event.plain_result(res)

    @filter.command("R6DAPI")
    async def set_api_key(self, event: AstrMessageEvent, message: str = ""):
        '''配置 R6Data API Key (管理员或直接在WebUI配置喵)'''
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

    @filter.command("R6M")
    async def r6m_command(self, event: AstrMessageEvent, message: str = ""):
        '''查询 R6S 赛事: /R6M <队伍名或赛区简称>'''
        query = message.strip()
        if not query:
            parts = event.message_str.split(maxsplit=1)
            if len(parts) > 1:
                query = parts[1].strip()
                
        if not query:
            yield event.plain_result("请在命令后输入队伍名 (如 G2) 或赛区简称 (如 EU, CNL)。用法: /R6M <队伍名/赛区>")
            return
            
        api_key = self.config.get("pandascore_api_key", "fWWv_p-nYL6Akk1JRol5IS8gZeJvvEvWHhLVRKYsYXlxI1Jn5F0")
        data = await fetch_pandascore_matches(query, api_key)
        res = format_pandascore_matches(data)
        yield event.plain_result(res)

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
        api_key = self.config.get("pandascore_api_key", "fWWv_p-nYL6Akk1JRol5IS8gZeJvvEvWHhLVRKYsYXlxI1Jn5F0")
        data = await fetch_pandascore_matches(query, api_key)
        res = format_pandascore_matches(data)
        yield event.plain_result(res)
