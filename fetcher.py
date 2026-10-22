import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from astrbot.api import logger

# 新版 R6Data 公共 API。旧地址 api.r6data.eu 已停用，站点迁移至 r6.arenyze.com
BASE_URL = "https://public-api.arenyze.com/r6/api"
APIKEY_HELP = "请前往 https://r6.arenyze.com/ 免费获取 Key（有效期约 1 个月），再用 /R6DAPI <key> 绑定。"

async def _fetch(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 20.0,
    auth_hint: str = "",
) -> Any:
    """内部通用请求函数，提供统一的错误处理和日志记录"""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
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

        # 尽量把服务端的错误码与提示透出，而不是只显示 HTTP 状态码
        detail = ""
        code = ""
        retry_after = e.response.headers.get("Retry-After")
        try:
            body = e.response.json()
            if isinstance(body, dict):
                code = str(body.get("code") or "")
                msg = body.get("message") or body.get("error")
                if msg:
                    detail = f"（{msg}）"
                retry_after = body.get("retryAfter") or retry_after
        except (ValueError, TypeError):
            pass

        if code == "STATS_UPSTREAM_THROTTLED":
            wait = _format_wait(retry_after)
            hint = f"服务端建议 {wait}后重试。" if wait else "请稍后重试。"
            return {"error": "上游统计服务暂时繁忙，" + hint}
        if status_code == 429:
            return {"error": "请求过于频繁，已触发 API 速率限制，请稍后再试。" + detail}
        if status_code in [401, 403]:
            return {"error": "API 密钥无效或权限被拒绝，请检查配置。" + auth_hint}
        if status_code == 404:
            return {"error": "未找到对应数据，请检查玩家 ID / 名称是否正确。"}
        if status_code in (502, 503, 504):
            wait = _format_wait(retry_after)
            hint = f"服务端建议 {wait}后重试。" if wait else "请稍后重试。"
            return {"error": "API 服务暂时不可用，" + hint}
        return {"error": f"API 访问失败 (HTTP {status_code}){detail}"}
    except httpx.RequestError as e:
        logger.error(f"R6States 网络请求异常: {type(e).__name__}: {e}")
        return {"error": "网络连接超时或无法连接到 API 服务器，请稍后重试。"}
    except Exception as e:
        logger.error(f"R6States 发生非预期错误: {type(e).__name__}: {e}")
        return {"error": f"系统内部错误: {str(e)}"}


def _platform_family(platform: str) -> str:
    """uplay 归属 pc；psn/xbl 原样传递"""
    return "pc" if platform == "uplay" else platform


def _format_wait(value: Any) -> str:
    """把服务端返回的 retryAfter 秒数转成可读时长"""
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return ""
    if seconds <= 0:
        return ""
    if seconds < 60:
        return f"{seconds} 秒"
    if seconds < 3600:
        return f"约 {seconds // 60} 分钟"
    hours = seconds / 3600
    if hours < 24:
        return f"约 {hours:.1f} 小时"
    return f"约 {hours / 24:.1f} 天"


async def _r6_get(
    path: str,
    api_key: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 20.0,
) -> Any:
    if not api_key:
        return {"error": "未配置 R6Data API Key。" + APIKEY_HELP}
    url = f"{BASE_URL}/{path.lstrip('/')}"
    headers = {
        "api-key": api_key,
        "Accept": "application/json",
        "User-Agent": "AstrBot-R6States-Plugin/1.1.0",
    }
    return await _fetch(url, headers, params, timeout, APIKEY_HELP)


async def fetch_player_profile(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    """V2 玩家档案：stats / account / banned / seasons / history 一次返回"""
    res = await _r6_get("/v2/profile", api_key, {
        "nameOnPlatform": player_id,
        "platformType": platform,
        "platform_families": _platform_family(platform),
    })
    return res if isinstance(res, dict) else {"error": "API 返回数据格式异常", "raw": str(res)}


async def fetch_player_operators(
    player_id: str,
    api_key: str,
    platform: str = "uplay",
    season_year: Optional[str] = None,
    modes: str = "all",
) -> dict:
    """V2 干员战绩，数据位于 operators.operators 扁平数组中"""
    params: Dict[str, Any] = {
        "nameOnPlatform": player_id,
        "platformType": platform,
        "modes": modes,
    }
    if season_year:
        params["seasonYear"] = season_year
    res = await _r6_get("/v2/operators", api_key, params)
    return res if isinstance(res, dict) else {"error": "API 返回数据格式异常", "raw": str(res)}


async def fetch_player_seasonal_stats(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    """/R6H 使用：从 profile 的 history 中取排位变动，结构与旧 seasonalStats 的 data 一致"""
    res = await fetch_player_profile(player_id, api_key, platform)
    if not isinstance(res, dict):
        return {"error": "API 返回数据格式异常"}
    if res.get("error"):
        return res
    return {"data": (res.get("history") or {}).get("data") or {}}


# 兼容旧调用名
async def fetch_player_stats(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    return await fetch_player_profile(player_id, api_key, platform)


async def fetch_player_data(player_id: str, api_key: str, platform: str = "uplay") -> dict:
    return await fetch_player_operators(player_id, api_key, platform)


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
        "User-Agent": "AstrBot-R6States-Plugin/1.1.0"
    }

    q_lower = query.lower().strip()
    search_query = query
    
    # 强制赛区匹配优先
    if q_lower in LEAGUE_ALIASES:
        real_name = LEAGUE_ALIASES[q_lower]
        url = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(real_name)}"
        leagues = await _fetch(url, headers, auth_hint="请检查 pandascore_api_key 配置。")
        if isinstance(leagues, list) and len(leagues) > 0:
            l_id = leagues[0].get("id")
            l_name = leagues[0].get("name", real_name)
            url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
            matches = await _fetch(url_matches, headers, auth_hint="请检查 pandascore_api_key 配置。")
            return {"type": "league", "name": l_name, "matches": matches if isinstance(matches, list) else []}
            
    # 检查队伍别名
    if q_lower in TEAM_ALIASES:
        search_query = TEAM_ALIASES[q_lower]
            
    # 搜索队伍
    url_teams = f"https://api.pandascore.co/r6siege/teams?search[name]={quote(search_query)}"
    teams = await _fetch(url_teams, headers, auth_hint="请检查 pandascore_api_key 配置。")
    
    if isinstance(teams, dict) and "error" in teams:
        return teams 

    if not isinstance(teams, list) or len(teams) == 0:
        # 尝试按缩写搜 (acronym)
        url_teams_acronym = f"https://api.pandascore.co/r6siege/teams?search[acronym]={quote(search_query)}"
        teams = await _fetch(url_teams_acronym, headers, auth_hint="请检查 pandascore_api_key 配置。")
        
    if isinstance(teams, list) and len(teams) > 0:
        team_best = teams[0]
        t_id = team_best.get("id")
        t_name = team_best.get("name", search_query)
        url_matches = f"https://api.pandascore.co/teams/{t_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches, headers, auth_hint="请检查 pandascore_api_key 配置。")
        return {"type": "team", "name": t_name, "matches": matches if isinstance(matches, list) else []}
        
    # 如果作为队伍搜不到，再作为普通赛区关键词搜一遍
    url_leagues = f"https://api.pandascore.co/r6siege/leagues?search[name]={quote(search_query)}"
    leagues = await _fetch(url_leagues, headers, auth_hint="请检查 pandascore_api_key 配置。")
    if isinstance(leagues, list) and len(leagues) > 0:
        league_best = leagues[0]
        l_id = league_best.get("id")
        l_name = league_best.get("name", search_query)
        url_matches = f"https://api.pandascore.co/leagues/{l_id}/matches?per_page=5&sort=-begin_at"
        matches = await _fetch(url_matches, headers, auth_hint="请检查 pandascore_api_key 配置。")
        return {"type": "league", "name": l_name, "matches": matches if isinstance(matches, list) else []}
        
    return {"error": f"找不到名称匹配 '{query}' 的队伍或赛区，请检查拼写。"}

async def fetch_r6_wiki(endpoint: str, api_key: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """通用 Wiki 数据抓取转发器（operators / maps / weapons 等）"""
    return await _r6_get(endpoint, api_key, params or {})

async def fetch_game_online_stats(api_key: str) -> dict:
    """获取全平台实时在线人数"""
    res = await _r6_get("/v2/gamestats", api_key, {})
    return res if isinstance(res, dict) else {"error": "在线统计数据解析异常"}
