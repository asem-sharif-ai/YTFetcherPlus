#!/bin/bash
set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$INSTALL_DIR/Run.sh"
LAUNCHER="/usr/local/bin/ytf"

echo "[YTFetcherPlus] Setup: Initializing in $INSTALL_DIR"

chmod +x "$RUN_SCRIPT"

echo "[YTFetcherPlus] Environment: Creating Virtual Environment..."
python3 -m venv "$INSTALL_DIR/env"

echo "[YTFetcherPlus] Dependencies: Installing Core Packages..."
"$INSTALL_DIR/env/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/env/bin/pip" install PyQt6 Pillow yt-dlp youtube-transcript-api -q

echo "[YTFetcherPlus] System: Creating Global Command 'ytf'..."
sudo rm -f "$LAUNCHER"
sudo tee "$LAUNCHER" > /dev/null <<EOF
#!/bin/bash
exec "$RUN_SCRIPT" "\$@"
EOF

sudo chmod +x "$LAUNCHER"

echo "[YTFetcherPlus] Finished: Installed Successfully"
echo "[YTFetcherPlus] Usage: Type 'ytf' or 'ytf [URL]'"