import time
import sys
from decimal import Decimal
from database import db
import setup
from core import stats

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()

# ─────────────────────────────────────────────
#  THEME  (one place to change everything)
# ─────────────────────────────────────────────
THEME = {
    "accent":    "bright_cyan",
    "accent2":   "magenta",
    "good":      "bright_green",
    "warn":      "yellow",
    "bad":       "bright_red",
    "dim":       "grey50",
    "border":    "cyan",
    "header_bg": "on grey11",
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
#  HELPER: sparkline using braille blocks
# ─────────────────────────────────────────────
SPARKS = " ▁▂▃▄▅▆▇█"

def sparkline(values: list[int], width: int = 20) -> str:
    if not values:
        return " " * width
    lo, hi = min(values), max(values)
    rng = hi - lo or 1
    chars = [SPARKS[int((v - lo) / rng * (len(SPARKS) - 1))] for v in values]
    return "".join(chars[-width:])

# ─────────────────────────────────────────────
#  HELPER: accuracy → coloured badge
# ─────────────────────────────────────────────
def acc_badge(acc: float) -> Text:
    if acc >= 70:
        style = THEME["good"]
        symbol = "▲"
    elif acc >= 40:
        style = THEME["warn"]
        symbol = "◆"
    else:
        style = THEME["bad"]
        symbol = "▼"
    t = Text()
    t.append(f"{symbol} {acc:5.1f}%", style=style)
    return t

# ─────────────────────────────────────────────
#  HELPER: horizontal bar (two-tone fill/empty)
# ─────────────────────────────────────────────
def hbar(value: int, max_val: int, width: int = 24,
         fill_style: str = "bright_cyan", empty_style: str = "grey23") -> Text:
    filled = int((value / max_val) * width) if max_val else 0
    t = Text()
    t.append("█" * filled, style=fill_style)
    t.append("░" * (width - filled), style=empty_style)
    return t

# ─────────────────────────────────────────────
#  SECTION: Header panel
# ─────────────────────────────────────────────
def build_header(handle: str, cf_rating: int | None = None) -> Panel:
    term_width = console.width or 120
    use_big = term_width >= 105

    header_text = Text(justify="center")
    if use_big:
        header_text.append(LOGO + "\n", style="bold bright_cyan")
    else:
        header_text.append("  ⚡  TRACK FORCES  ⚡\n", style="bold bright_cyan")

    sub = Text(justify="center")
    sub.append("⚡ ", style="yellow")
    sub.append("Codeforces Performance Dashboard", style="bold white")
    sub.append("  │  @", style=THEME["dim"])
    sub.append(handle, style=f"bold {THEME['accent']}")
    if cf_rating:
        sub.append("  │  Rating: ", style=THEME["dim"])
        sub.append(str(cf_rating), style=f"bold {THEME['warn']}")
    sub.append(" ⚡", style="yellow")

    header_text.append_text(sub)

    return Panel(
        Align.center(header_text, vertical="middle"),
        border_style=THEME["border"],
        style=THEME["header_bg"],
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    )

# ─────────────────────────────────────────────
#  SECTION: Profile / General stats sidebar
# ─────────────────────────────────────────────
def build_profile(gen: dict, handle: str) -> Panel:
    t = Table.grid(padding=(0, 1))
    t.add_column(style="bold grey70", no_wrap=True)
    t.add_column(justify="right", no_wrap=True)

    total   = gen["total_subs"]
    solved  = gen["unique_solved_qns"]
    unsolved = gen["unique_unsolved_qns"]
    total_qns = solved + unsolved
    solve_pct = float(gen["solved_qns_percentage"])
    sub_pct   = float(gen["solved_subs_percentage"])
    avg_r     = gen["avg_rating"]

    bar = hbar(solved, total_qns, width=18, fill_style=THEME["good"])

    t.add_row(
        Text("◈ HANDLE", style=f"bold {THEME['accent']}"),
        Text(f"@{handle}", style=f"bold {THEME['accent']}"),
    )
    t.add_row(Text(""), Text(""))

    t.add_row(
        Text("AVG PROBLEM RATING", style="bold grey60"),
        Text(str(avg_r), style=f"bold {THEME['warn']}"),
    )
    t.add_row(Text(""), Text(""))

    # ── Submissions block ──────────────────
    t.add_row(
        Text("── SUBMISSIONS ──────", style=THEME["dim"]),
        Text(""),
    )
    t.add_row(
        Text("Total"),
        Text(f"{total:,}", style="bold white"),
    )
    t.add_row(
        Text("Accepted %"),
        Text(f"{sub_pct:.1f}%", style=THEME["good"] if sub_pct >= 50 else THEME["bad"]),
    )
    t.add_row(Text(""), Text(""))

    # ── Problems block ─────────────────────
    t.add_row(
        Text("── PROBLEMS ─────────", style=THEME["dim"]),
        Text(""),
    )
    t.add_row(
        Text("Unique Solved"),
        Text(f"{solved:,}", style=f"bold {THEME['good']}"),
    )
    t.add_row(
        Text("Unique Unsolved"),
        Text(f"{unsolved:,}", style=f"bold {THEME['bad']}"),
    )
    t.add_row(
        Text("Solve Rate"),
        Text(f"{solve_pct:.1f}%", style=THEME["warn"]),
    )
    t.add_row(
        Text(""),
        bar,
    )

    return Panel(
        t,
        title=f"[bold {THEME['accent']}]◈ PROFILE MATRIX[/bold {THEME['accent']}]",
        border_style=THEME["border"],
        box=box.ROUNDED,
        padding=(1, 2),
    )

# ─────────────────────────────────────────────
#  SECTION: Rating distribution
# ─────────────────────────────────────────────
def build_ratings(rating_dist: list) -> Panel:
    if not rating_dist:
        return Panel("No data", title="Rating Distribution")

    max_count = max(c for _, c in rating_dist) or 1
    counts    = [c for _, c in rating_dist]
    spark     = sparkline(counts, width=len(counts))

    TIER_COLOURS = [
        (800,  "bright_green"),
        (1000, "green"),
        (1200, "cyan"),
        (1400, "bright_cyan"),
        (1600, "bright_blue"),
        (1900, "blue"),
        (2100, "magenta"),
        (2400, "bright_red"),
    ]

    def tier_colour(r: int) -> str:
        r = int(r)
        for threshold, colour in TIER_COLOURS:
            if r <= threshold:
                return colour
        return "bright_red"

    lines = Text()
    lines.append(f"  Trend: ", style=THEME["dim"])
    lines.append(f"{spark}\n\n", style=f"bold {THEME['accent']}")

    BAR_W = 24
    for rating, count in rating_dist:
        colour  = tier_colour(rating)
        filled  = int((count / max_count) * BAR_W)
        empty   = BAR_W - filled

        lines.append(f"  {str(rating):<5} ", style=f"bold {colour}")
        lines.append("█" * filled,           style=colour)         
        lines.append("░" * empty,            style="grey23")
        lines.append(f"  {count:>4} solves\n", style="grey70")

    return Panel(
        lines,
        title=f"[bold {THEME['accent2']}]📈 RATING DISTRIBUTION[/bold {THEME['accent2']}]",
        border_style=THEME["accent2"],
        box=box.ROUNDED,
        padding=(0, 1),
    )

# ─────────────────────────────────────────────
#  SECTION: Category breakdown
# ─────────────────────────────────────────────
def build_categories(cat_counts: list, acc_dict: dict, top_n: int = 10) -> Panel:
    if not cat_counts:
        return Panel("No data", title="Categories")

    max_count = cat_counts[0][1] or 1

    tbl = Table(
        show_header=True,
        header_style=f"bold {THEME['accent']}",
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
        expand=True,
    )
    tbl.add_column("Category",  style="bold white",   no_wrap=True, width=18)
    tbl.add_column("Solved",    justify="right",       width=7)
    tbl.add_column("Bar",                              ratio=1)
    tbl.add_column("Accuracy",  justify="right",       width=10)
    tbl.add_column("Grade",     justify="center",      width=3)

    for cat, count in cat_counts[:top_n]:
        acc    = acc_dict.get(cat, 0.0)
        bar    = hbar(count, max_count, width=20,
                      fill_style=THEME["good"] if acc >= 60 else
                                 THEME["warn"]  if acc >= 35 else THEME["bad"])
        grade  = "S" if acc >= 80 else "A" if acc >= 65 else "B" if acc >= 50 else "C" if acc >= 35 else "D"
        gstyle = (THEME["good"]  if grade in ("S","A") else
                  THEME["warn"]  if grade == "B" else
                  THEME["bad"])

        tbl.add_row(
            cat.title(),
            str(count),
            bar,
            acc_badge(acc),
            Text(grade, style=f"bold {gstyle}"),
        )

    return Panel(
        tbl,
        title=f"[bold {THEME['good']}]🏷  CATEGORY BREAKDOWN  [grey50](S≥80 A≥65 B≥50 C≥35 D<35)[/grey50][/bold {THEME['good']}]",
        border_style=THEME["good"],
        box=box.ROUNDED,
        padding=(0, 1),
    )

# ─────────────────────────────────────────────
#  SECTION: Weak spots / Gemini tip placeholder
# ─────────────────────────────────────────────
def build_insights(cat_counts: list, acc_dict: dict) -> Panel:
    weak = [
        (cat, count, acc_dict.get(cat, 0.0))
        for cat, count in cat_counts
        if count >= 5 and acc_dict.get(cat, 0.0) < 50.0
    ]
    weak.sort(key=lambda x: x[2])  

    t = Text()

    if weak:
        t.append("  ⚠  WEAK AREAS DETECTED\n\n", style=f"bold {THEME['warn']}")
        for cat, count, acc in weak[:4]:
            t.append(f"  • {cat.title():<20}", style="bold white")
            t.append(f"{acc:5.1f}%  ", style=THEME["bad"])
            t.append(f"({count} attempted)\n", style=THEME["dim"])
        t.append("\n")

    t.append("  💡 AI COACH  ", style=f"bold {THEME['accent']}")
    t.append("[Gemini integration coming soon]\n", style=THEME["dim"])
    t.append("  Run with --tips to get personalised improvement advice\n",
             style=THEME["dim"])

    return Panel(
        t,
        title=f"[bold {THEME['warn']}]🔍 INSIGHTS & COACHING[/bold {THEME['warn']}]",
        border_style=THEME["warn"],
        box=box.ROUNDED,
        padding=(0, 1),
    )

# ─────────────────────────────────────────────
#  SECTION: Footer
# ─────────────────────────────────────────────
def build_footer() -> Text:
    t = Text(justify="center")
    t.append("  [Q] ", style=f"bold {THEME['accent']}")
    t.append("Quit  ", style="grey60")
    t.append("  [R] ", style=f"bold {THEME['accent']}")
    t.append("Refresh  ", style="grey60")
    t.append("  [T] ", style=f"bold {THEME['accent']}")
    t.append("AI Tips  ", style="grey60")
    t.append("  •  TrackForces v1.0  •  ", style=THEME["dim"])
    t.append("github.com/AjayyXD/TrackForces", style=THEME["dim"])
    return t

# ─────────────────────────────────────────────
#  MASTER LAYOUT
# ─────────────────────────────────────────────
def create_hud(data: dict, handle: str ,
               cf_rating: int ) -> Layout:
    gen      = data["general_stats"]
    cat_data = data["category_stats"]

    acc_dict = {
        cat: float(acc)
        for cat, _, acc in cat_data["category_wise_accuracy"]
    }

    hud = Layout()

    hud.split_column(
        Layout(name="header",    size=7),
        Layout(name="main",      ratio=1),
        Layout(name="footer",    size=3),
    )

    hud["main"].split_row(
        Layout(name="left",  ratio=3),
        Layout(name="right", ratio=7),
    )

    hud["right"].split_column(
        Layout(name="top_right",    ratio=5),
        Layout(name="bottom_right", ratio=6),
    )

    hud["top_right"].split_row(
        Layout(name="ratings",  ratio=1),
        Layout(name="insights", ratio=1),
    )

    hud["header"].update(build_header(handle, cf_rating))
    hud["left"].update(build_profile(gen, handle))
    hud["ratings"].update(build_ratings(gen["rating_distribution"]))
    hud["insights"].update(build_insights(cat_data["category_wise_count"], acc_dict))
    hud["bottom_right"].update(
        build_categories(cat_data["category_wise_count"], acc_dict)
    )
    hud["footer"].update(
        Panel(build_footer(), border_style=THEME["dim"], box=box.ROUNDED, padding=(0, 0))
    )

    return hud


# ─────────────────────────────────────────────
#  ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    database_handler = db.database_handler()
    if not database_handler.is_init():
        setup.run_setup()

    stats_handler = stats.stats_handler()

    with console.status(
        "[bold bright_cyan]⚡ Fetching your Codeforces metrics...[/bold bright_cyan]",
        spinner="aesthetic",
    ):
        raw_data = stats_handler.get_user_stats()

    handle = raw_data.get("handle")
    rating = int(raw_data.get("rating"))

    master_layout = create_hud(raw_data, handle,rating)

    with Live(master_layout, screen=True, refresh_per_second=2):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    console.print(
        "\n[bold bright_cyan]⚡ TrackForces offline. Keep grinding.[/bold bright_cyan]\n"
    )