from typing import Dict, List

def clean_number(s: str) -> str:
    return s.replace(',', '')

def calculate_kd(kills, deaths):
    if deaths == 0: return float(kills)
    return round(kills / deaths, 2)

def calculate_winrate(wins, losses):
    total = wins + losses
    if total == 0: return 0.0
    return round((wins / total) * 100, 2)

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

    if "platform_families_full_profiles" in stats_data and stats_data["platform_families_full_profiles"]:
        boards = stats_data["platform_families_full_profiles"][0].get("board_ids_full_profiles", [])
        
        for board in boards:
            b_id = board.get("board_id", "")
            if b_id == "ranked":
                name = "排位"
                prof = board["full_profiles"][0].get("profile", {})
                max_rank = prof.get("max_rank", 0)
                max_rp = prof.get("max_rank_points", 0)
                curr_rank = prof.get("rank", 0)
                curr_rp = prof.get("rank_points", 0)
                season_id = prof.get("season_id", "未知")
            elif b_id == "standard":
                name = "快速"
            elif b_id == "living_game_mode":
                name = "非排"
            else:
                continue
                
            stats = board["full_profiles"][0].get("season_statistics", {})
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
    
    # 2. 本赛季段位记录 (无爬虫降级)
    res.append(f"🎖️ [排位记录 (Season {season_id})]")
    if max_rank > 0 or max_rp > 0:
        res.append(f"👑 本赛季最高: {get_rank_name(max_rank)} ({max_rp} RP)")
        res.append(f"当前排位: {get_rank_name(curr_rank)} ({curr_rp} RP)")
    else:
        res.append("未获取到本赛季有效排位记录。")
        
    res.append("")
    
    # 3. 近三个模式最常用的干员
    res.append("🔫 [本赛季或生涯最常用干员喵")
    operator_plays = {}
    
    if "split" in ops_data and "pc" in ops_data["split"]:
        playlists = ops_data["split"]["pc"]["playlists"]
        for p_name, p_data in playlists.items():
            if "operators" in p_data:
                for op_id, op_info in p_data["operators"].items():
                    name = op_info.get("operator", "Unknown")
                    # Try to get seasonal first, fallback to lifetime
                    played = op_info.get("rounds", {}).get("seasonal", {}).get("played", 0)
                    won = op_info.get("rounds", {}).get("seasonal", {}).get("won", 0)
                    
                    if played == 0:
                        played = op_info.get("rounds", {}).get("lifetime", {}).get("played", 0)
                        won = op_info.get("rounds", {}).get("lifetime", {}).get("won", 0)
                    
                    if name not in operator_plays:
                        operator_plays[name] = {"played": 0, "won": 0}
                        
                    if played:
                        operator_plays[name]["played"] += played
                    if won:
                        operator_plays[name]["won"] += won
                        
    # 取前三
    sorted_ops = sorted(operator_plays.items(), key=lambda x: x[1]["played"], reverse=True)
    top_ops = [op for op in sorted_ops if op[1]["played"] > 0][:3]
    
    if top_ops:
        for op in top_ops:
            w = op[1]["won"]
            p_count = op[1]["played"]
            wr = calculate_winrate(w, p_count - w)
            res.append(f"- {op[0]}: {p_count} 局 (胜率 {wr}%)")
    else:
        res.append("本赛季无相关统计干员数据喵。")

    return "\n".join(res)
