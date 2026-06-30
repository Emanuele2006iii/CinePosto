#!/bin/bash
# CinePosto Scraper — installazione su VM Linux con systemd timer.
# Eseguire dalla VM dopo `git clone` del monorepo.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="cineposto-scraper"

echo "=== CinePosto Scraper Setup ==="

# 1. venv + install (pyproject.toml è single source of truth)
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "Creo venv..."
    python3 -m venv "$PROJECT_DIR/.venv"
fi
echo "Installo dipendenze..."
"$PROJECT_DIR/.venv/bin/pip" install -e "$PROJECT_DIR[dev]" --quiet

# 2. output dirs
mkdir -p "$PROJECT_DIR/output/history" "$PROJECT_DIR/output/cache"

# 3. systemd unit + timer
echo "Installo systemd service + timer..."
sudo cp "$SCRIPT_DIR/$SERVICE_NAME.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/$SERVICE_NAME.timer"   /etc/systemd/system/
sudo systemctl daemon-reload

# 4. logrotate
echo "Installo logrotate..."
sudo cp "$SCRIPT_DIR/$SERVICE_NAME-logrotate" /etc/logrotate.d/$SERVICE_NAME

# 5. enable + start del timer (NON del .service: il timer lo invoca a 03:00)
sudo systemctl enable --now "$SERVICE_NAME.timer"

echo ""
echo "=== Installato! ==="
echo ""
echo "Comandi utili:"
echo "  sudo systemctl list-timers $SERVICE_NAME.timer    # vedi prossima esecuzione"
echo "  sudo systemctl status $SERVICE_NAME.service       # ultima run"
echo "  sudo systemctl start $SERVICE_NAME.service        # forza run manuale subito"
echo "  sudo journalctl -u $SERVICE_NAME.service -f       # follow log"
echo ""
echo "Run manuale dev (senza systemd):"
echo "  cd $PROJECT_DIR && source .venv/bin/activate && python -m scraper.main --once"
