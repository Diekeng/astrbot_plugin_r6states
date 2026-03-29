from typing import List, Dict, Any, Optional
from datetime import datetime

MAP_TRANSLATIONS = {
    "house": "芝加哥豪宅",
    "oregon": "俄勒冈乡间屋宅",
    "hereford base": "赫里福基地",
    "hereford": "赫里福基地",
    "club house": "俱乐部",
    "clubhouse": "俱乐部",
    "presidential plane": "总统专机",
    "plane": "总统专机",
    "consulate": "领事馆",
    "bank": "银行",
    "kanal": "运河",
    "chalet": "木屋",
    "kafe dostoyevsky": "杜斯妥也夫斯基咖啡馆",
    "kafe": "杜斯妥也夫斯基咖啡馆",
    "yacht": "游艇",
    "border": "边境",
    "favela": "贫民窟",
    "skyscraper": "摩天大楼",
    "bartlett university": "巴特雷特大学",
    "bartlett": "巴特雷特大学",
    "coastline": "海岸线",
    "theme park": "主题乐园",
    "themepark": "主题乐园",
    "tower": "塔楼",
    "villa": "庄园",
    "fortress": "要塞",
    "outback": "荒漠服务站",
    "emerald plains": "翡翠原",
    "emeraldplains": "翡翠原",
    "close quarter": "近距离战斗",
    "closequarter": "近距离战斗",
    "stadium bravo": "B号竞技场",
    "stadiumbravo": "B号竞技场",
    "nighthaven labs": "永夜安港实验室",
    "nighthavenlabs": "永夜安港实验室",
    "lair": "虎穴狼巢",
    "stadium alpha": "竞技场2020",
    "stadiumalpha": "竞技场2020",
}

# 逆向映射：从中文名映射回英文名供 API 查询
REVERSE_MAP_TRANSLATIONS = {v: k for k, v in MAP_TRANSLATIONS.items()}
# 补充一些可能的简短中文输入
REVERSE_MAP_TRANSLATIONS.update({
    "豪宅": "house",
    "俄勒冈": "oregon",
    "咖啡馆": "kafe",
    "实验室": "nighthavenlabs",
    "竞技场": "stadiumbravo",
    "翡翠原": "emeraldplains",
    "咖啡厅": "kafe",
})

def translate_map_query(query: str) -> str:
    """如果输入是中文地图名，翻译成英文以供 API 查询"""
    q = query.strip()
    return REVERSE_MAP_TRANSLATIONS.get(q, query)

def _find_exact(data: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
    if not data: return None
    q = query.lower().strip()
    for item in data:
        if item.get("name", "").lower() == q or item.get("safename", "").lower() == q:
            return item
    return data[0]

def format_operator_info(data: List[Dict[str, Any]], query: str = "") -> str:
    if not data or "error" in data:
        return f"❌ 未找到该干员信息。" if not data else f"❌ 错误: {data.get('error')}"
    
    op = _find_exact(data, query)
    
    roles = op.get('roles', [])
    if isinstance(roles, list):
        roles_str = ", ".join(roles)
    else:
        roles_str = str(roles)

    res = [
        f"👤 干员百科: {op.get('name')} ({op.get('realname', '机密')})",
        f"组织: {op.get('unit', '未知')} | 国籍: {op.get('country_code', '未知')}",
        f"属性: 速度 {op.get('speed', '?')} | 生命值 {op.get('health', '?')}",
        f"干员定位: {roles_str}",
        f"阵营: {op.get('side', '?').replace('attacker', '进攻方').replace('defender', '防守方').capitalize()}",
        f"赛季引入: {op.get('season_introduced', '基础干员')}",
        "",
        f"📜 背景传记:\n{op.get('bio', '暂无背景介绍数据。')[:300]}...",
        "",
        "💡 提示: 更多详情可咨询机器人或查阅官网。"
    ]
    return "\n".join(res)

def format_weapon_info(data: List[Dict[str, Any]], query: str = "") -> str:
    if not data or "error" in data:
        return "❌ 未找到该武器信息。"
    
    w = _find_exact(data, query)
    
    ops = w.get('operators', "")
    if isinstance(ops, str):
        ops_str = ops.replace(';', ', ')
    elif isinstance(ops, list):
        ops_str = ", ".join(ops)
    else:
        ops_str = str(ops)

    res = [
        f"🔫 武器百科: {w.get('name')}",
        f"类型: {w.get('type', '未知')}",
        f"伤害: {w.get('stats_damage') or w.get('damage', '未知')} | 射速: {w.get('stats_firerate') or w.get('fire_rate', '未知')}",
        f"弹匣容量: {w.get('stats_ammo') or w.get('capacity', '未知')}",
        f"支持干员: {ops_str[:150]}..." if ops_str else "暂无支持干员列表。"
    ]
    return "\n".join(res)

def format_map_info(data: List[Dict[str, Any]], query: str = "") -> str:
    if not data or "error" in data:
        return "❌ 未找到该地图信息。"
    
    m = _find_exact(data, query)
    m_name = m.get('name', '')
    m_name_cn = MAP_TRANSLATIONS.get(m_name.lower(), m_name)

    res = [
        f"🗺️ 地图百科: {m_name_cn} ({m_name})",
        f"所在地: {m.get('location', '未知')}",
        f"发布日期: {m.get('releaseDate', '未知')}",
        f"包含模式: {m.get('playlists', '未知')}",
        f"重做赛季: {m.get('mapReworked', '原版')}"
    ]
    return "\n".join(res)

def format_game_stats(data: Dict[str, Any]) -> str:
    if "error" in data:
        return f"❌ 无法获取在线人数: {data['error']}"
    
    cross = data.get("crossPlatform", {})
    steam = data.get("steam", {})
    uplay = data.get("ubisoft", {})
    
    res = [
        "🌐 R6S 实时在线统计",
        f"总注册用户: {cross.get('totalRegistered', '未知')}",
        f"月活跃用户: {cross.get('monthlyActive', '未知')}",
        "",
        "🔥 当前在线估算:",
        f"Steam: {steam.get('concurrent', '未知')}",
        f"Ubisoft Connect: {uplay.get('onlineEstimate', '未知')}",
        "",
        "📱 分平台活跃:",
        f"PC: {cross.get('platforms', {}).get('pc', '未知')}",
        f"PlayStation: {cross.get('platforms', {}).get('playstation', '未知')}",
        f"Xbox: {cross.get('platforms', {}).get('xbox', '未知')}",
        "",
        f"更新时间: {data.get('lastUpdated', '刚刚')}"
    ]
    return "\n".join(res)

def format_seasons_info(data: List[Dict[str, Any]]) -> str:
    if not data: return "❌ 未找到赛季信息。"
    s = data[0]
    return f"📅 赛季信息: {s.get('name')} ({s.get('code')})\n引入干员: {', '.join(s.get('operators', []))}\n引入地图: {s.get('map', '无')}"
