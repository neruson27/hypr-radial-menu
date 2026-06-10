#!/bin/bash
set -e

# Target paths
CONFIG_DIR="$HOME/.config/hypr-radial-menu"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing Hypr Radial Menu ==="

# 1. Create config directory if not exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating configuration directory at $CONFIG_DIR..."
    mkdir -p "$CONFIG_DIR"
fi

# 2. Copy config.toml if it does not exist
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    echo "Copying default config.toml to $CONFIG_DIR..."
    cp "$INSTALL_DIR/config.toml" "$CONFIG_DIR/config.toml"
else
    echo "Configuration file already exists at $CONFIG_DIR/config.toml (skipping overwrite)"
fi

# 3. Make scripts executable
echo "Setting executable permissions..."
chmod +x "$INSTALL_DIR/daemon.py"

# 4. Compile the C client
echo "Compiling C client..."
make -C "$INSTALL_DIR"

echo ""
echo "=== Installation Successful! ==="
echo ""
echo "To activate the radial menu on your extra mouse button:"
echo "1. Open your Hyprland configuration file (usually ~/.config/hypr/hyprland.conf)"
echo "2. Add the following line to start the daemon on login:"
echo "   exec-once = $INSTALL_DIR/daemon.py"
echo ""
echo "3. Add the following lines to bind your mouse button (e.g., BTN_SIDE / mouse:275):"
echo "   # Radial Menu bindings (BTN_SIDE)"
echo "   bind = , mouse:275, exec, $INSTALL_DIR/hypr-radial-menu-client press"
echo "   bindr = , mouse:275, exec, $INSTALL_DIR/hypr-radial-menu-client release"
echo ""
echo "   Tip: If you want to use the other side button (BTN_EXTRA), use mouse:276 instead."
echo "4. Reload Hyprland (Super+Shift+R or your config reload key)."
echo "5. Run the daemon once manually to test immediately without logging out:"
echo "   $INSTALL_DIR/daemon.py &"
echo ""
