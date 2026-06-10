#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell
import cairo
import math
import os
import socket
import threading
import tomllib
import subprocess

def load_config():
    paths = [
        os.path.expanduser("~/.config/hypr-radial-menu/config.toml"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return tomllib.load(f)
            except Exception as e:
                print(f"Error loading config at {p}: {e}")
    
    # Minimal fallback configuration
    return {
        "menu": {
            "radius_outer": 160,
            "radius_inner": 55,
            "deadzone": 25,
            "font_family_label": "Sans",
            "font_family_icon": "Noto Color Emoji",
            "font_size_label": 11,
            "font_size_icon": 22
        },
        "slices": []
    }

class RadialMenuDrawingArea(Gtk.DrawingArea):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.connect("draw", self.on_draw)
        
    def on_draw(self, widget, cr):
        # 1. Clear background to be transparent
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        
        # 2. Get center coordinate of window allocation
        cx = self.get_allocated_width() / 2
        cy = self.get_allocated_height() / 2
        
        n_slices = len(self.parent.slices)
        if n_slices == 0:
            return
            
        slice_w = 2 * math.pi / n_slices
        # Gap between slices in radians (approx 1.5 degrees)
        gap = 0.026
        
        # 3. Draw each slice
        for i, slice_data in enumerate(self.parent.slices):
            cr.new_path()
            scale = self.parent.slice_scales[i]
            # Hover factor t goes from 0.0 (unhovered) to 1.0 (hovered)
            t = (scale - 1.0) / 0.08
            t = max(0.0, min(1.0, t))
            
            # Smooth proportional scaling of radii to prevent shape deformation
            r_out = self.parent.radius_outer * scale
            r_in = self.parent.radius_inner * scale
            
            center_angle = -math.pi / 2 + i * slice_w
            start_angle = center_angle - slice_w / 2 + gap
            end_angle = center_angle + slice_w / 2 - gap
            
            # Draw sector path
            cr.arc(cx, cy, r_out, start_angle, end_angle)
            cr.arc_negative(cx, cy, r_in, end_angle, start_angle)
            cr.close_path()
            
            # Fill sector background (interpolate from obsidian slate to violet-cyan gradient)
            x1 = cx + r_in * math.cos(center_angle)
            y1 = cy + r_in * math.sin(center_angle)
            x2 = cx + r_out * math.cos(center_angle)
            y2 = cy + r_out * math.sin(center_angle)
            pat = cairo.LinearGradient(x1, y1, x2, y2)
            
            # Obsidian base: rgba(0.08, 0.08, 0.12, 0.72)
            # Hover start (Indigo): rgba(0.47, 0.14, 1.0, 0.85)
            # Hover end (Cyan): rgba(0.0, 0.60, 1.0, 0.90)
            r0 = 0.08 + (0.47 - 0.08) * t
            g0 = 0.08 + (0.14 - 0.08) * t
            b0 = 0.12 + (1.0 - 0.12) * t
            a0 = 0.72 + (0.85 - 0.72) * t
            pat.add_color_stop_rgba(0.0, r0, g0, b0, a0)
            
            r1 = 0.08 + (0.0 - 0.08) * t
            g1 = 0.08 + (0.60 - 0.08) * t
            b1 = 0.12 + (1.0 - 0.12) * t
            a1 = 0.72 + (0.90 - 0.72) * t
            pat.add_color_stop_rgba(1.0, r1, g1, b1, a1)
            
            cr.set_source(pat)
            cr.fill_preserve()
            
            # Draw borders (interpolate from subtle white/transparent to glow blue)
            br = 1.0 + (0.5 - 1.0) * t
            bg = 1.0 + (0.8 - 1.0) * t
            bb = 1.0
            ba = 0.06 + (0.6 - 0.06) * t
            lw = 1.0 + 1.0 * t
            
            cr.set_source_rgba(br, bg, bb, ba)
            cr.set_line_width(lw)
            cr.stroke()
            
            # Calculate position for label & icon (middle of the sector)
            r_text = r_in + (r_out - r_in) * 0.52
            tx = cx + r_text * math.cos(center_angle)
            ty = cy + r_text * math.sin(center_angle)
            
            icon = slice_data.get('icon', '')
            label = slice_data.get('label', '')
            
            # Choose text sizes and colors based on t
            icon_size = self.parent.font_size_icon * (1.0 + 0.12 * t)
            label_size = self.parent.font_size_label * (1.0 + 0.06 * t)
            icon_alpha = 0.7 + 0.3 * t
            label_alpha = 0.75 + 0.25 * t
            
            # Render Text & Icon
            if icon and label:
                # Draw Icon (Noto Color Emoji)
                cr.select_font_face(self.parent.font_family_icon, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                cr.set_font_size(icon_size)
                cr.set_source_rgba(1.0, 1.0, 1.0, icon_alpha)
                ext = cr.text_extents(icon)
                ix = tx - (ext.width / 2 + ext.x_bearing)
                iy = ty - 8 - (ext.height / 2 + ext.y_bearing)
                cr.move_to(ix, iy)
                cr.show_text(icon)
                
                # Draw Label (Outfit/Inter/Sans)
                font_weight = cairo.FONT_WEIGHT_BOLD if t > 0.5 else cairo.FONT_WEIGHT_NORMAL
                cr.select_font_face(self.parent.font_family, cairo.FONT_SLANT_NORMAL, font_weight)
                cr.set_font_size(label_size)
                cr.set_source_rgba(1.0, 1.0, 1.0, label_alpha)
                ext = cr.text_extents(label)
                lx = tx - (ext.width / 2 + ext.x_bearing)
                ly = ty + 14 - (ext.height / 2 + ext.y_bearing)
                cr.move_to(lx, ly)
                cr.show_text(label)
            elif icon:
                cr.select_font_face(self.parent.font_family_icon, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
                cr.set_font_size(icon_size)
                cr.set_source_rgba(1.0, 1.0, 1.0, icon_alpha)
                ext = cr.text_extents(icon)
                ix = tx - (ext.width / 2 + ext.x_bearing)
                iy = ty - (ext.height / 2 + ext.y_bearing)
                cr.move_to(ix, iy)
                cr.show_text(icon)
            elif label:
                font_weight = cairo.FONT_WEIGHT_BOLD if t > 0.5 else cairo.FONT_WEIGHT_NORMAL
                cr.select_font_face(self.parent.font_family, cairo.FONT_SLANT_NORMAL, font_weight)
                cr.set_font_size(label_size)
                cr.set_source_rgba(1.0, 1.0, 1.0, label_alpha)
                ext = cr.text_extents(label)
                lx = tx - (ext.width / 2 + ext.x_bearing)
                ly = ty - (ext.height / 2 + ext.y_bearing)
                cr.move_to(lx, ly)
                cr.show_text(label)
                
        # 4. Draw Center Deadzone circle
        cr.new_path()
        cr.arc(cx, cy, self.parent.radius_inner - 6, 0, 2 * math.pi)
        cr.set_source_rgba(0.04, 0.04, 0.06, 0.85)
        cr.fill_preserve()
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.08)
        cr.set_line_width(1.5)
        cr.stroke()

class RadialMenuApp:
    def __init__(self):
        self.config = load_config()
        self.slices = self.config.get('slices', [])
        
        # Load parameters
        m_cfg = self.config.get('menu', {})
        self.radius_outer = m_cfg.get('radius_outer', 160)
        self.radius_inner = m_cfg.get('radius_inner', 55)
        self.deadzone = m_cfg.get('deadzone', 25)
        self.font_family = m_cfg.get('font_family_label', "Sans")
        self.font_family_icon = m_cfg.get('font_family_icon', "Noto Color Emoji")
        self.font_size_label = m_cfg.get('font_size_label', 11)
        self.font_size_icon = m_cfg.get('font_size_icon', 22)
        
        # Window size is diameter + padding
        self.window_width = self.radius_outer * 2 + 40
        self.window_height = self.radius_outer * 2 + 40
        
        # State variables
        self.running = True
        self.tracking = False
        self.center_x = 0
        self.center_y = 0
        self.hovered_slice = -1
        self.slice_scales = [1.0] * len(self.slices)
        self.timeout_id = None
        
        # Initialize GTK Window
        self.window = Gtk.Window()
        self.window.set_title("Hypr Radial Menu")
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_size_request(self.window_width, self.window_height)
        
        # Setup visual for transparency
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.window.set_visual(visual)
            
        # Initialize Layer Shell
        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_namespace(self.window, "radial-menu")
        
        # Anchors (needed to position using margins)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, False)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, False)
        
        # Add drawing area
        self.drawing_area = RadialMenuDrawingArea(self)
        self.drawing_area.set_size_request(self.window_width, self.window_height)
        self.window.add(self.drawing_area)
        
        # Window close handler
        self.window.connect("destroy", self.on_destroy)
        
        # Start Unix Socket listener thread
        self.socket_thread = threading.Thread(target=self.run_socket_server, daemon=True)
        self.socket_thread.start()

    def run_socket_server(self):
        socket_path = f"/tmp/hypr-radial-menu-{os.getuid()}.sock"
        if os.path.exists(socket_path):
            try:
                os.remove(socket_path)
            except OSError:
                pass
                
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(socket_path)
        s.listen(5)
        os.chmod(socket_path, 0o600)
        
        while self.running:
            try:
                conn, addr = s.accept()
                data = conn.recv(1024)
                if data:
                    cmd = data.decode('utf-8').strip()
                    GLib.idle_add(self.handle_ipc_command, cmd)
                conn.close()
            except Exception as e:
                if not self.running:
                    break
                    
        try:
            os.remove(socket_path)
        except OSError:
            pass

    def handle_ipc_command(self, cmd):
        if cmd == "press":
            self.show_menu()
        elif cmd == "release":
            self.hide_menu()
        elif cmd == "quit":
            self.quit()

    def get_hyprland_cursor_pos(self):
        try:
            sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
            runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
            path = os.path.join(runtime_dir, "hypr", sig, ".socket.sock")
            if not os.path.exists(path):
                path = f"/tmp/hypr/{sig}/.socket.sock"
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(path)
                s.sendall(b"cursorpos")
                res = s.recv(1024).decode('utf-8').strip()
                parts = res.split(',')
                return int(parts[0]), int(parts[1])
        except Exception as e:
            return 0, 0

    def show_menu(self):
        # 1. Reload configuration in case it changed
        self.config = load_config()
        self.slices = self.config.get('slices', [])
        m_cfg = self.config.get('menu', {})
        self.radius_outer = m_cfg.get('radius_outer', 160)
        self.radius_inner = m_cfg.get('radius_inner', 55)
        self.deadzone = m_cfg.get('deadzone', 25)
        self.font_family = m_cfg.get('font_family_label', "Sans")
        self.font_family_icon = m_cfg.get('font_family_icon', "Noto Color Emoji")
        self.font_size_label = m_cfg.get('font_size_label', 11)
        self.font_size_icon = m_cfg.get('font_size_icon', 22)
        
        self.window_width = self.radius_outer * 2 + 40
        self.window_height = self.radius_outer * 2 + 40
        self.window.set_size_request(self.window_width, self.window_height)
        self.window.resize(1, 1)
        self.drawing_area.set_size_request(self.window_width, self.window_height)
        
        # 2. Get global cursor position
        x_g, y_g = self.get_hyprland_cursor_pos()
        self.center_x = x_g
        self.center_y = y_g
        
        # 3. Find the monitor hosting the cursor
        display = Gdk.Display.get_default()
        n_monitors = display.get_n_monitors()
        target_monitor = display.get_monitor(0)
        rel_x = x_g
        rel_y = y_g
        scale = 1
        
        for i in range(n_monitors):
            m = display.get_monitor(i)
            geom = m.get_geometry()
            if geom.x <= x_g < geom.x + geom.width and geom.y <= y_g < geom.y + geom.height:
                target_monitor = m
                rel_x = x_g - geom.x
                rel_y = y_g - geom.y
                scale = m.get_scale_factor()
                break
                
        # 4. Bind window to the correct monitor
        GtkLayerShell.set_monitor(self.window, target_monitor)
        
        # 5. Position centered at cursor (adjusting for monitor-scale factor)
        logical_x = rel_x / scale
        logical_y = rel_y / scale
        
        margin_left = int(logical_x - self.window_width / 2)
        margin_top = int(logical_y - self.window_height / 2)
        
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.LEFT, margin_left)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, margin_top)
        
        # Reset state & show
        self.hovered_slice = -1
        self.slice_scales = [1.0] * len(self.slices)
        self.window.show_all()
        
        # Start cursor tracking tick
        self.tracking = True
        self.track_mouse()
        if self.timeout_id is None:
            self.timeout_id = GLib.timeout_add(12, self.on_track_tick)

    def on_track_tick(self):
        if not self.tracking:
            return False
        
        self.track_mouse()
        
        # Update scales (Lerp animation for smooth scaling)
        changed = False
        for i in range(len(self.slices)):
            target = 1.08 if i == self.hovered_slice else 1.0
            diff = target - self.slice_scales[i]
            if abs(diff) > 0.005:
                self.slice_scales[i] += diff * 0.25
                changed = True
            else:
                self.slice_scales[i] = target
                
        if changed:
            self.drawing_area.queue_draw()
            
        return True

    def track_mouse(self):
        x_g, y_g = self.get_hyprland_cursor_pos()
        dx = x_g - self.center_x
        dy = y_g - self.center_y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < self.deadzone:
            new_hover = -1
        else:
            # Calculate angle in radians [0, 2pi] clockwise
            angle_rad = math.atan2(dy, dx)
            if angle_rad < 0:
                angle_rad += 2 * math.pi
            
            # Shift so that top (up, 3pi/2) is 0
            shifted = (angle_rad + 0.5 * math.pi) % (2 * math.pi)
            
            n_slices = len(self.slices)
            slice_w = 2 * math.pi / n_slices
            new_hover = int((shifted + slice_w / 2) % (2 * math.pi) / slice_w)
            if new_hover >= n_slices:
                new_hover = 0
                
        if new_hover != self.hovered_slice:
            self.hovered_slice = new_hover
            # Trigger immediate redraw for snappy visual feedback
            self.drawing_area.queue_draw()

    def hide_menu(self):
        self.tracking = False
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            
        self.window.hide()
        
        # Execute action
        if self.hovered_slice != -1:
            slice_data = self.slices[self.hovered_slice]
            self.execute_action(slice_data)
            
        self.hovered_slice = -1
        self.slice_scales = [1.0] * len(self.slices)
        self.drawing_area.queue_draw()

    def execute_action(self, slice_data):
        action_type = slice_data.get('type', 'command')
        action = slice_data.get('action', '')
        if not action:
            return
            
        if action_type == 'command':
            subprocess.Popen(action, shell=True, preexec_fn=os.setsid)
        elif action_type == 'shortcut':
            # Dispatch shortcut via Hyprland sendshortcut
            cmd = ["hyprctl", "dispatch", "sendshortcut", f"{action},"]
            subprocess.Popen(cmd)
        elif action_type == 'hyprland':
            # Run Hyprland dispatcher command directly
            cmd = ["hyprctl", "dispatch"] + action.split()
            subprocess.Popen(cmd)

    def on_destroy(self, widget):
        self.quit()

    def quit(self):
        self.running = False
        Gtk.main_quit()

if __name__ == "__main__":
    app = RadialMenuApp()
    Gtk.main()
