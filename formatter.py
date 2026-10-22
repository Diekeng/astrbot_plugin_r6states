from typing import Dict
from datetime import datetime

# 新版 API 的 board_id（旧版还有 living_game_mode）
BOARD_NAMES = {
    "ranked": "排位",
    "standard": "标准",
    "casual": "休闲",
    "living_game_mode": "非排",
    "event": "活动",
    "warmup": "热身",
}

def clean_number(s: str) -> str:
    return s.replace(',', '')

def calculate_kd(kills, deaths):
    if deaths == 0: return float(kills)
    return round(kills / deaths, 2)

def calculate_winrate(wins, losses):
    total = wins + losses
    if total == 0: return 0.0
    return round((wins / total) * 100, 2)

def _top_operators(ops_data: dict, limit: int = 3):
    """返回 [(干员名, 局数, 胜率)]，兼容新版扁平数组与旧版 split 结构"""
    if not isinstance(ops_data, dict):
        return []

    # 新版：operators.operators[]，字段为 roundsPlayed / winPercent / wins / losses
    entries = (ops_data.get("operators") or {}).get("operators") or []
    if isinstance(entries, list) and entries:
        ranked = sorted(entries, key=lambda o: o.get("roundsPlayed") or 0, reverse=True)
        result = []
        for op in ranked:
            played = op.get("roundsPlayed") or 0
            if played <= 0:
                continue
            wr = op.get("winPercent")
            if wr is None:
                wr = calculate_winrate(op.get("wins", 0), op.get("losses", 0))
            result.append((op.get("operator", "Unknown"), played, wr))
            if len(result) >= limit:
                break
        return result

    # 旧版兼容：split.pc.playlists.*.operators.*.rounds
    operator_plays = {}
    split_data = ops_data.get("split", {})
    if isinstance(split_data, dict):
        playlists = split_data.get("pc", {}).get("playlists", {})
        if isinstance(playlists, dict):
            for p_data in playlists.values():
                if not isinstance(p_data, dict):
                    continue
                ops = p_data.get("operators", {})
                if not isinstance(ops, dict):
                    continue
                for op_info in ops.values():
                    if not isinstance(op_info, dict):
                        continue
                    name = op_info.get("operator", "Unknown")
                    rounds = op_info.get("rounds", {})
                    played = rounds.get("seasonal", {}).get("played", 0)
                    won = rounds.get("seasonal", {}).get("won", 0)
                    if played == 0:
                        played = rounds.get("lifetime", {}).get("played", 0)
                        won = rounds.get("lifetime", {}).get("won", 0)
                    operator_plays.setdefault(name, {"played": 0, "won": 0})
                    operator_plays[name]["played"] += played
                    operator_plays[name]["won"] += won

    sorted_ops = sorted(operator_plays.items(), key=lambda x: x[1]["played"], reverse=True)
    return [
        (name, plays["played"], calculate_winrate(plays["won"], plays["played"] - plays["won"]))
        for name, plays in sorted_ops if plays["played"] > 0
    ][:limit]

def get_rank_name(rank_id: int) -> str:
    if rank_id == 0: return "Unranked"
    ranks = [
        "Copper 5", "Copper 4", "Copper 3", "Copper 2", "Copper 1",
        "Bronze 5", "Bronze 4", "Bronze 3", "Bronze 2", "Bronze 1",
        "Silver 5", "Silver 4", "Silver 3", "Silver 2", "Silver 1",
        "Gold 5", "Gold 4", "Gold 3", "Gold 2", "Gold 1",
        "Platinum 5", "Platinum 4", "Platinum 3", "Platinum 2", "Platinum 1",
        "Emerald 5", "Emerald 4", "Emerald 3", "Emerald 2", "Emerald 1",
        "Diamond 5", "Diamond 4", "Diamond 3", "Diamond 2", "Diamond 1",
        "Champion"
    ]
    if 1 <= rank_id <= len(ranks):
        return ranks[rank_id - 1]
    return f"Rank {rank_id}"

def format_new_overview(player_id: str, stats_data: dict, ops_data: dict) -> str:
    res = [f"🎯 {player_id} 个人分析面板喵\n"]
    
    # 1. 本赛季数据
    res.append("📊 [本赛季数据]")
    res.append(f"{'模式':<12} | {'KD':<5} | {'胜率':<5} | {'击杀/死亡':<10} | {'场次'}")
    
    max_rank = 0
    max_rp = 0
    curr_rank = 0
    curr_rp = 0
    season_id = "未知"

    # 新版 API 把战绩放在 profile["stats"] 下，同时兼容旧结构
    stats_root = stats_data.get("stats")
    if not isinstance(stats_root, dict):
        stats_root = stats_data
    profiles = stats_root.get("platform_families_full_profiles") or []
    if isinstance(profiles, list) and len(profiles) > 0:
        boards = profiles[0].get("board_ids_full_profiles", [])
        
        for board in boards:
            b_id = board.get("board_id", "")
            name = BOARD_NAMES.get(b_id)
            if not name:
                continue

            inner_profiles = board.get("full_profiles", [])
            if not inner_profiles:
                continue

            fp = inner_profiles[0]
            prof = fp.get("profile", {})
            if b_id == "ranked":
                max_rank = prof.get("max_rank", 0)
                max_rp = prof.get("max_rank_points", 0)
                curr_rank = prof.get("rank", 0)
                curr_rp = prof.get("rank_points", 0)
                # 新结构里 season_id 在档案条目上，不在 profile 内
                season_id = fp.get("season_id") or prof.get("season_id", "未知")

            stats = fp.get("season_statistics", {})
            k = stats.get("kills", 0)
            d = stats.get("deaths", 0)
            w = stats.get("match_outcomes", {}).get("wins", 0)
            l = stats.get("match_outcomes", {}).get("losses", 0)
            a = stats.get("match_outcomes", {}).get("abandons", 0)
            
            kd = calculate_kd(k, d)
            wr = calculate_winrate(w, l)
            matches = w + l + a
            
            res.append(f"{name:<12} | {kd:<5} | {wr:<4}% | {k}/{d:<6} | {matches}")
    else:
        res.append("未获取到本赛季统计数据。")
        
    res.append("")
    
    # 2. 本赛季段位记录
    res.append(f"🎖️ [排位记录 (Season {season_id})]")
    if max_rank > 0 or max_rp > 0:
        res.append(f"👑 本赛季最高: {get_rank_name(max_rank)} ({max_rp} RP)")
        res.append(f"当前排位: {get_rank_name(curr_rank)} ({curr_rp} RP)")
    else:
        res.append("未获取到本赛季有效排位记录。")
        
    res.append("")
    
    # 3. 最常用的干员
    res.append("🔫 [生涯最常用干员]")

    top_ops = _top_operators(ops_data)
    if top_ops:
        for op_name, played, wr in top_ops:
            res.append(f"- {op_name}: {played} 局 (胜率 {wr}%)")
    else:
        res.append("本赛季无相关统计干员数据喵。")

    return "\n".join(res)

def format_match_history(player_id: str, sea_data: dict) -> str:
    if not isinstance(sea_data, dict) or "error" in sea_data:
        return f"❌ 获取 {player_id} 变动记录失败: {sea_data.get('error') if isinstance(sea_data, dict) else '未知数据结构'}"
    
    data_root = sea_data.get("data")
    if not isinstance(data_root, dict):
        data_root = {}
    history = (data_root.get("history") or {}).get("data") or []
    if not history:
        # 兼容 profile 接口把 history 放在顶层的情况
        history = (sea_data.get("history") or {}).get("data") or []
    if not history:
        return f"📅 玩家 {player_id} 本赛季暂无排位变动记录。"
    
    res = [f"📊 {player_id} 最近比赛记录 (Rank Points)"]
    
    # 我们展示最近的 3 次变动 (需要 4 个数据点来计算 3 个差值)
    count = 0
    for i in range(len(history) - 1):
        if count >= 3: break
        
        curr = history[i]
        prev = history[i+1]
        
        if not isinstance(curr, list) or len(curr) < 2 or not isinstance(prev, list) or len(prev) < 2:
            continue

        t_str = curr[0] # ISO time
        try:
            dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
            display_time = dt.strftime("%m-%d %H:%M")
        except (ValueError, TypeError):
            display_time = str(t_str)[:16]
            
        curr_obj = curr[1]
        prev_obj = prev[1]
        if not isinstance(curr_obj, dict) or not isinstance(prev_obj, dict):
            continue

        curr_val = curr_obj.get("value", 0)
        prev_val = prev_obj.get("value", 0)
        diff = curr_val - prev_val
        
        rank_name = curr_obj.get("metadata", {}).get("rank", "Unknown")
        result_icon = "📈 胜" if diff > 0 else "📉 负" if diff < 0 else "➖ 平/未变"
        
        res.append(f"{count+1}. {display_time} | {result_icon} ({diff:+} RP) | {rank_name} [{curr_val} RP]")
        count += 1
        
    if count == 0:
        res.append("暂无足够的数据点来对比胜负变动。")
        
    return "\n".join(res)

