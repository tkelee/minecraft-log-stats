import csv
import html
import re
import sys
from collections import defaultdict


PLAYER_NAME_PATTERN = r"[A-Za-z0-9_]{3,16}"
MESSAGE_PREFIX_PATTERN = r"^\[[^\]]+\]\s+\[[^\]]+\]:\s+"

JOIN_PATTERN = re.compile(
    rf"{MESSAGE_PREFIX_PATTERN}(?P<player>{PLAYER_NAME_PATTERN}) joined the game$"
)

LEFT_PATTERN = re.compile(
    rf"{MESSAGE_PREFIX_PATTERN}(?P<player>{PLAYER_NAME_PATTERN}) left the game$"
)

CHAT_PATTERN = re.compile(
    rf"{MESSAGE_PREFIX_PATTERN}<(?P<player>{PLAYER_NAME_PATTERN})>\s?.*$"
)

DEATH_REASONS = [
    "fell ",
    "was slain",
    "was shot",
    "was blown up",
    "was killed",
    "was burned",
    "went up in flames",
    "tried to swim in lava",
    "drowned",
    "blew up",
    "hit the ground too hard",
    "fell out of the world",
    "starved to death",
    "suffocated",
    "walked into",
    "discovered the floor was lava",
    "didn't want to live in the same world as",
    "was pricked to death",
    "froze to death",
    "experienced kinetic energy",
]

DEATH_REASON_PATTERN = "|".join(re.escape(reason) for reason in DEATH_REASONS)

DEATH_PATTERN = re.compile(
    rf"{MESSAGE_PREFIX_PATTERN}(?P<player>{PLAYER_NAME_PATTERN}) (?P<reason>{DEATH_REASON_PATTERN}).*$"
)


def create_empty_stat():
    return {
        "joined": 0,
        "left": 0,
        "deaths": 0,
        "chats": 0,
    }


def get_sorted_players(stats):
    return sorted(
        stats.items(),
        key=lambda item: (-item[1]["joined"], -item[1]["chats"], item[0].lower())
    )


def parse_log_file(log_path):
    stats = defaultdict(create_empty_stat)
    found_any_event = False

    with open(log_path, "r", encoding="utf-8", errors="replace") as file:
        for raw_line in file:
            line = raw_line.rstrip("\n")

            join_match = JOIN_PATTERN.match(line)
            if join_match:
                player = join_match.group("player")
                stats[player]["joined"] += 1
                found_any_event = True
                continue

            left_match = LEFT_PATTERN.match(line)
            if left_match:
                player = left_match.group("player")
                stats[player]["left"] += 1
                found_any_event = True
                continue

            death_match = DEATH_PATTERN.match(line)
            if death_match:
                player = death_match.group("player")
                stats[player]["deaths"] += 1
                found_any_event = True
                continue

            chat_match = CHAT_PATTERN.match(line)
            if chat_match:
                player = chat_match.group("player")
                stats[player]["chats"] += 1
                found_any_event = True

    return stats, found_any_event


def print_report(stats):
    sorted_players = get_sorted_players(stats)

    print("玩家活动统计（按加入次数排序）")
    print("-" * 72)
    print(
        f"{'排名':<4} "
        f"{'玩家名':<16} "
        f"{'加入次数':<8} "
        f"{'离开次数':<8} "
        f"{'死亡次数':<8} "
        f"{'聊天次数':<8}"
    )
    print("-" * 72)

    for index, (player, data) in enumerate(sorted_players, start=1):
        print(
            f"{index:<4} "
            f"{player:<16} "
            f"{data['joined']:<8} "
            f"{data['left']:<8} "
            f"{data['deaths']:<8} "
            f"{data['chats']:<8}"
        )


def export_csv(stats, output_path):
    sorted_players = get_sorted_players(stats)

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["rank", "player", "joined", "left", "deaths", "chats"])

        for index, (player, data) in enumerate(sorted_players, start=1):
            writer.writerow([
                index,
                player,
                data["joined"],
                data["left"],
                data["deaths"],
                data["chats"],
            ])


def get_summary(stats):
    total_players = len(stats)
    total_joined = sum(player["joined"] for player in stats.values())
    total_left = sum(player["left"] for player in stats.values())
    total_deaths = sum(player["deaths"] for player in stats.values())
    total_chats = sum(player["chats"] for player in stats.values())

    sorted_players = get_sorted_players(stats)
    most_active = sorted_players[0][0] if sorted_players else "-"

    most_deaths_player = "-"
    if sorted_players:
        most_deaths_player = max(
            stats.items(),
            key=lambda item: (item[1]["deaths"], item[0].lower())
        )[0]

    most_chats_player = "-"
    if sorted_players:
        most_chats_player = max(
            stats.items(),
            key=lambda item: (item[1]["chats"], item[0].lower())
        )[0]

    return {
        "total_players": total_players,
        "total_joined": total_joined,
        "total_left": total_left,
        "total_deaths": total_deaths,
        "total_chats": total_chats,
        "most_active": most_active,
        "most_deaths_player": most_deaths_player,
        "most_chats_player": most_chats_player,
    }


def generate_insights(stats):
    insights = []

    if not stats:
        return ["没有足够数据生成建议。"]

    total_joined = sum(player["joined"] for player in stats.values())
    total_left = sum(player["left"] for player in stats.values())
    total_deaths = sum(player["deaths"] for player in stats.values())
    total_chats = sum(player["chats"] for player in stats.values())

    most_active_player, most_active_data = max(
        stats.items(),
        key=lambda item: (item[1]["joined"], item[1]["chats"], item[0].lower())
    )

    most_deaths_player, most_deaths_data = max(
        stats.items(),
        key=lambda item: (item[1]["deaths"], item[0].lower())
    )

    most_chats_player, most_chats_data = max(
        stats.items(),
        key=lambda item: (item[1]["chats"], item[0].lower())
    )

    insights.append(
        f"{most_active_player} 是当前最活跃玩家，可以优先关注这类核心玩家。"
    )

    if most_deaths_data["deaths"] >= 3:
        insights.append(
            f"{most_deaths_player} 死亡次数较多，可能需要检查玩法难度、出生点附近风险或玩家是否卡在某个区域。"
        )

    if most_chats_data["chats"] >= 3:
        insights.append(
            f"{most_chats_player} 聊天较活跃，可能是社区氛围的关键玩家。"
        )

    if total_joined > total_left + 2:
        insights.append(
            "加入次数明显多于离开次数，可能是日志不完整，或者服务器曾异常关闭。"
        )

    if total_chats == 0:
        insights.append(
            "没有识别到聊天记录，可能是服务器聊天较少，或日志格式与当前规则不匹配。"
        )

    if total_deaths == 0:
        insights.append(
            "没有识别到死亡记录，可能是服务器玩法较轻松，或死亡日志格式暂未支持。"
        )

    return insights


def export_html(stats, output_path):
    summary = get_summary(stats)
    insights = generate_insights(stats)
    sorted_players = get_sorted_players(stats)

    rows = []
    for index, (player, data) in enumerate(sorted_players, start=1):
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{html.escape(player)}</td>"
            f"<td>{data['joined']}</td>"
            f"<td>{data['left']}</td>"
            f"<td>{data['deaths']}</td>"
            f"<td>{data['chats']}</td>"
            "</tr>"
        )

    html_content = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Minecraft 服务器日志报告</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      margin: 32px;
      background: #f6f7f9;
      color: #222;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    .subtitle {{
      color: #666;
      margin-bottom: 24px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .card {{
      background: white;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .label {{
      color: #666;
      font-size: 14px;
    }}
    .value {{
      font-size: 28px;
      font-weight: 700;
      margin-top: 6px;
    }}
    .insights {{
      background: white;
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      margin-bottom: 24px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid #eee;
      text-align: left;
    }}
    th {{
      background: #eef1f5;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
  </style>
</head>
<body>
  <h1>Minecraft 服务器日志报告</h1>
  <div class="subtitle">由 minecraft_log_stats.py 自动生成</div>

  <div class="cards">
    <div class="card">
      <div class="label">识别玩家数</div>
      <div class="value">{summary['total_players']}</div>
    </div>
    <div class="card">
      <div class="label">总加入次数</div>
      <div class="value">{summary['total_joined']}</div>
    </div>
    <div class="card">
      <div class="label">总离开次数</div>
      <div class="value">{summary['total_left']}</div>
    </div>
    <div class="card">
      <div class="label">总死亡次数</div>
      <div class="value">{summary['total_deaths']}</div>
    </div>
    <div class="card">
      <div class="label">总聊天次数</div>
      <div class="value">{summary['total_chats']}</div>
    </div>
  </div>

  <div class="insights">
    <h2>运营建议</h2>
    <ul>
      {''.join(f"<li>{html.escape(item)}</li>" for item in insights)}
    </ul>
  </div>

  <h2>玩家排行榜</h2>
  <table>
    <thead>
      <tr>
        <th>排名</th>
        <th>玩家名</th>
        <th>加入次数</th>
        <th>离开次数</th>
        <th>死亡次数</th>
        <th>聊天次数</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_content)


def main():
    if len(sys.argv) != 2:
        print("用法: python3 minecraft_log_stats.py <latest.log 文件路径>")
        return

    log_path = sys.argv[1]

    try:
        stats, found_any_event = parse_log_file(log_path)
    except FileNotFoundError:
        print(f"错误：文件不存在：{log_path}")
        return
    except OSError as error:
        print(f"错误：无法打开文件：{log_path}")
        print(f"系统信息：{error}")
        return

    if not found_any_event:
        print("没有识别到玩家活动记录。可能原因：日志文件不是服务器日志，或者格式不匹配。")
        return

    print_report(stats)

    export_csv(stats, "report.csv")
    print("\n已导出 CSV 报告：report.csv")

    export_html(stats, "report.html")
    print("已导出 HTML 报告：report.html")


if __name__ == "__main__":
    main()
