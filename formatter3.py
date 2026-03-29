from datetime import datetime

def format_pandascore_matches(data: dict) -> str:
    if not isinstance(data, dict):
        return "❌ 赛事数据返回格式异常。"
    if "error" in data:
        return f"❌ {data['error']}"
        
    t_type = "战队" if data.get("type") == "team" else "赛区"
    name = data.get("name", "Unknown")
    matches = data.get("matches", [])
    
    if not matches or not isinstance(matches, list):
        return f"🎮 找到 {t_type} '{name}'，但近期没有可用的比赛安排或比分。"
        
    res = [f"🎮 【{name}】 近期 R6S 赛事 (展示前 {len(matches)} 场):", ""]
    
    for m in matches:
        if not isinstance(m, dict): continue
        m_name = m.get("name", "Unknown Match")
        status = m.get("status", "unknown")
        
        league = m.get("league", {})
        league_name = league.get("name", "") if isinstance(league, dict) else ""
        
        serie = m.get("serie", {})
        serie_name = serie.get("name", "") if isinstance(serie, dict) else ""
        
        tourn = m.get("tournament", {})
        tourn_name = tourn.get("name", "") if isinstance(tourn, dict) else ""
        
        league_info = f"{league_name}"
        if serie_name: league_info += f" - {serie_name}"
        if tourn_name: league_info += f" - {tourn_name}"
        
        begin_at = m.get("begin_at")
        
        # Parse time
        time_str = "未知时间"
        if begin_at:
            try:
                dt = datetime.fromisoformat(str(begin_at).replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = str(begin_at)[:16]
                
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
        if status in ["finished", "running"] and isinstance(results, list) and results:
            team_names = {}
            for op in m.get("opponents", []):
                if not isinstance(op, dict): continue
                t = op.get("opponent", {})
                if isinstance(t, dict):
                    team_names[t.get("id")] = t.get("name", "Unknown")
                
            score_list = []
            for r in results:
                if not isinstance(r, dict): continue
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
