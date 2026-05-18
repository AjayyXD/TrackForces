<div align="center">

```
  ████████╗██████╗  █████╗  ██████╗██╗  ██╗    ███████╗ ██████╗ ██████╗  ██████╗███████╗███████╗
     ██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝
     ██║   ██████╔╝███████║██║     █████╔╝     █████╗  ██║   ██║██████╔╝██║     █████╗  ███████╗
     ██║   ██╔══██╗██╔══██║██║     ██╔═██╗     ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝  ╚════██║
     ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗    ██║     ╚██████╔╝██║  ██║╚██████╗███████╗███████║
     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝
```

**⚡ A terminal-based Codeforces performance dashboard ⚡**

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![MariaDB](https://img.shields.io/badge/MariaDB-required-brown?style=flat-square&logo=mariadb)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## What is TrackForces?

TrackForces is a rich terminal dashboard that pulls your [Codeforces](https://codeforces.com) submission history and presents it as a live, colour-coded HUD — no browser required. It shows your profile stats, problem rating distribution, per-category performance, and automatically flags weak areas for targeted practice.

On first run it fetches your entire submission history from the Codeforces API and stores it locally in a MariaDB database. Every subsequent run only syncs new submissions, so the dashboard launches instantly after the initial setup.

---

## Features

- **Live terminal HUD** — full-screen dashboard powered by [Rich](https://github.com/Textualize/rich), auto-refreshes every 2 seconds
- **Profile Matrix** — total submissions, acceptance rate, unique solved / unsolved counts, solve rate bar
- **Rating Distribution** — sparkline trend + per-rating-bucket bar chart with Codeforces tier colours (800 → Grandmaster)
- **Category Breakdown** — top 10 problem tags ranked by solve count, with accuracy badges (S / A / B / C / D grading)
- **Insights & Coaching** — automatic detection of weak tags (≥ 5 attempts, < 50 % accuracy), with a Gemini AI coach integration coming soon
- **Incremental sync** — only new submissions are fetched on each run; your existing data is never re-downloaded
- **First-run wizard** — interactive prompt asks for your handle, then quietly fetches everything in the background

---

## Project Structure

```
TrackForces/
├── main.py               # Entry point — builds and runs the live HUD
├── setup.py              # First-run wizard (handle prompt + initial data fetch)
├── .env                  # Database credentials (not committed in production)
│
├── core/
│   └── stats.py          # Stats aggregation layer (wraps db queries into clean dicts)
│
├── database/
│   └── db.py             # MariaDB handler — all SQL queries live here
│
└── services/
    └── cf_client.py      # Codeforces API client (user info + submissions)
```

---

## Database Schema

TrackForces expects a MariaDB database named `TrackForces` with the following tables. Run this SQL before the first launch:

```sql
CREATE DATABASE IF NOT EXISTS TrackForces;
USE TrackForces;

CREATE TABLE IF NOT EXISTS User (
    handle       VARCHAR(50) PRIMARY KEY,
    rating       INT,
    last_sub_id  BIGINT,
    is_init      TINYINT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Question (
    id              VARCHAR(20) PRIMARY KEY,
    contest_id      INT,
    problem_index   VARCHAR(5),
    rating          INT
);

CREATE TABLE IF NOT EXISTS Submissions (
    submission_id  BIGINT PRIMARY KEY,
    user_handle    VARCHAR(50),
    question_id    VARCHAR(20),
    verdict        VARCHAR(20),
    FOREIGN KEY (user_handle)  REFERENCES User(handle),
    FOREIGN KEY (question_id)  REFERENCES Question(id)
);

CREATE TABLE IF NOT EXISTS Category (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(100) UNIQUE
);

CREATE TABLE IF NOT EXISTS Question_Categories (
    question_id  VARCHAR(20),
    category_id  INT,
    PRIMARY KEY (question_id, category_id),
    FOREIGN KEY (question_id)  REFERENCES Question(id),
    FOREIGN KEY (category_id)  REFERENCES Category(id)
);
```

---

## Configuration

Copy the `.env` file to the project root and fill in your credentials:

```ini
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=TrackForces
```


---

## Usage

```bash
python main.py
```

**First run:** You will be prompted for your Codeforces handle. TrackForces will then fetch your entire submission history (this can take a minute for large accounts) and store it locally.

**Subsequent runs:** Only new submissions since your last run are synced, so the dashboard appears almost immediately.

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + C` | Quit |

> `[R] Refresh` and `[T] AI Tips` shown in the footer are planned for an upcoming release.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `rich` | Terminal UI — panels, tables, live layout |
| `mariadb` | MariaDB / MySQL connector |
| `python-dotenv` | Loads `.env` credentials |
| `questionary` | Interactive first-run prompt |
| `requests` | Codeforces API calls |

All dependencies are listed in the virtual environment included in the repository. For a clean install, use the provided setup script (Linux) or follow the manual steps (Windows).

---

## Roadmap

- [ ] `--tips` flag: Gemini AI coaching with personalised improvement advice
- [ ] `[R]` hotkey: in-dashboard manual refresh
- [ ] Contest performance timeline
- [ ] Exportable stats (JSON / CSV)

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you'd like to change.

---

## License

MIT — see `LICENSE` for details.

---

<div align="center">
  Made with ⚡ by <a href="https://github.com/AjayyXD">AjayyXD</a> &nbsp;•&nbsp; <a href="https://github.com/AjayyXD/TrackForces">github.com/AjayyXD/TrackForces</a>
</div>