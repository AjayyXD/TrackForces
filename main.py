import time
import threading
from database import db
import setup
from core import stats
from core import gemini

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich import box

console = Console()

# ─────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────
T = {
    "accent":   "bright_cyan",
    "accent2":  "magenta",
    "good":     "bright_green",
    "warn":     "yellow",
    "bad":      "bright_red",
    "muted":    "grey50",
    "border":   "cyan",
    "dim_bdr":  "grey50",
    "bg":       "on grey11",
}

LOGO = (
    "  ████████╗██████╗  █████╗  ██████╗██╗  ██╗    ███████╗ ██████╗ ██████╗  ██████╗███████╗███████╗\n"
    "     ██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝\n"
    "     ██║   ██████╔╝███████║██║     █████╔╝     █████╗  ██║   ██║██████╔╝██║     █████╗  ███████╗\n"
    "     ██║   ██╔══██╗██╔══██║██║     ██╔═██╗     ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝  ╚════██║\n"
    "     ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗    ██║     ╚██████╔╝██║  ██║╚██████╗███████╗███████║\n"
    "     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝"
)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
SPARKS = " ▁▂▃▄▅▆▇█"

def sparkline(values: list[int], width: int = 20) -> str:
    if not values:
        return " " * width
    lo, hi = min(values), max(values)
    rng = hi - lo or 1
    chars = [SPARKS[int((v - lo) / rng * (len(SPARKS) - 1))] for v in values]
    return "".join(chars[-width:])

def acc_badge(acc: float) -> Text:
    if acc >= 70:
        style, symbol = T["good"],  "▲"
    elif acc >= 40:
        style, symbol = T["warn"],  "◆"
    else:
        style, symbol = T["bad"],   "▼"
    t = Text()
    t.append(f"{symbol} {acc:5.1f}%", style=style)
    return t

def hbar(value: int, max_val: int, width: int = 20,
         fill: str = "bright_cyan", empty: str = "grey23") -> Text:
    filled = int((value / max_val) * width) if max_val else 0
    t = Text()
    t.append("█" * filled,            style=fill)
    t.append("░" * (width - filled),  style=empty)
    return t

def stat_row(label: str, value: str, val_style: str = "bold white") -> tuple:
    return (Text(label, style=T["muted"]), Text(value, style=val_style))

def divider(label: str = "") -> tuple:
    sep = Text(f" {label} " if label else "", style=f"bold {T['muted']}")
    return (sep, Text(""))

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
def build_header(handle: str, cf_rating: int | None = None) -> Panel:
    w = console.width or 120
    body = Text(justify="center")

    if w >= 105:
        body.append(LOGO + "\n", style=f"bold {T['accent']}")
    else:
        body.append("  ⚡  TRACK FORCES  ⚡\n", style=f"bold {T['accent']}")

    meta = Text(justify="center")
    meta.append("⚡ ", style=T["warn"])
    meta.append("Codeforces Performance Dashboard", style="bold white")
    meta.append("  ·  ", style=T["muted"])
    meta.append(f"@{handle}", style=f"bold {T['accent']}")
    if cf_rating:
        meta.append("  ·  Rating: ", style=T["muted"])
        meta.append(str(cf_rating), style=f"bold {T['warn']}")
    meta.append("  ⚡", style=T["warn"])
    body.append_text(meta)

    return Panel(
        Align.center(body, vertical="middle"),
        border_style=T["border"],
        style="on grey11",
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    )

# ─────────────────────────────────────────────
#  LEFT COLUMN — Profile stats
# ─────────────────────────────────────────────
def build_profile(gen: dict, handle: str) -> Panel:
    total     = gen["total_subs"]
    solved    = gen["unique_solved_qns"]
    unsolved  = gen["unique_unsolved_qns"]
    total_qns = solved + unsolved
    solve_pct = float(gen["solved_qns_percentage"])
    sub_pct   = float(gen["solved_subs_percentage"])
    avg_r     = gen["avg_rating"]

    t = Table.grid(padding=(0, 1))
    t.add_column(style="grey70",    no_wrap=True, min_width=18)
    t.add_column(justify="right",   no_wrap=True, min_width=10)

    # Handle
    t.add_row(
        Text("◈ HANDLE", style=f"bold {T['accent']}"),
        Text(f"@{handle}", style=f"bold {T['accent']}"),
    )
    t.add_row(*divider())

    # Avg rating big stat
    t.add_row(
        Text("AVG PROBLEM RATING", style=f"bold {T['muted']}"),
        Text(str(avg_r), style=f"bold {T['warn']}"),
    )
    t.add_row(*divider())

    # Submissions
    t.add_row(*divider("── SUBMISSIONS"))
    t.add_row(*stat_row("Total",       f"{total:,}"))
    t.add_row(*stat_row(
        "Accepted %",
        f"{sub_pct:.1f}%",
        T["good"] if sub_pct >= 50 else T["bad"],
    ))
    t.add_row(*divider())

    # Problems
    t.add_row(*divider("── PROBLEMS"))
    t.add_row(*stat_row("Unique Solved",   f"{solved:,}",   f"bold {T['good']}"))
    t.add_row(*stat_row("Unique Unsolved", f"{unsolved:,}", f"bold {T['bad']}"))
    t.add_row(*stat_row("Solve Rate",      f"{solve_pct:.1f}%", T["warn"]))
    t.add_row(Text(""), hbar(solved, total_qns, width=20, fill=T["good"]))
    t.add_row(*divider())

    # Mini gauge: acceptance
    t.add_row(*divider("── ACCEPTANCE"))
    acc_bar = hbar(int(sub_pct), 100, width=20,
                   fill=T["good"] if sub_pct >= 50 else T["bad"])
    t.add_row(Text(""), acc_bar)
    t.add_row(*stat_row("", f"{sub_pct:.1f}% of all subs AC'd"))

    return Panel(
        t,
        title=f"[bold {T['accent']}]◈ PROFILE[/bold {T['accent']}]",
        border_style=T["border"],
        box=box.ROUNDED,
        padding=(1, 2),
    )

# ─────────────────────────────────────────────
#  CENTRE-TOP — Rating distribution (horizontal, compact)
# ─────────────────────────────────────────────
TIER_COLOURS = [
    (800,  "bright_green"),
    (1000, "green"),
    (1200, "cyan"),
    (1400, "bright_cyan"),
    (1600, "bright_blue"),
    (1900, "blue"),
    (2100, "medium_purple1"),
    (2400, "bright_red"),
]

def tier_colour(r: int) -> str:
    for threshold, colour in TIER_COLOURS:
        if int(r) <= threshold:
            return colour
    return "bright_red"

def build_ratings(rating_dist: list) -> Panel:
    if not rating_dist:
        return Panel("No data", title="Rating Distribution")

    max_count = max(c for _, c in rating_dist) or 1
    counts    = [c for _, c in rating_dist]
    spark     = sparkline(counts, width=len(counts))

    lines = Text()
    lines.append("  Trend  ", style=T["muted"])
    lines.append(spark + "\n\n", style=f"bold {T['accent']}")

    BAR_W = 22
    for rating, count in rating_dist:
        colour = tier_colour(rating)
        filled = int((count / max_count) * BAR_W)
        pct    = count / sum(counts) * 100

        lines.append(f"  {str(rating):<5} ", style=f"bold {colour}")
        lines.append("█" * filled,           style=colour)
        lines.append("░" * (BAR_W - filled), style="grey23")
        lines.append(f"  {count:>3} ", style="grey70")
        lines.append(f"({pct:4.1f}%)\n", style=T["muted"])

    return Panel(
        lines,
        title=f"[bold {T['accent2']}]📈 RATING DISTRIBUTION[/bold {T['accent2']}]",
        border_style=T["accent2"],
        box=box.ROUNDED,
        padding=(0, 1),
    )

# ─────────────────────────────────────────────
#  CENTRE-BOTTOM — Category breakdown
# ─────────────────────────────────────────────
def build_categories(cat_counts: list, acc_dict: dict, top_n: int = 10) -> Panel:
    if not cat_counts:
        return Panel("No data", title="Categories")

    max_count = cat_counts[0][1] or 1

    tbl = Table(
        show_header=True,
        header_style=f"bold {T['accent']}",
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
        expand=True,
    )
    tbl.add_column("Category",  style="bold white",  no_wrap=True, min_width=20)
    tbl.add_column("Solved",    justify="right",      width=6)
    tbl.add_column("Progress",                        ratio=1, min_width=22)
    tbl.add_column("Accuracy",  justify="right",      width=10)
    tbl.add_column("Grade",     justify="center",     width=5)

    GRADE_MAP = [
        (80, "S", T["good"]),
        (65, "A", T["good"]),
        (50, "B", T["warn"]),
        (35, "C", T["warn"]),
        (0,  "D", T["bad"]),
    ]

    for cat, count in cat_counts[:top_n]:
        acc   = acc_dict.get(cat, 0.0)
        grade, gstyle = next(
            (g, s) for threshold, g, s in GRADE_MAP if acc >= threshold
        )
        fill = T["good"] if acc >= 65 else T["warn"] if acc >= 35 else T["bad"]
        bar  = hbar(count, max_count, width=22, fill=fill)

        tbl.add_row(
            cat.title(),
            str(count),
            bar,
            acc_badge(acc),
            Text(grade, style=f"bold {gstyle}"),
        )

    legend = Text(justify="right")
    legend.append("S≥80 ", style=f"bold {T['good']}")
    legend.append("A≥65 ", style=f"bold {T['good']}")
    legend.append("B≥50 ", style=f"bold {T['warn']}")
    legend.append("C≥35 ", style=f"bold {T['warn']}")
    legend.append("D<35",  style=f"bold {T['bad']}")

    return Panel(
        tbl,
        title=f"[bold {T['good']}]🏷  CATEGORY BREAKDOWN[/bold {T['good']}]",
        subtitle=legend,
        border_style=T["good"],
        box=box.ROUNDED,
        padding=(0, 1),
    )

# ─────────────────────────────────────────────
#  RIGHT COLUMN — Insights (full height, no clipping)
# ─────────────────────────────────────────────
def build_insights(cat_counts: list, acc_dict: dict):
    weak = sorted(
        [
            (cat, count, acc_dict.get(cat, 0.0))
            for cat, count in cat_counts
            if count >= 3 and acc_dict.get(cat, 0.0) < 50.0
        ],
        key=lambda x: x[2],
    )

    base = Text()

    # ── Weak areas block ──────────────────────
    if weak:
        base.append("  ⚠  WEAK AREAS\n\n", style=f"bold {T['warn']}")
        for cat, count, acc in weak[:5]:
            label = cat.title()[:18]
            base.append(f"  {label:<18}", style="bold white")
            base.append(f" {acc:5.1f}%", style=T["bad"])
            base.append(f"  {count} tried\n", style=T["muted"])
        base.append("\n")
    else:
        base.append("  ✔  No glaring weak areas!\n\n", style=f"bold {T['good']}")

    # ── Strength block ────────────────────────
    strong = sorted(
        [
            (cat, count, acc_dict.get(cat, 0.0))
            for cat, count in cat_counts
            if count >= 3 and acc_dict.get(cat, 0.0) >= 65.0
        ],
        key=lambda x: -x[2],
    )
    if strong:
        base.append("  ★  STRENGTHS\n\n", style=f"bold {T['good']}")
        for cat, count, acc in strong[:3]:
            label = cat.title()[:18]
            base.append(f"  {label:<18}", style="bold white")
            base.append(f" {acc:5.1f}%\n", style=T["good"])
        base.append("\n")

    base.append("  ─" * 14 + "\n\n", style=T["dim_bdr"])
    base.append("  💡  AI COACH\n\n", style=f"bold {T['accent']}")

    # ── Gemini fetch in background ─────────────
    result: dict = {"data": None, "done": False}

    def fetch():
        try:
            coach        = gemini.gemini_coach()
            result["data"] = coach.get_user_insights()
        except Exception:
            result["data"] = None
        finally:
            result["done"] = True

    threading.Thread(target=fetch, daemon=True).start()

    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not result["done"]:
        spinning = Text.assemble(
            base.copy(),
            (f"  {frames[i % len(frames)]}  Consulting Gemini…\n",
             f"bold {T['accent']}"),
        )
        yield _insights_panel(spinning)
        time.sleep(0.1)
        i += 1

    # ── Build final content ────────────────────
    final = base.copy()
    raw   = result["data"]
    gdata = raw.parsed if raw else None

    def _wrap(text: str, limit: int = 68) -> str:
        return text if len(text) <= limit else text[:limit - 1] + "…"

    if gdata and gdata.insights:
        final.append("  Insights\n", style=f"bold {T['accent']}")
        for item in gdata.insights[:3]:
            final.append(f"  • {_wrap(item)}\n", style="white")
        final.append("\n")

    if gdata and gdata.suggestions:
        final.append("  Suggestions\n", style=f"bold {T['accent']}")
        for item in gdata.suggestions[:3]:
            final.append(f"  • {_wrap(item)}\n", style="white")
        final.append("\n")

    if gdata and gdata.focus_topics:
        final.append("  Focus Topics\n", style=f"bold {T['accent']}")
        for topic in gdata.focus_topics[:4]:
            final.append(f"  ▶  {topic}\n", style=f"bold {T['warn']}")
    elif not gdata:
        final.append(
            "  ✘  Could not reach Gemini.\n     Check your API key or network.\n",
            style=T["bad"],
        )

    yield _insights_panel(final)


def _insights_panel(content: Text) -> Panel:
    return Panel(
        content,
        title=f"[bold {T['warn']}]🔍 INSIGHTS & COACHING[/bold {T['warn']}]",
        border_style=T["warn"],
        box=box.ROUNDED,
        padding=(1, 1),
    )

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
def build_footer() -> Text:
    t = Text(justify="center")
    for key, label in [("Q", "Quit"), ("R", "Refresh"), ("T", "AI Tips")]:
        t.append(f"  [{key}] ", style=f"bold {T['accent']}")
        t.append(f"{label}  ", style="grey60")
    t.append("  ·  TrackForces v1.0  ·  ", style=T["muted"])
    t.append("github.com/AjayyXD/TrackForces", style=T["muted"])
    return t

# ─────────────────────────────────────────────
#  MASTER LAYOUT
#
#  ┌─────────────────── header ────────────────────┐
#  │  left (25%)  │   centre (45%)   │  right (30%) │
#  │              │  ratings (top)   │              │
#  │   profile    │──────────────────│   insights   │
#  │   (full)     │  categories(bot) │   (full)     │
#  └──────────────┴──────────────────┴──────────────┘
#  └─────────────────── footer ────────────────────┘
# ─────────────────────────────────────────────
def create_hud(data: dict, handle: str, cf_rating: int) -> Layout:
    gen      = data["general_stats"]
    cat_data = data["category_stats"]
    acc_dict = {
        cat: float(acc)
        for cat, _, acc in cat_data["category_wise_accuracy"]
    }

    hud = Layout()
    hud.split_column(
        Layout(name="header", size=8),
        Layout(name="body",   ratio=1),
        Layout(name="footer", size=3),
    )

    # Three-column body
    hud["body"].split_row(
        Layout(name="left",   ratio=25),
        Layout(name="centre", ratio=45),
        Layout(name="right",  ratio=30),
    )

    # Centre split: ratings on top, categories below
    hud["centre"].split_column(
        Layout(name="ratings",    ratio=4),
        Layout(name="categories", ratio=6),
    )

    # Populate
    hud["header"].update(build_header(handle, cf_rating))
    hud["left"].update(build_profile(gen, handle))
    hud["ratings"].update(build_ratings(gen["rating_distribution"]))
    hud["categories"].update(
        build_categories(cat_data["category_wise_count"], acc_dict)
    )
    hud["footer"].update(
        Panel(build_footer(), border_style=T["dim_bdr"], box=box.ROUNDED, padding=(0, 0))
    )

    return hud


# ─────────────────────────────────────────────
#  ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    db_handler = db.database_handler()
    if not db_handler.is_init():
        setup.run_setup()

    stats_handler = stats.stats_handler()

    with console.status(
        "[bold bright_cyan]⚡ Fetching your Codeforces metrics…[/bold bright_cyan]",
        spinner="aesthetic",
    ):
        raw_data = stats_handler.get_user_stats()

    handle = raw_data.get("handle")
    rating = int(raw_data.get("rating"))

    master = create_hud(raw_data, handle, rating)

    cat_data = raw_data["category_stats"]
    acc_dict = {
        cat: float(acc)
        for cat, _, acc in cat_data["category_wise_accuracy"]
    }
    insights_gen = build_insights(cat_data["category_wise_count"], acc_dict)

    with Live(master, screen=True, refresh_per_second=12):
        try:
            for panel in insights_gen:
                master["right"].update(panel)
                time.sleep(0.08)
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    console.print(
        "\n[bold bright_cyan]⚡ TrackForces offline. Keep grinding.[/bold bright_cyan]\n"
    )