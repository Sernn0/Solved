#!/usr/bin/env python3
"""Generate overall problem-solving stats SVGs for README from local solutions."""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "problem-stats-matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(tempfile.gettempdir()) / "problem-stats-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({
    "font.family": "monospace",
    "font.monospace": ["JetBrains Mono", "Menlo", "Courier New", "DejaVu Sans Mono"],
})

HANDLE = "sernn"
REPO_ROOT = Path(__file__).parent.parent
DATA_FILE = REPO_ROOT / "data" / "problem_history.json"
ASSETS_DIR = REPO_ROOT / "assets"
SOLUTION_ROOTS = {
    "Baekjoon": REPO_ROOT / "백준",
    "Programmers": REPO_ROOT / "프로그래머스",
}

ASSETS_DIR.mkdir(exist_ok=True)

CANVAS_W = 9.6
CONTENT_L = 0.08
CONTENT_R = 0.98

EXT_TO_LANG = {
    "cs": "C#",
    "py": "Python",
    "c": "C",
    "cpp": "C++",
    "java": "Java",
    "js": "JavaScript",
    "kt": "Kotlin",
    "rb": "Ruby",
    "swift": "Swift",
    "go": "Go",
    "rs": "Rust",
    "ts": "TypeScript",
    "scala": "Scala",
    "php": "PHP",
    "hs": "Haskell",
    "lua": "Lua",
    "pl": "Perl",
    "r": "R",
    "sh": "Bash",
}

LANG_COLOR = {
    "C#": "#9B4F96",
    "Python": "#3572A5",
    "C": "#6E6E6E",
    "C++": "#F34B7D",
    "Java": "#B07219",
    "JavaScript": "#F1E05A",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "Swift": "#F05138",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "TypeScript": "#3178C6",
    "Scala": "#C22D40",
    "PHP": "#4F5D95",
    "Haskell": "#5E5086",
    "Lua": "#000080",
    "Perl": "#0298C3",
    "R": "#198CE7",
    "Bash": "#89E051",
    "Other": "#8A8A8A",
}

PLATFORM_COLOR = {
    "Baekjoon": "#0076C0",
    "Programmers": "#00A98F",
}

C_TEXT = "#344054"
C_MUTED = "#667085"
C_ACCENT = "#4F46E5"
C_LIGHT = "#D0D5DD"
C_GRID = "#EAECF0"


def solution_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lstrip(".").lower() in EXT_TO_LANG
    )


def collect_stats() -> dict:
    platforms: dict[str, int] = {}
    lang_counts: dict[str, int] = {}
    solution_file_count = 0

    for platform, root in SOLUTION_ROOTS.items():
        files = solution_files(root)
        problem_dirs = {path.parent for path in files}
        platforms[platform] = len(problem_dirs)
        solution_file_count += len(files)

        for path in files:
            lang = EXT_TO_LANG.get(path.suffix.lstrip(".").lower(), "Other")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    return {
        "handle": HANDLE,
        "solved": sum(platforms.values()),
        "solution_files": solution_file_count,
        "platforms": platforms,
        "languages": lang_counts,
    }


def update_history(stats: dict) -> list:
    DATA_FILE.parent.mkdir(exist_ok=True)
    history = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else []
    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
    history = [item for item in history if item["date"] != today]
    history.append({
        "date": today,
        "solved": stats["solved"],
        "solution_files": stats["solution_files"],
        "platforms": stats["platforms"],
    })
    history.sort(key=lambda item: item["date"])
    DATA_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n")
    return history


def generate_profile_card(stats: dict):
    fig = plt.figure(figsize=(CANVAS_W, 3.2), facecolor="none")
    ax_d = fig.add_axes([0.04, 0.03, 0.44, 0.94])
    ax_i = fig.add_axes([0.50, 0.05, 0.48, 0.90])

    for ax in (ax_d, ax_i):
        ax.set_facecolor("none")
        ax.axis("off")

    platforms = [(name, count) for name, count in stats["platforms"].items() if count > 0]
    sizes = [count for _, count in platforms] or [1]
    colors = [PLATFORM_COLOR.get(name, C_LIGHT) for name, _ in platforms] or [C_LIGHT]

    ax_d.pie(
        sizes,
        colors=colors,
        startangle=90,
        wedgeprops=dict(width=0.44, edgecolor="white", linewidth=0.8),
        radius=1.0,
    )
    ax_d.text(0, 0.08, str(stats["solved"]), ha="center", va="center",
              fontsize=34, fontweight="bold", color=C_ACCENT)
    ax_d.text(0, -0.16, "solved", ha="center", va="center",
              fontsize=11, color=C_MUTED)
    ax_d.set_xlim(-1.22, 1.22)
    ax_d.set_ylim(-1.22, 1.22)

    ax_i.set_xlim(0, 1)
    ax_i.set_ylim(0, 1)
    ax_i.text(0.04, 0.90, HANDLE, fontsize=25, fontweight="bold",
              color=C_TEXT, va="center")
    ax_i.text(0.96, 0.76, "Problem Solved", fontsize=13, fontweight="bold",
              color=C_ACCENT, va="center", ha="right")

    top_lang = max(stats["languages"].items(), key=lambda item: item[1])[0] if stats["languages"] else "None"
    rows = [
        ("Total", f"{stats['solved']} solved"),
        ("Baekjoon", f"{stats['platforms'].get('Baekjoon', 0)} solved"),
        ("Programmers", f"{stats['platforms'].get('Programmers', 0)} solved"),
        ("Main Lang", top_lang),
    ]
    for i, (label, value) in enumerate(rows):
        y = 0.58 - i * 0.125
        ax_i.text(0.04, y, label, fontsize=9.4, color=C_MUTED, va="center")
        ax_i.text(0.96, y, value, fontsize=11.8, fontweight="bold",
                  color=C_TEXT, va="center", ha="right")
        if i < len(rows) - 1:
            ax_i.plot([0.04, 0.96], [y - 0.062, y - 0.062],
                      color=C_LIGHT, linewidth=0.8)

    if platforms:
        total = sum(count for _, count in platforms)
        ax_i.text(0.04, 0.120, "Platforms", fontsize=8.4, color=C_MUTED, va="center")
        bx, by, bh = 0.04, 0.028, 0.072
        ax_i.add_patch(FancyBboxPatch(
            (bx - 0.002, by - 0.004), 0.926, bh + 0.008,
            boxstyle="round,pad=0,rounding_size=0.013",
            facecolor=C_LIGHT, edgecolor="none", alpha=0.40, zorder=1,
        ))
        for platform, count in platforms:
            bw = (count / total) * 0.92
            ax_i.add_patch(FancyBboxPatch(
                (bx + 0.0018, by + 0.003), max(bw - 0.0036, 0.005), bh - 0.006,
                boxstyle="round,pad=0,rounding_size=0.009",
                facecolor=PLATFORM_COLOR.get(platform, C_LIGHT),
                edgecolor="none", zorder=2,
            ))
            bx += bw

    plt.savefig(ASSETS_DIR / "profile_card.svg",
                format="svg", bbox_inches=None, pad_inches=0, transparent=True)
    plt.close()
    print("  - profile_card.svg")


def generate_lang_list(lang_counts: dict):
    langs = sorted(lang_counts.items(), key=lambda item: -item[1])
    if not langs:
        langs = [("No solutions yet", 1)]

    total = sum(count for _, count in langs)
    n = len(langs)
    items_per_row = min(4, n)
    n_rows = max(1, (n + items_per_row - 1) // items_per_row)
    col_w = (CONTENT_R - CONTENT_L) / items_per_row
    fig_h = n_rows * 0.70
    bar_h_in = 0.35
    bar_h = bar_h_in / fig_h
    bar_w = (bar_h_in / 3.0) / CANVAS_W

    fig = plt.figure(figsize=(CANVAS_W, fig_h), facecolor="none")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_facecolor("none")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    for idx, (lang, count) in enumerate(langs):
        row = idx // items_per_row
        col = idx % items_per_row
        bx = CONTENT_L + col * col_w
        cy = 1.0 - (row + 0.5) / n_rows
        pct = count / total * 100
        lang_color = LANG_COLOR.get(lang, LANG_COLOR["Other"])

        ax.add_patch(plt.Rectangle(
            (bx, cy - bar_h / 2), bar_w, bar_h,
            color=lang_color, zorder=5, linewidth=0,
        ))
        tx = bx + bar_w + 0.010
        ax.text(tx, cy + bar_h * 0.28, lang, ha="left", va="center",
                fontsize=11, fontweight="bold", color=C_TEXT, zorder=5)
        ax.text(tx, cy - bar_h * 0.28, f"{pct:.1f}%",
                ha="left", va="center", fontsize=9, color=C_MUTED, zorder=5)

    plt.savefig(ASSETS_DIR / "lang_list.svg",
                format="svg", bbox_inches=None, pad_inches=0, transparent=True)
    plt.close()
    print("  - lang_list.svg")


def draw_progress_axes(ax, history: list):
    graph_days = 30
    latest_dt = datetime.strptime(history[-1]["date"], "%Y-%m-%d")
    first_dt = datetime.strptime(history[0]["date"], "%Y-%m-%d")
    window_start = max(first_dt, latest_dt - timedelta(days=graph_days - 1))
    window_days = (latest_dt - window_start).days + 1

    hist_dict = {item["date"]: item["solved"] for item in history}
    disp_dates = []
    disp_solved = []
    last_known = history[0]["solved"]
    for i in range(window_days):
        day = window_start + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        if key in hist_dict:
            last_known = hist_dict[key]
        disp_dates.append(day)
        disp_solved.append(last_known)

    if len(disp_dates) >= 2:
        date_nums = mdates.date2num(disp_dates)
        if len(disp_dates) >= 4:
            x_smooth = np.linspace(date_nums[0], date_nums[-1], 300)
            y_smooth = np.interp(x_smooth, date_nums, disp_solved)
            x_plot = mdates.num2date(x_smooth)
            y_plot = y_smooth
        else:
            x_plot = disp_dates
            y_plot = disp_solved

        ax.plot(x_plot, y_plot, color=C_ACCENT, linewidth=1.4,
                zorder=5, solid_capstyle="round")
        y_floor = max(0, min(disp_solved) - 1)
        ax.fill_between(x_plot, y_plot, y_floor, alpha=0.12,
                        color=C_ACCENT, zorder=3)
        ax.set_xlim(window_start - timedelta(hours=12), latest_dt + timedelta(hours=12))
    else:
        y_floor = max(0, disp_solved[-1] - 1)
        ax.scatter([disp_dates[-1]], [disp_solved[-1]], color=C_ACCENT, s=38,
                   zorder=6, edgecolors="white", linewidths=0.8)
        ax.set_xlim(disp_dates[-1] - timedelta(days=1), disp_dates[-1] + timedelta(days=1))

    ax.scatter([disp_dates[-1]], [disp_solved[-1]], color=C_ACCENT, s=24,
               zorder=7, edgecolors="white", linewidths=0.8)
    ax.set_ylim(bottom=y_floor)
    tick_interval = max(1, window_days // 7)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=tick_interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.tick_params(axis="x", colors=C_MUTED, labelsize=10, rotation=30)
    ax.tick_params(axis="y", colors=C_MUTED, labelsize=10)
    ax.set_ylabel("Solved Problems", fontsize=10, color=C_MUTED, labelpad=4)
    ax.grid(True, color=C_GRID, linewidth=0.6, linestyle="--", alpha=0.7)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(C_LIGHT)

    ax.annotate(str(disp_solved[-1]), xy=(disp_dates[-1], disp_solved[-1]),
                xytext=(3, 3), textcoords="offset points",
                fontsize=12, color=C_ACCENT, fontweight="bold")


def generate_progress_graph(history: list, stats: dict):
    fig = plt.figure(figsize=(CANVAS_W, 5.5), facecolor="none")
    ax = fig.add_axes([0.08, 0.18, 0.71, 0.68])
    ax_r = fig.add_axes([0.81, 0.05, 0.17, 0.90])

    for axis in (ax, ax_r):
        axis.set_facecolor("none")

    ax_r.axis("off")
    ax_r.set_xlim(0, 1)
    ax_r.set_ylim(0, 1)

    latest = history[-1] if history else {
        "solved": stats["solved"],
        "solution_files": stats["solution_files"],
        "platforms": stats["platforms"],
    }
    ax_r.text(0.05, 0.92, "Solved", fontsize=11, color=C_MUTED)
    ax_r.text(0.05, 0.88, str(latest["solved"]),
              fontsize=26, fontweight="bold", color=C_ACCENT, va="top")
    ax_r.text(0.05, 0.72, "Files", fontsize=11, color=C_MUTED)
    ax_r.text(0.05, 0.64, str(latest.get("solution_files", stats["solution_files"])),
              fontsize=14, fontweight="bold", color=C_ACCENT)

    platforms = latest.get("platforms", stats["platforms"])
    y = 0.50
    for platform, count in platforms.items():
        ax_r.text(0.05, y, platform, fontsize=9.5, color=C_MUTED)
        ax_r.text(0.95, y, str(count), fontsize=10.5, fontweight="bold",
                  color=PLATFORM_COLOR.get(platform, C_ACCENT), ha="right")
        y -= 0.085

    if len(history) >= 2:
        prev = history[-2]
        delta = latest["solved"] - prev["solved"]
        dc = "#16A34A" if delta > 0 else "#EF4444" if delta < 0 else C_MUTED
        ds = f"+{delta} solved" if delta > 0 else f"{delta} solved" if delta < 0 else "0 solved"
        ax_r.text(0.05, 0.58, ds, fontsize=11, color=dc, fontweight="bold")

    if history:
        draw_progress_axes(ax, history)
    else:
        ax.axis("off")
        ax.text(0.5, 0.5, "Collecting problem-solving progress...",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color=C_MUTED)

    ax.set_title("Overall Progress", fontsize=17, color=C_ACCENT,
                 pad=5, fontweight="bold", loc="left")

    plt.savefig(ASSETS_DIR / "progress_graph.svg",
                format="svg", bbox_inches=None, pad_inches=0, transparent=True)
    plt.close()
    print("  - progress_graph.svg")


def main():
    print("Collecting problem solutions from repo...")
    stats = collect_stats()

    print("Updating overall history...")
    history = update_history(stats)

    print("Generating SVGs...")
    generate_profile_card(stats)
    generate_lang_list(stats["languages"])
    generate_progress_graph(history, stats)

    print(
        f"\nDone - {stats['handle']} · Problem Solved · "
        f"{stats['solved']} solved · {stats['solution_files']} solution files"
    )


if __name__ == "__main__":
    main()
