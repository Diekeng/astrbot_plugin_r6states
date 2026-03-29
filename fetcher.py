import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from astrbot.api import logger

async def _fetch(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None) -> Any:
    """内部通用请求函数，提供统一的错误处理和日志记录"""
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError as e:
                logger.error(f"R6States API JSON 解析失败: {e}, URL: {url}")
                return {"error": "API 返回了非法的 JSON 数据结构"}
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        logger.error(f"R6States API 请求返回错误状态码: {status_code}, URL: {url}")
        if status_code in [401, 403]:
            return {"error": "API 密钥无效或权限被拒绝，请检查配置。"}
        return {"error": f"API 访问失败 (HTTP {status_code})"}
    except httpx.RequestError as e:
        logger.error(f"R6States 网络请求异常: {type(e).__name__}: {e}")
        return {"error": "网络连接超时或无法连接到 API 服务器，请稍后重试。"}
    except Exception as e:
        logger.error(f"R6States 发生非预期错误: {type(e).__name__}: {e}")
        return {"error": f"系统内部错误: {str(e)}"}

async def fetch_r6data(player_id: str, api_key: str, data_type: str, platform: str = "uplay") -> dict:
    if not api_key:
        return {"error": "未配置 R6Data API Key，请先使用 /R6DAPI <key> 设置。"}
        
    url = "https://api.r6data.eu/api/stats"
    params = {
        "type": data_type,
        "nameOnPlatform": player_id,
        "platformType": platform,
        "platform_families": "pc"
    }
    headers = {
        "api-key": api_key,
        "User-Agent": "AstrBot-R6States-Plugin/1.0"
    }
    res = await _fetch(url, headers, params)
    return res if isinstance(res, dict) else {"error": "API 返回数据格式异常", "raw": str(res)}

async def fetch_player_data(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    return await fetch_r6data(player_id, api_key, "operatorStats", platform)

async def fetch_player_stats(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    return await fetch_r6data(player_id, api_key, "stats", platform)

LEAGUE_ALIASES = {
    "eu": "Europe MENA League",
    "eml": "Europe MENA League",
    "na": "North America League",
    "nal": "North America League",
    "cn": "China",
    "cnl": "China",
    "br": "Brazil League",
    "latam": "LATAM League",
    "kr": "South Korea League",
    "jp": "Japan League",
    "asia": "Asia League",
    "apl": "Asia-Pacific League",
    "sal": "South America League",
    "sa": "South America League",
    "oce": "Oceania League",
    "mena": "MENA League"
}

TEAM_ALIASES = {
    "ag": "AllGamers",
    "all gamers": "AllGamers",
    "ase": "Attacking Soul Esports",
    "4am": "Four Angry Men",
    "kz": "Kingzone",
    "mq": "My Queen",
    "tec": "Titan Esports Club",
    "tyloo": "TYLOO",
    "wolvesy": "WolvesY",
    "wbg": "Weibo Gaming"
}

async def fetch_pandascore_matches(query: str, api_key: str) -> dict:
    if not api_key:
        return {"error": "未配置 Pandascore API Key，请在配置中填入。"}
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "AstrBot-R6States-Plugin/1.0"
    }

    q_lower = query.lower().strip()
    search_query = query
    
    # 强制赛区匹配优先
    if q_lower in LEAGUE_ALIASES:
        real_name = LEAGUE_ALIASES[q_lower]
        url = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(real_name)}"
        leagues = await _fetch(url, headers)
        if isinstance(leagues, list) and len(leagues) > 0:
            l_id = leagues[0].get("id")
            l_name = leagues[0].get("name", real_name)
            url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
            matches = await _fetch(url_matches, headers)
            return {"type": "league", "name": l_name, "matches": matches if isinstance(matches, list) else []}
            
    # 检查队伍别名
    if q_lower in TEAM_ALIASES:
        search_query = TEAM_ALIASES[q_lower]
            
    # 搜索队伍
    url_teams = f"https://api.pandascore.co/r6siege/teams?search[name]={quote(search_query)}"
    teams = await _fetch(url_teams, headers)
    
    if isinstance(teams, dict) and "error" in teams:
        return teams 

    if not isinstance(teams, list) or len(teams) == 0:
        # 尝试按缩写搜 (acronym)
        url_teams_acronym = f"https://api.pandascore.co/r6siege/teams?search[acronym]={quote(search_query)}"
        teams = await _fetch(url_teams_acronym, headers)
        
    if isinstance(teams, list) and len(teams) > 0:
        team_best = teams[0]
        t_id = team_best.get("id")
        t_name = team_best.get("name", search_query)
        url_matches = f"https://api.pandascore.co/teams/{t_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches, headers)
        return {"type": "team", "name": t_name, "matches": matches if isinstance(matches, list) else []}
        
    # 如果作为队伍搜不到，再作为普通赛区关键词搜一遍
    url_leagues = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(search_query)}"
    leagues = await _fetch(url_leagues, headers)
    if isinstance(leagues, list) and len(leagues) > 0:
        league_best = leagues[0]
        l_id = league_best.get("id")
        l_name = league_best.get("name", search_query)
        url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches, headers)
        return {"type": "league", "name": l_name, "matches": matches if isinstance(matches, list) else []}
        
    return {"error": f"找不到名称匹配 '{query}' 的队伍或赛区，请检查拼写。"}

async def fetch_player_seasonal_stats(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    return await fetch_r6data(player_id, api_key, "seasonalStats", platform)

async def fetch_r6_wiki(endpoint: str, api_key: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """通用 Wiki 数据抓取转发器"""
    url = f"https://api.r6data.eu/api/{endpoint.lstrip('/')}"
    headers = {
        "api-key": api_key, 
        "Content-Type": "application/json",
        "User-Agent": "AstrBot-R6States-Plugin/1.0"
    }
    return await _fetch(url, headers, params)

async def fetch_game_online_stats(api_key: str) -> dict:
    """获取全平台实时在线人数"""
    res = await fetch_r6_wiki("stats", api_key, params={"type": "gameStats"})
    return res if isinstance(res, dict) else {"error": "在线统计数据解析异常"}

