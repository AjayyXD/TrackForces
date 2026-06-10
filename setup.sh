#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  TrackForces — Linux Setup Script
#  Supports: Debian/Ubuntu, Arch/Manjaro, Fedora/RHEL/CentOS
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}${BOLD}[TrackForces]${RESET} $*"; }
success() { echo -e "${GREEN}${BOLD}[✔]${RESET} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}[!]${RESET} $*"; }
die()     { echo -e "${RED}${BOLD}[✘]${RESET} $*" >&2; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
cat << 'EOF'
  ████████╗██████╗  █████╗  ██████╗██╗  ██╗    ███████╗ ██████╗ ██████╗  ██████╗███████╗███████╗
     ██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔════╝
     ██║   ██████╔╝███████║██║     █████╔╝     █████╗  ██║   ██║██████╔╝██║     █████╗  ███████╗
     ██║   ██╔══██╗██╔══██║██║     ██╔═██╗     ██╔══╝  ██║   ██║██╔══██╗██║     ██╔══╝  ╚════██║
     ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗    ██║     ╚██████╔╝██║  ██║╚██████╗███████╗███████║
     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝
EOF
echo -e "${RESET}"
echo -e "${BOLD}  ⚡ TrackForces — Linux Setup${RESET}"
echo -e "  ${CYAN}github.com/AjayyXD/TrackForces${RESET}"
echo ""

# ── Must run from the TrackForces project root ────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

[[ -f "main.py" ]] || die "Run this script from the TrackForces project root."

# ── Detect distro ─────────────────────────────────────────────────────────────
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        DISTRO_ID="${ID,,}"                        # lowercase
        DISTRO_LIKE="${ID_LIKE:+${ID_LIKE,,}}"    # empty string if unset
    elif command -v lsb_release &>/dev/null; then
        DISTRO_ID="$(lsb_release -si | tr '[:upper:]' '[:lower:]')"
        DISTRO_LIKE=""
    else
        die "Cannot detect Linux distribution."
    fi

    if [[ "$DISTRO_ID" =~ ^(ubuntu|debian|linuxmint|pop|elementary|kali|zorin)$ ]] \
       || [[ "$DISTRO_LIKE" =~ debian ]]; then
        DISTRO_FAMILY="debian"
    elif [[ "$DISTRO_ID" =~ ^(arch|manjaro|endeavouros|garuda|artix)$ ]] \
         || [[ "$DISTRO_LIKE" =~ arch ]]; then
        DISTRO_FAMILY="arch"
    elif [[ "$DISTRO_ID" =~ ^(fedora|rhel|centos|rocky|almalinux|ol)$ ]] \
         || [[ "$DISTRO_LIKE" =~ (fedora|rhel) ]]; then
        DISTRO_FAMILY="fedora"
    else
        die "Unsupported distribution: $DISTRO_ID. Supported families: Debian/Ubuntu, Arch, Fedora/RHEL."
    fi

    info "Detected distro family: ${BOLD}$DISTRO_FAMILY${RESET} (${DISTRO_ID})"
}

# ── Privilege check ───────────────────────────────────────────────────────────
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        SUDO=""
    elif command -v sudo &>/dev/null; then
        SUDO="sudo"
        info "Script will use sudo for privileged commands."
    else
        die "This script requires root or sudo access."
    fi
}

# ── Install system packages ───────────────────────────────────────────────────
install_system_deps() {
    info "Installing system dependencies..."

    case "$DISTRO_FAMILY" in
        debian)
            $SUDO apt-get update -qq
            $SUDO apt-get install -y \
                python3 python3-pip python3-venv \
                mariadb-server mariadb-client \
                libmariadb-dev pkg-config \
                curl git
            ;;
        arch)
            $SUDO pacman -Sy --noconfirm --needed \
                python python-pip \
                mariadb \
                base-devel \
                curl git
            # Arch ships MariaDB uninitialized
            if ! $SUDO mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql &>/dev/null 2>&1; then
                warn "mariadb-install-db failed (may already be initialised — continuing)"
            fi
            ;;
        fedora)
            if command -v dnf &>/dev/null; then
                PKG_MGR="dnf"
            else
                PKG_MGR="yum"
            fi
            $SUDO $PKG_MGR install -y \
                python3 python3-pip \
                mariadb-server mariadb \
                mariadb-connector-c-devel \
                gcc python3-devel \
                curl git
            ;;
    esac

    success "System packages installed."
}

# ── Ensure MariaDB is running ─────────────────────────────────────────────────
start_mariadb() {
    info "Starting MariaDB service..."

    # Try systemd first, fall back to service
    if command -v systemctl &>/dev/null && systemctl list-units --type=service &>/dev/null 2>&1; then
        $SUDO systemctl enable mariadb  &>/dev/null || $SUDO systemctl enable mysql  &>/dev/null || true
        $SUDO systemctl start  mariadb  2>/dev/null || $SUDO systemctl start  mysql  2>/dev/null || true
    elif command -v service &>/dev/null; then
        $SUDO service mariadb start 2>/dev/null || $SUDO service mysql start 2>/dev/null || true
    fi

    # Wait up to 15 s for MariaDB to become ready
    local retries=15
    until mysqladmin ping --silent 2>/dev/null || mariadb-admin ping --silent 2>/dev/null; do
        ((retries--))
        [[ $retries -eq 0 ]] && die "MariaDB did not start in time. Check logs: journalctl -u mariadb"
        sleep 1
    done

    success "MariaDB is running."
}

# ── Generate a random password ────────────────────────────────────────────────
gen_password() {
    # Try multiple sources; always 24 printable ASCII chars, no shell-special chars
    python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '!@#%^&*'
print(''.join(secrets.choice(chars) for _ in range(24)))
"
}

# ── Create DB user + database + tables ───────────────────────────────────────
setup_database() {
    info "Setting up MariaDB database and user..."

    DB_NAME="TrackForces"
    DB_USER="trackforces_user"
    DB_PASS="$(gen_password)"
    DB_HOST="127.0.0.1"
    DB_PORT="3306"

    # Determine how to run privileged SQL
    # On fresh installs root has no password; try socket auth then empty password
    run_sql() {
        if $SUDO mariadb -u root --silent -e "$1" 2>/dev/null; then return 0; fi
        if $SUDO mysql    -u root --silent -e "$1" 2>/dev/null; then return 0; fi
        # Last resort: ask for root password
        warn "Could not connect as root without a password."
        read -rsp "  Enter MariaDB root password: " MARIA_ROOT_PASS; echo ""
        mariadb -u root -p"$MARIA_ROOT_PASS" --silent -e "$1"
    }

    run_sql "
        CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci;

        CREATE OR REPLACE USER '${DB_USER}'@'localhost'
            IDENTIFIED BY '${DB_PASS}';
        CREATE OR REPLACE USER '${DB_USER}'@'127.0.0.1'
            IDENTIFIED BY '${DB_PASS}';

        GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
        GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
        FLUSH PRIVILEGES;
    "

    # Create tables
    run_sql "
        USE \`${DB_NAME}\`;

        CREATE TABLE IF NOT EXISTS User (
            handle       VARCHAR(50)  PRIMARY KEY,
            rating       INT,
            last_sub_id  BIGINT,
            is_init      TINYINT(1)   DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS Question (
            id              VARCHAR(20)  PRIMARY KEY,
            contest_id      INT,
            problem_index   VARCHAR(5),
            rating          INT
        );

        CREATE TABLE IF NOT EXISTS Submissions (
            submission_id  BIGINT       PRIMARY KEY,
            user_handle    VARCHAR(50),
            question_id    VARCHAR(20),
            verdict        VARCHAR(20),
            FOREIGN KEY (user_handle)  REFERENCES User(handle),
            FOREIGN KEY (question_id)  REFERENCES Question(id)
        );

        CREATE TABLE IF NOT EXISTS Category (
            id    INT AUTO_INCREMENT  PRIMARY KEY,
            name  VARCHAR(100)        UNIQUE
        );

        CREATE TABLE IF NOT EXISTS Question_Categories (
            question_id  VARCHAR(20),
            category_id  INT,
            PRIMARY KEY (question_id, category_id),
            FOREIGN KEY (question_id)  REFERENCES Question(id),
            FOREIGN KEY (category_id)  REFERENCES Category(id)
        );
    "

    success "Database '${DB_NAME}' and tables created."

    # Write .env (overwrite to keep it authoritative)
    cat > .env << EOF
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
EOF

    chmod 600 .env   # Only owner can read credentials
    success ".env written with generated credentials (chmod 600)."

    # Export for use later in this script
    export DB_USER DB_PASS DB_HOST DB_PORT DB_NAME
}

# ── Python virtual environment + pip packages ─────────────────────────────────
setup_python_env() {
    info "Setting up Python virtual environment..."

    # Use existing venv if present, create if not
    if [[ ! -f venv/bin/activate ]]; then
        python3 -m venv venv
    fi

    # shellcheck source=/dev/null
    source venv/bin/activate

    pip install --quiet --upgrade pip

    # Install project dependencies
    pip install --quiet \
        rich \
        mariadb \
        python-dotenv \
        questionary \
        requests

    success "Python environment ready."
}

# ── Register the 'tf' command ─────────────────────────────────────────────────
install_tf_command() {
    info "Installing 'tf' command..."

    TF_DIR="$SCRIPT_DIR"
    TF_VENV="$TF_DIR/venv/bin/python"
    TF_MAIN="$TF_DIR/main.py"

    # Write launcher script
    TF_LAUNCHER="/usr/local/bin/tf"

    $SUDO tee "$TF_LAUNCHER" > /dev/null << EOF
#!/usr/bin/env bash
# TrackForces launcher — generated by setup.sh
exec "${TF_VENV}" "${TF_MAIN}" "\$@"
EOF

    $SUDO chmod +x "$TF_LAUNCHER"
    success "'tf' command installed at ${TF_LAUNCHER}."

    # Verify it's on PATH
    if command -v tf &>/dev/null; then
        success "Verified: 'tf' is accessible from PATH."
    else
        warn "'tf' installed but not found on PATH. You may need to open a new terminal."
    fi
}

# ── Sanity check: test DB connection from Python ──────────────────────────────
verify_db_connection() {
    info "Verifying database connection..."

    # shellcheck source=/dev/null
    source venv/bin/activate

    python3 - << PYEOF
import os, sys
from dotenv import load_dotenv
load_dotenv(dotenv_path="${SCRIPT_DIR}/.env")
try:
    import mariadb
    conn = mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    conn.close()
    print("  DB connection OK")
except Exception as e:
    print(f"  DB connection FAILED: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    success "Database connection verified."
}

# ── Summary ───────────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${GREEN}${BOLD}  ⚡ TrackForces setup complete!${RESET}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    echo -e "  ${BOLD}Run TrackForces:${RESET}  ${CYAN}tf${RESET}"
    echo -e "  ${BOLD}Credentials:${RESET}      ${CYAN}${SCRIPT_DIR}/.env${RESET}  ${YELLOW}(keep this private)${RESET}"
    echo -e "  ${BOLD}MariaDB user:${RESET}     ${CYAN}trackforces_user${RESET}  (database-scoped only)"
    echo ""
    echo -e "  On first run you will be asked for your Codeforces handle."
    echo -e "  Initial data fetch may take a minute for large accounts."
    echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    detect_distro
    check_sudo
    install_system_deps
    start_mariadb
    setup_database
    setup_python_env
    install_tf_command
    verify_db_connection
    print_summary
}

main "$@"