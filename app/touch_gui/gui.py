#!/usr/bin/env python3
"""Minimal touchscreen GUI for Cubatron using framebuffer + touch events.

Features (MVP):
- Touch login: select user, enter 6-digit PIN (on-screen keypad)
- Main screen: Preparar, Depósitos, Parada de emergencia
- Preparar: list recipes (requires token from PIN login or token file)
- Depósitos: show and adjust tank levels, save to backend

Behavior:
- If no token file is present the GUI starts in user-selection mode.
- After successful PIN login the GUI stores the JWT in memory and uses it.
- If a logged-in user doesn't interact for 40s, they are logged out and the GUI returns to user selection.
"""
import os
import sys
import time
import threading
from typing import Optional

os.environ.setdefault("SDL_FBDEV", "/dev/fb1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except Exception as exc:  # pragma: no cover - runtime dependency
    print("pygame is required:", exc)
    sys.exit(1)

try:
    import requests
except Exception as exc:  # pragma: no cover - runtime dependency
    print("requests is required:", exc)
    sys.exit(1)

try:
    from evdev import list_devices, InputDevice, ecodes
    EVDEV_AVAILABLE = True
except Exception:
    EVDEV_AVAILABLE = False


API_BASE = os.environ.get("CUBATRON_API_BASE", "http://127.0.0.1:8000/api")
TOKEN_FILES = ["/etc/cubatron/touch_token", "./touch_token"]


def load_token() -> Optional[str]:
    env = os.environ.get("CUBATRON_TOUCH_TOKEN")
    if env:
        return env.strip()
    for p in TOKEN_FILES:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                tok = fh.read().strip()
                if tok:
                    return tok
        except Exception:
            continue
    return None


def find_touch_device():
    if not EVDEV_AVAILABLE:
        return None
    for path in list_devices():
        try:
            dev = InputDevice(path)
            name = (dev.name or "").lower()
            if any(k in name for k in ("touch", "xpt", "ads7846", "tslib")):
                return dev
        except Exception:
            continue
    # fallback: return first device with ABS events
    for path in list_devices():
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            if ecodes.EV_ABS in caps:
                return dev
        except Exception:
            continue
    return None


def evdev_to_pygame(dev, screen_w, screen_h):
    try:
        abs_x = dev.absinfo(ecodes.ABS_X)
        abs_y = dev.absinfo(ecodes.ABS_Y)
        min_x, max_x = abs_x.min, abs_x.max
        min_y, max_y = abs_y.min, abs_y.max
    except Exception:
        min_x, max_x, min_y, max_y = 0, 4096, 0, 4096

    raw_x = None
    raw_y = None
    try:
        for e in dev.read_loop():
            if e.type == ecodes.EV_ABS:
                if e.code == ecodes.ABS_X:
                    raw_x = e.value
                elif e.code == ecodes.ABS_Y:
                    raw_y = e.value
            elif e.type == ecodes.EV_KEY and e.code == ecodes.BTN_TOUCH:
                if e.value == 1:
                    if raw_x is None or raw_y is None:
                        continue
                    try:
                        x = int((raw_x - min_x) / max(1, (max_x - min_x)) * (screen_w - 1))
                        y = int((raw_y - min_y) / max(1, (max_y - min_y)) * (screen_h - 1))
                    except Exception:
                        continue
                    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": 1})
                    pygame.event.post(ev)
                else:
                    ev = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (0, 0), "button": 1})
                    pygame.event.post(ev)
    except Exception:
        return


class Button:
    def __init__(self, rect, text, color=(200, 200, 200), fg=(0, 0, 0), callback=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.fg = fg
        self.callback = callback

    def draw(self, surf, font):
        pygame.draw.rect(surf, self.color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        txt = font.render(self.text, True, self.fg)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def contains(self, pos):
        return self.rect.collidepoint(pos)


class TouchGUI:
    def __init__(self):
        self.running = True
        self.token = load_token()
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

        # Display init: try hardware fb drivers first, fallback to dummy + manual framebuffer write
        self.fb_path = "/dev/fb1"
        self.fb_fd = None
        self.fb_info = None
        self.using_hw_display = False

        drivers = []
        env_driver = os.environ.get("SDL_VIDEODRIVER")
        if env_driver:
            drivers.append(env_driver)
        drivers.extend(["fbcon", "fbdev", "directfb", "dummy"])

        initialized = False
        for drv in drivers:
            if not drv:
                continue
            os.environ["SDL_VIDEODRIVER"] = drv
            try:
                # initialize only display subsystem to respect env driver choice
                pygame.display.quit()
                pygame.display.init()
                # create real display surface when supported
                surf = pygame.display.set_mode((480, 320))
                pygame.display.set_caption("Cubatron Touch GUI")
                self.screen = surf
                self.using_hw_display = drv != "dummy"
                initialized = True
                break
            except Exception:
                try:
                    pygame.display.quit()
                except Exception:
                    pass
                continue

        # If we initialized but are using the `dummy` driver, set up the framebuffer
        # writer so we can manually flush the offscreen surface to /dev/fb1.
        if initialized and not getattr(self, "using_hw_display", False):
            try:
                self._init_framebuffer()
            except Exception:
                # leave fb_fd as None if we can't open it
                self.fb_fd = None

        if not initialized:
            # final fallback: use dummy driver and create an offscreen surface
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.Surface((480, 320))
            self.using_hw_display = False
            # try to initialize framebuffer writer
            try:
                self._init_framebuffer()
            except Exception:
                self.fb_fd = None

        # fonts and timing
        try:
            pygame.font.init()
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 20)
        except Exception:
            self.font = None
            self.small_font = None

        self.clock = pygame.time.Clock()

        self.message = ""
        self.message_ttl = 0

        # session state
        self.current_user = None
        self.last_interaction = time.time()

        # touch login state
        self.touch_users = []
        self.selected_user = None
        self.pin_buffer = ""
        self.selection_time = 0

        # initial scene: show Home if no token, otherwise go to menu
        self.scene = "menu" if self.token else "home"
        self.recipes = []
        self.tanks = []

        self._setup_main_buttons()
        self._setup_home_buttons()

        dev = find_touch_device()
        if dev:
            t = threading.Thread(target=evdev_to_pygame, args=(dev, 480, 320), daemon=True)
            t.start()

        if not self.token:
            # preload users for touch login
            self.load_touch_users()

    def _setup_main_buttons(self):
        w, h = self.screen.get_size()
        bh = h // 3
        self.btn_prepare = Button((0, 0, w, bh), "Preparar", color=(80, 170, 240), callback=self.open_prepare)
        self.btn_tanks = Button((0, bh, w, bh), "Depósitos", color=(120, 200, 120), callback=self.open_tanks)
        self.btn_stop = Button((0, 2 * bh, w, bh), "PARADA EMERGENCIA", color=(220, 50, 50), fg=(255, 255, 255), callback=self.emergency_stop)

    def _setup_home_buttons(self):
        w, h = self.screen.get_size()
        # centered "Comenzar" button
        self.btn_start = Button((w // 2 - 80, 180, 160, 60), "Comenzar", color=(80, 170, 240), callback=lambda: self.set_scene_and_reload("user_select"))

    def show_message(self, text, seconds=2):
        self.message = text
        self.message_ttl = time.time() + seconds

    def emergency_stop(self):
        try:
            r = requests.post(f"{API_BASE}/machine/stop", timeout=5)
            if r.ok:
                self.show_message("Parada enviada", 3)
            else:
                self.show_message(f"Error: {r.status_code}", 3)
        except Exception as exc:
            self.show_message(f"Error: {exc}", 3)

    def open_prepare(self):
        self.scene = "prepare"
        self.load_recipes()

    def open_tanks(self):
        self.scene = "tanks"
        self.load_tanks()

    def load_recipes(self):
        if not self.token:
            self.show_message("Token no encontrado. Accede con PIN", 6)
            self.recipes = []
            return
        try:
            r = self.session.get(f"{API_BASE}/drinks/recipes", timeout=5)
            if r.ok:
                self.recipes = r.json()
            else:
                self.show_message(f"Error recetas: {r.status_code}", 3)
                self.recipes = []
        except Exception as exc:
            self.show_message(f"Error recetas: {exc}", 3)
            self.recipes = []

    def load_tanks(self):
        try:
            r = requests.get(f"{API_BASE}/machine/status", timeout=5)
            if r.ok:
                data = r.json()
                self.tanks = data.get("tanks", [])
            else:
                self.show_message("No se pudo obtener depósitos", 3)
                self.tanks = []
        except Exception as exc:
            self.show_message(f"Error tanks: {exc}", 3)
            self.tanks = []

    def save_tanks(self):
        payload = []
        for t in self.tanks:
            payload.append({"id": t.get("id"), "name": t.get("name") or "", "liquid_type": t.get("liquid_type") or "", "current_ml": int(t.get("current_level", 0))})
        try:
            r = requests.post(f"{API_BASE}/machine/tanks/update", json=payload, timeout=5)
            if r.ok:
                self.show_message("Depósitos guardados", 3)
            else:
                self.show_message(f"Error: {r.status_code}", 3)
        except Exception as exc:
            self.show_message(f"Error: {exc}", 3)

    def draw_main(self):
        self.screen.fill((20, 20, 20))
        self.btn_prepare.draw(self.screen, self.font)
        self.btn_tanks.draw(self.screen, self.font)
        self.btn_stop.draw(self.screen, self.font)

    def draw_menu(self):
        # Menu header + main buttons
        self.screen.fill((18, 18, 18))
        try:
            title = self.font.render("Menu", True, (255, 255, 255))
            self.screen.blit(title, (16, 12))
        except Exception:
            pass
        self.btn_prepare.draw(self.screen, self.font)
        self.btn_tanks.draw(self.screen, self.font)
        self.btn_stop.draw(self.screen, self.font)

    def draw_home(self):
        self.screen.fill((12, 12, 12))
        try:
            title = self.font.render("Cubatron", True, (255, 255, 255))
            self.screen.blit(title, title.get_rect(center=(240, 60)))
        except Exception:
            pass
        # start button
        try:
            self.btn_start.draw(self.screen, self.font)
        except Exception:
            pass

    # --- Touch login screens ---
    def load_touch_users(self):
        # First try the API; if it fails, fall back to reading the local SQLite DB
        try:
            r = self.session.get(f"{API_BASE}/users/touch/list", timeout=5)
            if r.ok:
                self.touch_users = r.json() or []
                return
        except Exception:
            pass

        # fallback: read DB directly
        try:
            self.touch_users = self._load_users_from_db()
        except Exception:
            self.touch_users = []

    def _load_users_from_db(self):
        out = []
        try:
            # import config lazily to avoid side-effects
            from app.config import DATA_DIR
            import sqlite3
            db_path = str(DATA_DIR / "cubatron.db")
            if not os.path.exists(db_path):
                return out
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cols = [r[1] for r in cur.execute("PRAGMA table_info(user);").fetchall()]
            select_cols = ["id", "username", "full_name"]
            if "pin_hash" in cols:
                select_cols.append("pin_hash")
            query = f"SELECT {','.join(select_cols)} FROM user WHERE is_archived = 0"
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()
            for row in rows:
                d = {select_cols[i]: row[i] for i in range(len(select_cols))}
                out.append({
                    "id": d.get("id"),
                    "username": d.get("username"),
                    "full_name": d.get("full_name") or d.get("username"),
                    "has_pin": bool(d.get("pin_hash")) if "pin_hash" in d else False,
                    "pin_hash": d.get("pin_hash") if "pin_hash" in d else None,
                })
        except Exception:
            return []
        return out

    def _get_user_from_db(self, user_id: int):
        try:
            from app.config import DATA_DIR
            import sqlite3
            db_path = str(DATA_DIR / "cubatron.db")
            if not os.path.exists(db_path):
                return None
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cols = [r[1] for r in cur.execute("PRAGMA table_info(user);").fetchall()]
            select_cols = ["id", "username", "full_name", "role"]
            if "pin_hash" in cols:
                select_cols.append("pin_hash")
            query = f"SELECT {','.join(select_cols)} FROM user WHERE id = ?"
            cur.execute(query, (user_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return {select_cols[i]: row[i] for i in range(len(select_cols))}
        except Exception:
            return None

    def draw_user_select(self):
        self.screen.fill((12, 12, 12))
        title = self.font.render("Selecciona usuario", True, (255, 255, 255))
        self.screen.blit(title, (16, 12))

        w, h = self.screen.get_size()
        pad = 8
        bw = w - 2 * pad
        bh = 48
        y = 56
        for i, u in enumerate(self.touch_users[:6]):
            rect = pygame.Rect(pad, y, bw, bh)
            pygame.draw.rect(self.screen, (70, 70, 70), rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            txt = f"{u.get('full_name') or u.get('username')}"
            surf = self.small_font.render(txt, True, (230, 230, 230))
            self.screen.blit(surf, (pad + 8, y + 12))
            y += bh + pad

    def draw_pin_entry(self):
        self.screen.fill((6, 6, 6))
        back = Button((10, 10, 80, 36), "Atrás", color=(200, 200, 200), callback=lambda: self.set_scene_and_reload("user_select"))
        back.draw(self.screen, self.small_font)
        if not self.selected_user:
            return
        title = self.font.render(self.selected_user.get("full_name") or self.selected_user.get("username"), True, (255, 255, 255))
        self.screen.blit(title, (20, 56))

        # PIN placeholders
        pin_display = "".join(["•" if i < len(self.pin_buffer) else "_" for i in range(6)])
        self.screen.blit(self.font.render(pin_display, True, (255, 255, 255)), (120, 110))

        # keypad layout 3x4
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "←", "0", "OK"]
        w, h = self.screen.get_size()
        pad = 8
        kw = (w - 4 * pad) // 3
        kh = 56
        start_y = 150
        for idx, k in enumerate(keys):
            row = idx // 3
            col = idx % 3
            x = pad + col * (kw + pad)
            y = start_y + row * (kh + pad)
            rect = pygame.Rect(x, y, kw, kh)
            pygame.draw.rect(self.screen, (120, 120, 120), rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            surf = self.font.render(k, True, (0, 0, 0))
            self.screen.blit(surf, surf.get_rect(center=rect.center))

    def attempt_pin_login(self):
        if not self.selected_user:
            return
        if len(self.pin_buffer) != 6:
            self.show_message("Introduce 6 dígitos", 2)
            self.pin_buffer = ""
            return
        payload = {"user_id": int(self.selected_user.get("id")), "pin": self.pin_buffer}
        try:
            r = requests.post(f"{API_BASE}/users/touch/pin-login", json=payload, timeout=5)
            if r.ok:
                data = r.json()
                token = data.get("access_token")
                if token:
                    self.token = token
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.current_user = {"id": data.get("user_id"), "username": data.get("username"), "full_name": data.get("full_name")}
                    self.pin_buffer = ""
                    self.show_message("Login correcto", 2)
                    self.scene = "menu"
                    return
            # failure
            self.show_message("PIN inválido", 2)
        except Exception as exc:
            # API login failed; try verifying against local DB (fallback)
            try:
                from app.security import verify_password, create_access_token
                uid = int(self.selected_user.get("id"))
                dbu = self._get_user_from_db(uid)
                if dbu and dbu.get("pin_hash") and verify_password(self.pin_buffer, dbu.get("pin_hash")):
                    token = create_access_token({"sub": dbu.get("username"), "role": dbu.get("role") or "user", "user_id": dbu.get("id")}, expires_minutes=60)
                    self.token = token
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.current_user = {"id": dbu.get("id"), "username": dbu.get("username"), "full_name": dbu.get("full_name")}
                    self.pin_buffer = ""
                    self.show_message("Login correcto (local)", 2)
                    self.scene = "menu"
                    return
            except Exception:
                pass
            self.show_message(f"Error login: {exc}", 3)
        self.pin_buffer = ""

    def draw_prepare(self):
        self.screen.fill((10, 10, 10))
        w, h = self.screen.get_size()
        back = Button((10, 10, 80, 36), "Atrás", color=(200, 200, 200), callback=self.goto_main)
        back.draw(self.screen, self.small_font)
        title = self.font.render("Preparar bebida", True, (255, 255, 255))
        self.screen.blit(title, (120, 12))

        if not self.token:
            msg = self.small_font.render("Token no encontrado. Accede con PIN", True, (200, 200, 200))
            self.screen.blit(msg, (20, 60))
            return

        cols = 2
        pad = 8
        bw = (w - pad * (cols + 1)) // cols
        bh = 80
        for i, r in enumerate(self.recipes[:6]):
            row = i // cols
            col = i % cols
            x = pad + col * (bw + pad)
            y = 60 + row * (bh + pad)
            btn = Button((x, y, bw, bh), r.get("name", "?"), color=(100, 140, 220), callback=lambda rr=r: self.preview_recipe(rr))
            btn.draw(self.screen, self.small_font)

    def preview_recipe(self, recipe):
        # Default preview: medium + first glass option
        glass_options = recipe.get("glass_options") or []
        glass = glass_options[0] if glass_options else recipe.get("glass_type", "highball")
        payload = {"recipe_id": int(recipe.get("id")), "serving_mode": "medium", "glass_type": glass}
        try:
            r = self.session.post(f"{API_BASE}/drinks/preview", json=payload, timeout=5)
            if r.ok:
                info = r.json()
                self.scene = "preview"
                self.preview_info = {"recipe": recipe, "payload": payload, "preview": info}
            else:
                self.show_message(f"Preview error: {r.status_code}", 3)
        except Exception as exc:
            self.show_message(f"Error preview: {exc}", 3)

    def draw_preview(self):
        self.screen.fill((8, 8, 8))
        back = Button((10, 10, 80, 36), "Atrás", color=(200, 200, 200), callback=lambda: self.set_scene_and_reload("prepare"))
        back.draw(self.screen, self.small_font)
        recipe = self.preview_info.get("recipe")
        pv = self.preview_info.get("preview")
        title = self.font.render(recipe.get("name", ""), True, (255, 255, 255))
        self.screen.blit(title, (20, 56))
        y = 100
        for item in pv.get("liquid_breakdown", []):
            txt = f"{item.get('ml')}ml - {item.get('liquid')}"
            self.screen.blit(self.small_font.render(txt, True, (220, 220, 220)), (24, y))
            y += 22
        start_btn = Button((300, 240, 160, 60), "Iniciar", color=(40, 180, 40), callback=self.start_make)
        start_btn.draw(self.screen, self.font)

    def start_make(self):
        payload = self.preview_info.get("payload")
        try:
            r = self.session.post(f"{API_BASE}/drinks/make", json=payload, timeout=10)
            if r.ok:
                self.show_message("Bebida en preparación", 4)
                self.set_scene_and_reload("main")
            else:
                self.show_message(f"Error make: {r.status_code}", 4)
        except Exception as exc:
            self.show_message(f"Error make: {exc}", 4)

    def draw_tanks(self):
        self.screen.fill((6, 6, 6))
        back = Button((10, 10, 80, 36), "Atrás", color=(200, 200, 200), callback=lambda: self.set_scene_and_reload("main"))
        back.draw(self.screen, self.small_font)
        title = self.font.render("Depósitos", True, (255, 255, 255))
        self.screen.blit(title, (120, 12))
        y = 60
        for idx, t in enumerate(self.tanks):
            name = t.get("name") or f"Tank {idx}"
            level = int(t.get("current_level", 0))
            pygame.draw.rect(self.screen, (40, 40, 40), (20, y, 440, 48))
            self.screen.blit(self.small_font.render(f"{name}", True, (230, 230, 230)), (30, y + 8))
            self.screen.blit(self.small_font.render(f"{level}%", True, (230, 230, 230)), (380, y + 8))
            # draw plus/minus
            minus = Button((380, y + 20, 24, 24), "-", color=(160, 160, 160), callback=lambda i=idx: self.adjust_tank(i, -10))
            plus = Button((410, y + 20, 24, 24), "+", color=(160, 160, 160), callback=lambda i=idx: self.adjust_tank(i, 10))
            minus.draw(self.screen, self.small_font)
            plus.draw(self.screen, self.small_font)
            y += 60
        save = Button((300, 260, 160, 48), "Guardar", color=(60, 160, 60), callback=self.save_tanks)
        save.draw(self.screen, self.font)

    def adjust_tank(self, idx, delta):
        try:
            cur = int(self.tanks[idx].get("current_level", 0))
            cur = max(0, min(100, cur + delta))
            self.tanks[idx]["current_level"] = cur
        except Exception:
            pass

    def set_scene_and_reload(self, scene):
        self.scene = scene
        if scene == "menu":
            self._setup_main_buttons()
        elif scene == "prepare":
            self.load_recipes()
        elif scene == "tanks":
            self.load_tanks()
        elif scene == "user_select":
            self.selected_user = None
            self.pin_buffer = ""
            self.load_touch_users()

    def goto_main(self):
        self.scene = "menu"

    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            self.running = False
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.last_interaction = time.time()
            pos = ev.pos
            if self.scene == "main" or self.scene == "menu":
                if self.btn_prepare.contains(pos):
                    self.btn_prepare.callback()
                elif self.btn_tanks.contains(pos):
                    self.btn_tanks.callback()
                elif self.btn_stop.contains(pos):
                    self.btn_stop.callback()
            elif self.scene == "user_select":
                # user list taps
                w, h = self.screen.get_size()
                pad = 8
                bw = w - 2 * pad
                bh = 48
                y = 56
                for i, u in enumerate(self.touch_users[:6]):
                    rect = pygame.Rect(pad, y, bw, bh)
                    if rect.collidepoint(pos):
                        self.selected_user = u
                        self.scene = "pin_entry"
                        self.pin_buffer = ""
                        self.selection_time = time.time()
                        break
                    y += bh + pad
            elif self.scene == "pin_entry":
                # back button
                if 10 <= pos[0] <= 90 and 10 <= pos[1] <= 46:
                    self.set_scene_and_reload("user_select")
                    return
                w, h = self.screen.get_size()
                pad = 8
                kw = (w - 4 * pad) // 3
                kh = 56
                start_y = 150
                # keypad
                for idx in range(12):
                    row = idx // 3
                    col = idx % 3
                    x = pad + col * (kw + pad)
                    y = start_y + row * (kh + pad)
                    rect = pygame.Rect(x, y, kw, kh)
                    if rect.collidepoint(pos):
                        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "←", "0", "OK"]
                        key = keys[idx]
                        if key.isdigit():
                            if len(self.pin_buffer) < 6:
                                self.pin_buffer += key
                        elif key == "←":
                            self.pin_buffer = self.pin_buffer[:-1]
                        elif key == "OK":
                            self.attempt_pin_login()
                        break
            elif self.scene == "prepare":
                w, h = self.screen.get_size()
                if 10 <= pos[0] <= 90 and 10 <= pos[1] <= 46:
                    self.goto_main()
                else:
                    # recipe buttons
                    cols = 2
                    pad = 8
                    bw = (w - pad * (cols + 1)) // cols
                    bh = 80
                    for i, r in enumerate(self.recipes[:6]):
                        row = i // cols
                        col = i % cols
                        x = pad + col * (bw + pad)
                        y = 60 + row * (bh + pad)
                        rect = pygame.Rect(x, y, bw, bh)
                        if rect.collidepoint(pos):
                            self.preview_recipe(r)
            elif self.scene == "preview":
                # start button area
                if 300 <= pos[0] <= 460 and 240 <= pos[1] <= 300:
                    self.start_make()
                if 10 <= pos[0] <= 90 and 10 <= pos[1] <= 46:
                    self.set_scene_and_reload("prepare")
            elif self.scene == "tanks":
                # back
                if 10 <= pos[0] <= 90 and 10 <= pos[1] <= 46:
                    self.set_scene_and_reload("main")
                # plus/minus and save
                y = 60
                for idx, t in enumerate(self.tanks):
                    if 380 <= pos[0] <= 404 and y + 20 <= pos[1] <= y + 44:
                        self.adjust_tank(idx, -10)
                    if 410 <= pos[0] <= 434 and y + 20 <= pos[1] <= y + 44:
                        self.adjust_tank(idx, 10)
                    y += 60
                if 300 <= pos[0] <= 460 and 260 <= pos[1] <= 308:
                    self.save_tanks()

    def run(self):
        while self.running:
            for ev in pygame.event.get():
                self.handle_event(ev)

            # Auto-logout on inactivity (40s) for logged-in users
            if self.current_user and (time.time() - self.last_interaction) > 40:
                # clear session
                self.current_user = None
                self.token = None
                if "Authorization" in self.session.headers:
                    self.session.headers.pop("Authorization")
                self.show_message("Sesión cerrada por inactividad", 2)
                self.set_scene_and_reload("user_select")

            # If user selected a PIN entry and they didn't interact for 40s, go back
            if self.scene == "pin_entry" and self.selection_time and (time.time() - self.selection_time) > 40:
                self.selected_user = None
                self.pin_buffer = ""
                self.set_scene_and_reload("user_select")

            if self.scene == "main":
                self.draw_main()
            elif self.scene == "menu":
                self.draw_menu()
            elif self.scene == "user_select":
                self.draw_user_select()
            elif self.scene == "pin_entry":
                self.draw_pin_entry()
            elif self.scene == "prepare":
                self.draw_prepare()
            elif self.scene == "preview":
                self.draw_preview()
            elif self.scene == "tanks":
                self.draw_tanks()

            # message overlay
            if self.message and time.time() < self.message_ttl:
                s = self.small_font.render(self.message, True, (255, 255, 255))
                self.screen.blit(s, (10, 280))

            pygame.display.flip()
            # if we are rendering offscreen, flush to fb device if available
            if not self.using_hw_display and getattr(self, "fb_fd", None):
                try:
                    self._fb_write(self.screen)
                except Exception:
                    pass
            self.clock.tick(20)

    # --- framebuffer helpers ---
    def _init_framebuffer(self):
        # read fb properties and open device for raw writes
        path = self.fb_path
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        # read virtual size
        vs = open(f"/sys/class/graphics/{os.path.basename(path)}/virtual_size", "r").read().strip() if os.path.exists(f"/sys/class/graphics/{os.path.basename(path)}/virtual_size") else None
        if vs:
            w, h = [int(x) for x in vs.split(",")]
        else:
            # fallback to proc info
            w, h = 480, 320
        bpp = int(open(f"/sys/class/graphics/{os.path.basename(path)}/bits_per_pixel").read().strip()) if os.path.exists(f"/sys/class/graphics/{os.path.basename(path)}/bits_per_pixel") else 16
        line_len = int(open(f"/sys/class/graphics/{os.path.basename(path)}/line_length").read().strip()) if os.path.exists(f"/sys/class/graphics/{os.path.basename(path)}/line_length") else (w * (bpp // 8))
        self.fb_info = {"width": w, "height": h, "bpp": bpp, "line_length": line_len}
        # open device
        try:
            self.fb_fd = open(path, "r+b", buffering=0)
            try:
                print(f"[touch_gui] opened framebuffer {path}: {self.fb_info}")
            except Exception:
                pass
        except Exception:
            self.fb_fd = None

    def _fb_write(self, surface: "pygame.Surface"):
        # convert surface (RGB) to framebuffer format (supporting RGB565 primary)
        if not self.fb_fd or not self.fb_info:
            return
        fb_w = self.fb_info.get("width")
        fb_h = self.fb_info.get("height")
        bpp = self.fb_info.get("bpp")
        line_len = self.fb_info.get("line_length", fb_w * (bpp // 8))
        surf_w, surf_h = surface.get_size()
        # get raw RGB bytes from surface (row-major)
        raw = pygame.image.tostring(surface, "RGB")

        # write row by row respecting line_length (stride)
        try:
            if bpp == 16:
                # convert RGB888 -> RGB565 per-row
                src_row_stride = surf_w * 3
                for row in range(min(fb_h, surf_h)):
                    rs = row * src_row_stride
                    re = rs + src_row_stride
                    row_raw = raw[rs:re]
                    out_row = bytearray(surf_w * 2)
                    j = 0
                    for i in range(0, len(row_raw), 3):
                        r = row_raw[i]
                        g = row_raw[i+1]
                        b = row_raw[i+2]
                        val = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
                        out_row[j] = val & 0xFF
                        out_row[j+1] = (val >> 8) & 0xFF
                        j += 2
                    # pad to line length if needed
                    if line_len > len(out_row):
                        out_row.extend(b"\x00" * (line_len - len(out_row)))
                    self.fb_fd.seek(row * line_len)
                    self.fb_fd.write(out_row)
            else:
                # 24/32bpp simple per-row write with padding
                src_row_stride = surf_w * 3
                for row in range(min(fb_h, surf_h)):
                    rs = row * src_row_stride
                    re = rs + src_row_stride
                    row_raw = raw[rs:re]
                    if line_len > len(row_raw):
                        row_raw = row_raw + (b"\x00" * (line_len - len(row_raw)))
                    self.fb_fd.seek(row * line_len)
                    self.fb_fd.write(row_raw)
        except Exception:
            # do not crash on fb write errors
            return


def main():
    app = TouchGUI()
    try:
        app.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
