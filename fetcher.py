import httpx
import asyncio

async def fetch_r6data(player_id: str, api_key: str, data_type: str, platform: str = "uplay") -> dict:
    url = "https://api.r6data.eu/api/stats"
    params = {
        "type": data_type,
        "nameOnPlatform": player_id,
        "platformType": platform,
    }
    if data_type in ["stats", "operatorStats", "seasonalStats"]:
        params["platform_families"] = "pc"

    if not api_key:
        return {"error": "未设置 API Key喵"}
    headers = {"api-key": api_key, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e)}

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
    from urllib.parse import quote
    
    if not api_key:
        return {"error": "未配置 Pandascore API Key"}
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    async def _fetch(url: str):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                return resp.json()
        except:
            return None

    q_lower = query.lower()
    search_query = query
    
    # 强制赛区匹配优先
    if q_lower in LEAGUE_ALIASES:
        # ... stay as is ...
        real_name = LEAGUE_ALIASES[q_lower]
        url = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(real_name)}"
        leagues = await _fetch(url)
        if leagues:
            l_id = leagues[0]["id"]
            l_name = leagues[0]["name"]
            url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
            matches = await _fetch(url_matches)
            return {"type": "league", "name": l_name, "matches": matches or []}
            
    # 检查队伍别名
    if q_lower in TEAM_ALIASES:
        search_query = TEAM_ALIASES[q_lower]
            
    # 搜索队伍
    url_teams = f"https://api.pandascore.co/r6siege/teams?search[name]={quote(search_query)}"
    teams = await _fetch(url_teams)
    
    if not teams:
        # 尝试按缩写搜 (acronym)
        url_teams_acronym = f"https://api.pandascore.co/r6siege/teams?search[acronym]={quote(search_query)}"
        teams = await _fetch(url_teams_acronym)
        
    if teams:
        t_id = teams[0]["id"]
        t_name = teams[0]["name"]
        url_matches = f"https://api.pandascore.co/teams/{t_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches)
        return {"type": "team", "name": t_name, "matches": matches or []}
        
    # 如果作为队伍搜不到，再作为普通赛区搜一遍
    url_leagues = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(search_query)}"
    leagues = await _fetch(url_leagues)
    if leagues:
        l_id = leagues[0]["id"]
        l_name = leagues[0]["name"]
        url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches)
        return {"type": "league", "name": l_name, "matches": matches or []}
        
    return {"error": f"找不到名称匹配 '{query}' 的队伍或赛区。"}
