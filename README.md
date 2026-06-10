# 🌐 Hypr Radial Menu (Pie Menu)

A highly responsive, beautiful, hardware-accelerated radial menu for **Hyprland** (Wayland) written in Python and C. It allows you to bind a mouse button (like a side button) to open a circular overlay containing custom actions, window management shortcuts, or applications around your cursor.

![Preview](https://github.com/cachyos/cachyos-artwork/raw/main/cachyos-wallpapers/neon_grid.png) *(Note: Add your own custom wallpaper/aesthetic to make it yours!)*

---

## ✨ Features

- ⚡ **Zero Latency**: Powered by a C client (`hypr-radial-menu-client`) communicating via Unix sockets for instant key press and release response times.
- 📐 **Monitor Aware**: Correctly handles multi-monitor layouts and high-DPI scaling.
- 🎨 **Gorgeous Design**: Built using GTK 3, Cairo, and GTK Layer Shell. Supports smooth scale-up hover animations (spring/lerp interpolation) and glowing neon accent gradients.
- 🌫️ **Frosted Glass (Blur)**: Leverages Hyprland's native compositor blur rules for an ultra-premium glassmorphism effect.
- 🔧 **Fully Customizable**: Simple TOML configuration for adding commands, shortcuts (`Ctrl+C`, `Ctrl+V`, etc.), or native Hyprland dispatchers.

---

## 🛠️ How it Works

1. **Daemon (`daemon.py`)**: Runs in the background and keeps the radial menu window ready but hidden.
2. **Client (`hypr-radial-menu-client`)**: A lightweight C executable that instantly signals the daemon on button press and release.
3. **Hyprland Binds**: Intercepts the mouse button. Press triggers the menu; release triggers the selected action.

---

## 🚀 Installation & Setup

### 📋 Prerequisites
Before setting up the menu, make sure you have the following dependencies installed:
- **GTK 3** & **PyGObject** (for the GUI window)
- **gtk-layer-shell** (for proper overlay alignment under Wayland)
- **grim** & **slurp** (required for the default **Screenshot** action)
- **wl-clipboard** (required for copying screenshots and clipboard actions)

### ⚙️ Installation

1. Clone the repository and run the installer:
   ```bash
   git clone git@github.com:neruson27/hypr-radial-menu.git
   cd hypr-radial-menu
   ./install.sh
   ```
2. Open your Hyprland configuration file (usually `~/.config/hypr/hyprland.conf`) and add the following lines:

### 1. Autostart Daemon
Add this so the menu runs on startup (replace `/path/to/` with the actual path where you cloned the repository):
```ini
exec-once = /path/to/hypr-radial-menu/daemon.py
```

### 2. Mouse Binds
Add this to bind your mouse's extra button. 
- `mouse:275` represents the **Side Button (Back)**.
- `mouse:276` represents the **Side Button (Forward)**.

Choose the one you prefer (replace `/path/to/` with the actual path):
```ini
# Radial Menu bindings (BTN_SIDE / Back button)
bind = , mouse:275, exec, /path/to/hypr-radial-menu/hypr-radial-menu-client press
bindr = , mouse:275, exec, /path/to/hypr-radial-menu/hypr-radial-menu-client release
```

### 3. Glassmorphism Blur (Highly Recommended!)
Add these lines to enable hardware-accelerated blur under the transparent radial menu:
```ini
# Beautiful blur effect under the radial menu
layerrule = blur, radial-menu
layerrule = ignorealpha 0.5, radial-menu
```

---

## ⚙️ Customization (`config.toml`)

Your active configuration is stored at:
📂 `~/.config/hypr-radial-menu/config.toml`

You can edit this file to change the radius, fonts, deadzone, or to customize the menu slices. The menu will automatically reload your configuration every time you press the button!

### Action Types:
- `command`: Executes a background shell command (e.g. `kitty`, `firefox`, or `grim -g "$(slurp)" - | wl-copy`).
- `shortcut`: Simulates keyboard shortcuts sent to the active window (e.g. `CTRL, C` or `ALT, F4`).
- `hyprland`: Executes a native Hyprland dispatcher command (e.g. `killactive` to close a window, or `togglefloating`).

### Default Slices:
1. **Terminal** (Kitty)
2. **Screenshot** (Grim + Slurp) *(Note: Requires `grim`, `slurp`, and `wl-clipboard` installed)*
3. **Copy** (Ctrl+C)
4. **Files** (Dolphin)
5. **Close Window** (Hyprland active window close)
6. **Float Window** (Hyprland active window toggle float)
7. **Paste** (Ctrl+V)
8. **Browser** (Firefox)

---

## 🧪 Quick Test

To test without logging out or restarting:
1. Start the daemon manually:
   ```bash
   /path/to/hypr-radial-menu/daemon.py &
   ```
2. Open the menu by sending a press signal:
   ```bash
   /path/to/hypr-radial-menu/hypr-radial-menu-client press
   ```
3. Close the menu and execute the hovered action:
   ```bash
   /path/to/hypr-radial-menu/hypr-radial-menu-client release
   ```
