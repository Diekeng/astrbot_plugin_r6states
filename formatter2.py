def format_operator_stats(data: dict) -> str:
    operators = data["split"]["pc"]["playlists"]["quickmatch"]["operators"]

    lines = ["干员数据："]

    for op in operators.values():
        name = op["operator"]
        played = op["rounds"]["lifetime"]["played"]
        winrate = op["rounds"]["lifetime"]["winRate"]

        lines.append(f"{name} | 场次:{played} | 胜率:{winrate}%")

    return "\n".join(lines)