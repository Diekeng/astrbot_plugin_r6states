from datetime import datetime

def format_pandascore_matches(data: dict) -> str:
    if "error" in data:
        return f"❌ {data['error']}"
        
    t_type = "战队" if data.get("type") == "team" else "赛区"
    name = data.get("name", "Unknown")
    matches = data.get("matches", [])
    
    if not matches:
        return f"🎮 找到 {t_type} '{name}'，但近期没有可用的比赛安排或比分。"
        
    res = [f"🎮 【{name}】 近期 R6S 赛事 (总计展示最新 {len(matches)} 场):", ""]
    
    for m in matches:
        m_name = m.get("name", "Unknown Match")
        status = m.get("status", "unknown")
        league_name = m.get("league", {}).get("name", "")
        serie_name = m.get("serie", {}).get("name", "")
        tourn_name = m.get("tournament", {}).get("name", "")
        
        league_info = f"{league_name}"
        if serie_name: league_info += f" - {serie_name}"
        if tourn_name: league_info += f" - {tourn_name}"
        
        begin_at = m.get("begin_at")
        
        # Parse time
        time_str = "未知时间"
        if begin_at:
            try:
                dt = datetime.fromisoformat(begin_at.replace("Z", "+00:00"))
                # Convert to local readable
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
                
        # Status mapping
        status_map = {
            "finished": "已结束",
            "running": "进行中 🔴",
            "not_started": "未开始 🕒",
            "canceled": "已取消 🚫",
            "postponed": "已延期"
        }
        s_cn = status_map.get(status, status)
        
        # Scores
        results = m.get("results", [])
        score_str = ""
        if status in ["finished", "running"] and results:
            # We need to map team IDs to names safely
            team_names = {}
            for op in m.get("opponents", []):
                t = op.get("opponent", {})
                team_names[t.get("id")] = t.get("name", "Unknown")
                
            score_list = []
            for r in results:
                t_id = r.get("team_id")
                sc = r.get("score")
                t_name = team_names.get(t_id, f"Team_{t_id}")
                score_list.append(f"{t_name} {sc}")
                
            score_str = " | ".join(score_list)
            
        line = f"🔹 [{league_info}] {m_name}\n   时间: {time_str} | 状态: {s_cn}"
        if score_str:
            line += f"\n   比分: {score_str}"
        res.append(line)
        res.append("")
        
    return "\n".join(res).strip()
