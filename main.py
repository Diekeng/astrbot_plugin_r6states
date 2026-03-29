import asyncio
import argparse
import shlex
from typing import List

from .parser import parse_overview
from .formatter import format_overview

R6_OUTPUT_MODE = "TEXT"
R6_ANALYSE = False


async def query_player_overview(player_id: str, full_mode: bool) -> str:
    """
    原理：异步调用数据解析和格式化函数。
    作用：获取并返回玩家数据的字符串结果，捕获查询过程中的异常。
    """
    try:
        message = format_overview(await parse_overview(player_id), full_mode)
        return f"🎯 {player_id} 的所有 section:\n{message}"
    except Exception as e:
        return f"❌ 查询玩家 {player_id} 失败，可能是由于ID错误或网络延迟: {e}"


def create_parser():
    """
    配置命令行参数解析器，复刻 NoneBot 的 ArgumentParser。
    """
    parser = argparse.ArgumentParser(prog="R6", add_help=False)
    parser.add_argument("-g", "--group", action="store_true")
    parser.add_argument("ids", nargs="*")
    parser.add_argument("-m", "--map")
    parser.add_argument("-f", "--full", action="store_true")
    return parser


async def handle_r6_command(args_list: List[str]):
    parser = create_parser()
    try:
        args = parser.parse_args(args_list)
    except SystemExit:
        print("参数解析错误。用法: R6 [-g] [-f] [-m MAP] [ids...]")
        return

    ids = args.ids
    is_group = args.group
    full_mode = args.full

    # 逻辑校验
    if not ids:
        print("一个id都不给是何意味？")
        return

    if is_group:
        if len(ids) > 5:
            print("一次开那么多是何意味？")
            return
        for player_id in ids:
            print(await query_player_overview(player_id, full_mode))
        print("全开了喵！")
    else:
        if len(ids) != 1:
            print("何意味")
            return
        print(await query_player_overview(ids[0], full_mode))


async def main():
    print("=== R6 查询工具 (控制台版) ===")
    print("输入 '/R6 help' 查看帮助，输入 'exit' 退出程序。")

    while True:
        try:
            # 获取用户输入
            user_input = input("\n> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "退出"]:
                break

            # 处理 help
            if user_input.lower() in ["/r6 help", "r6 help"]:
                print("/R6 [options] <id1> <id2> ...\n"
                      "-g, --group    开启组队模式 (最多5个)\n"
                      "-m, --map      指定地图\n"
                      "-f, --full     完整数据")
                continue

            # 处理 R6 指令
            if user_input.lower().startswith(("/r6", "r6")):
                # 使用 shlex.split 处理带空格的参数
                parts = shlex.split(user_input)
                # 移除开头的 '/r6' 或 'r6'
                await handle_r6_command(parts[1:])

            else:
                print("未知指令，请输入 /R6 help")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
