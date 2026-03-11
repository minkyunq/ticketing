import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import pyautogui
import keyboard
import pygetwindow as gw
from PIL import Image, ImageTk
import numpy as np

# ─── 설정 파일 경로 ───────────────────────────────────────────────
CONFIG_FILE = "config.json"

# ─── 색상 BGR → RGB 매핑 (이미지 폴더 참조용) ────────────────────
COLOR_OPTIONS = ["보라색", "파란색", "초록색", "빨간색", "노란색", "주황색", "흰색"]
COLOR_MAP = {
    "보라색": (128, 0, 128),
    "파란색": (0, 0, 255),
    "초록색": (0, 128, 0),
    "빨간색": (255, 0, 0),
    "노란색": (255, 255, 0),
    "주황색": (255, 165, 0),
    "흰색":   (255, 255, 255),
}
COLOR_BADGE = {
    "보라색": "#800080",
    "파란색": "#0000FF",
    "초록색": "#008000",
    "빨간색": "#FF0000",
    "노란색": "#FFD700",
    "주황색": "#FFA500",
    "흰색":   "#DDDDDD",
}

TOLERANCE = 30  # 색상 허용 오차


def load_config():
    default = {
        "f8_x": "318", "f8_y": "270",
        "f9_x": "398", "f9_y": "543",
        "f10_x": "780", "f10_y": "636",
        "color1": "보라색", "color2": "보라색", "color3": "초록색",
        "count": "1명"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**default, **json.load(f)}
        except Exception:
            pass
    return default


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ─── 색상 찾기 함수 ───────────────────────────────────────────────
def find_color_in_region(x1, y1, x2, y2, target_rgb, tol=TOLERANCE):
    """지정 영역에서 색상 좌표를 찾아 반환"""
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    img = np.array(screenshot)
    tr, tg, tb = target_rgb
    mask = (
        (np.abs(img[:, :, 0].astype(int) - tr) < tol) &
        (np.abs(img[:, :, 1].astype(int) - tg) < tol) &
        (np.abs(img[:, :, 2].astype(int) - tb) < tol)
    )
    coords = np.argwhere(mask)
    if len(coords) == 0:
        return None
    y, x = coords[0]
    return (x1 + x, y1 + y)


# ─── 매크로 로직 ──────────────────────────────────────────────────
class MacroEngine:
    def __init__(self, app):
        self.app = app
        self.running = False

    def get_coords(self):
        cfg = self.app.get_config()
        x1 = int(cfg["f8_x"]); y1 = int(cfg["f8_y"])
        x2 = int(cfg["f9_x"]); y2 = int(cfg["f9_y"])
        fx = int(cfg["f10_x"]); fy = int(cfg["f10_y"])
        return x1, y1, x2, y2, fx, fy

    def run_ticketing(self):
        self.running = True
        cfg = self.app.get_config()
        x1, y1, x2, y2, fx, fy = self.get_coords()
        count_str = cfg["count"]
        count = int(count_str.replace("명", ""))
        colors = [cfg["color1"], cfg["color2"], cfg["color3"]]
        priority = [COLOR_MAP[c] for c in colors]

        self.app.log("🎯 티켓팅 실행 시작!")
        found = 0
        while self.running and found < count:
            for idx, color_rgb in enumerate(priority):
                if not self.running:
                    break
                pos = find_color_in_region(x1, y1, x2, y2, color_rgb)
                if pos:
                    self.app.log(f"  ✅ {colors[idx]} 좌석 발견: {pos}")
                    pyautogui.click(pos[0], pos[1])
                    time.sleep(0.3)
                    found += 1
                    if found >= count:
                        break
            time.sleep(0.1)

        if found >= count:
            self.app.log(f"🖱️ 선택완료 클릭: ({fx}, {fy})")
            pyautogui.click(fx, fy)
            self.app.log("🎉 티켓팅 완료!")
        else:
            self.app.log("⚠️ 매크로 중지됨.")
        self.running = False
        self.app.update_status(False)

    def stop(self):
        self.running = False


# ─── GUI ─────────────────────────────────────────────────────────
class TicketingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("티켓팅")
        self.root.resizable(False, False)
        self.root.configure(bg="#F0F0F0")
        self.config = load_config()
        self.engine = MacroEngine(self)
        self.macro_thread = None
        self._build_ui()
        self._register_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 구성 ───────────────────────────────────────────────────
    def _build_ui(self):
        cfg = self.config

        # ── 탭 ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#F0F0F0", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[10, 4], font=("맑은 고딕", 9))

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=5, pady=5)

        main_frame = tk.Frame(nb, bg="#F0F0F0")
        nb.add(main_frame, text="티켓팅")

        # ── [좌표1] 그룹 ──
        coord_frame = tk.LabelFrame(main_frame, text="  [좌표1]  ", fg="red",
                                    font=("맑은 고딕", 9, "bold"),
                                    bg="#F0F0F0", bd=1, relief="groove")
        coord_frame.pack(fill="x", padx=10, pady=8)

        def coord_row(parent, label, xvar, yvar, row):
            tk.Label(parent, text=label, bg="#F0F0F0",
                     font=("맑은 고딕", 9)).grid(row=row, column=0, columnspan=2,
                                                sticky="w", padx=10, pady=(6, 0))
            ex = tk.Entry(parent, textvariable=xvar, width=10,
                          font=("맑은 고딕", 9), relief="sunken")
            ex.grid(row=row+1, column=0, padx=(10, 2), pady=2)
            ey = tk.Entry(parent, textvariable=yvar, width=10,
                          font=("맑은 고딕", 9), relief="sunken")
            ey.grid(row=row+1, column=1, padx=(2, 10), pady=2)

        self.f8x = tk.StringVar(value=cfg["f8_x"])
        self.f8y = tk.StringVar(value=cfg["f8_y"])
        self.f9x = tk.StringVar(value=cfg["f9_x"])
        self.f9y = tk.StringVar(value=cfg["f9_y"])
        self.f10x = tk.StringVar(value=cfg["f10_x"])
        self.f10y = tk.StringVar(value=cfg["f10_y"])

        coord_row(coord_frame, "범위 좌표↖ (F8)", self.f8x, self.f8y, 0)
        coord_row(coord_frame, "범위 좌표↘ (F9)", self.f9x, self.f9y, 2)
        coord_row(coord_frame, "선택완료 좌표 (F10)", self.f10x, self.f10y, 4)

        # ── [좌석] 그룹 ──
        seat_frame = tk.LabelFrame(main_frame, text="  [좌석]  ", fg="red",
                                   font=("맑은 고딕", 9, "bold"),
                                   bg="#F0F0F0", bd=1, relief="groove")
        seat_frame.pack(fill="x", padx=10, pady=4)

        tk.Label(seat_frame, text="좌석색", bg="#F0F0F0",
                 font=("맑은 고딕", 9)).grid(row=0, column=0, columnspan=3,
                                             sticky="w", padx=10, pady=(6, 2))

        self.color1 = tk.StringVar(value=cfg["color1"])
        self.color2 = tk.StringVar(value=cfg["color2"])
        self.color3 = tk.StringVar(value=cfg["color3"])

        for i, (cvar, order) in enumerate(
                [(self.color1, "1순위"), (self.color2, "2순위"), (self.color3, "3순위")]):
            self._color_row(seat_frame, cvar, order, row=i+1)

        # 인원수
        tk.Label(seat_frame, text="인원수", bg="#F0F0F0",
                 font=("맑은 고딕", 9)).grid(row=4, column=0, columnspan=3,
                                             sticky="w", padx=10, pady=(8, 2))
        self.count_var = tk.StringVar(value=cfg["count"])
        count_cb = ttk.Combobox(seat_frame, textvariable=self.count_var,
                                values=["1명", "2명", "3명", "4명"],
                                width=12, state="readonly",
                                font=("맑은 고딕", 9))
        count_cb.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # ── 버튼 영역 ──
        btn_frame = tk.Frame(main_frame, bg="#F0F0F0")
        btn_frame.pack(fill="x", padx=10, pady=6)

        btn_style = {"font": ("맑은 고딕", 9, "bold"), "relief": "raised",
                     "bd": 2, "cursor": "hand2", "width": 12}

        self.btn_date = tk.Button(btn_frame, text="날짜/회차 선택 (F1)",
                                  bg="#4A90D9", fg="white",
                                  command=self._f1_action, **btn_style)
        self.btn_date.pack(side="left", padx=(0, 4))

        self.btn_start = tk.Button(btn_frame, text="티켓팅 실행 (F2)",
                                   bg="#27AE60", fg="white",
                                   command=self._f2_action, **btn_style)
        self.btn_start.pack(side="left", padx=4)

        self.btn_stop = tk.Button(btn_frame, text="■ 중지",
                                  bg="#E74C3C", fg="white",
                                  command=self._stop, state="disabled", **btn_style)
        self.btn_stop.pack(side="left", padx=4)

        # ── 로그 ──
        log_frame = tk.LabelFrame(main_frame, text="  로그  ",
                                  font=("맑은 고딕", 9), bg="#F0F0F0",
                                  bd=1, relief="groove")
        log_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.log_text = tk.Text(log_frame, height=6, state="disabled",
                                bg="#1E1E1E", fg="#00FF00",
                                font=("Consolas", 8), bd=0,
                                insertbackground="white")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # ── 상태바 ──
        self.status_var = tk.StringVar(value="대기 중 | F1: 날짜선택  F2: 실행  F8/F9/F10: 좌표등록")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              font=("맑은 고딕", 8), bg="#DDDDDD",
                              anchor="w", relief="sunken", bd=1)
        status_bar.pack(fill="x", side="bottom")

    def _color_row(self, parent, cvar, order_label, row):
        cb = ttk.Combobox(parent, textvariable=cvar, values=COLOR_OPTIONS,
                          width=10, state="readonly", font=("맑은 고딕", 9))
        cb.grid(row=row, column=0, padx=(10, 4), pady=2, sticky="w")

        badge_lbl = tk.Label(parent, text=f"({order_label}:■)",
                             bg="#F0F0F0", font=("맑은 고딕", 9))
        badge_lbl.grid(row=row, column=1, padx=2)

        def update_badge(*_):
            col = cvar.get()
            badge_lbl.config(fg=COLOR_BADGE.get(col, "#000"))
        cvar.trace_add("write", update_badge)
        update_badge()

    # ── 단축키 등록 ───────────────────────────────────────────────
    def _register_hotkeys(self):
        keyboard.add_hotkey("f1", self._f1_action)
        keyboard.add_hotkey("f2", self._f2_action)
        keyboard.add_hotkey("f8", self._capture_f8)
        keyboard.add_hotkey("f9", self._capture_f9)
        keyboard.add_hotkey("f10", self._capture_f10)

    def _capture_f8(self):
        pos = pyautogui.position()
        self.f8x.set(str(pos.x)); self.f8y.set(str(pos.y))
        self.log(f"📌 F8 좌표 등록: ({pos.x}, {pos.y})")

    def _capture_f9(self):
        pos = pyautogui.position()
        self.f9x.set(str(pos.x)); self.f9y.set(str(pos.y))
        self.log(f"📌 F9 좌표 등록: ({pos.x}, {pos.y})")

    def _capture_f10(self):
        pos = pyautogui.position()
        self.f10x.set(str(pos.x)); self.f10y.set(str(pos.y))
        self.log(f"📌 F10 좌표 등록: ({pos.x}, {pos.y})")

    # ── 액션 ──────────────────────────────────────────────────────
    def _f1_action(self):
        self.log("📅 F1: 날짜/회차 선택 모드 — 직접 클릭하여 선택하세요.")
        messagebox.showinfo("날짜/회차 선택",
                            "날짜/회차를 직접 선택해 주세요.\n"
                            "선택 후 F2를 눌러 티켓팅을 시작하세요.")

    def _f2_action(self):
        if self.engine.running:
            return
        self._save_config()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_var.set("🔴 매크로 실행 중...")
        self.macro_thread = threading.Thread(target=self.engine.run_ticketing, daemon=True)
        self.macro_thread.start()

    def _stop(self):
        self.engine.stop()
        self.log("⛔ 사용자에 의해 중지됨.")
        self.update_status(False)

    def update_status(self, running: bool):
        if running:
            self.status_var.set("🔴 매크로 실행 중...")
        else:
            self.status_var.set("대기 중 | F1: 날짜선택  F2: 실행  F8/F9/F10: 좌표등록")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    # ── 설정 ──────────────────────────────────────────────────────
    def get_config(self):
        return {
            "f8_x": self.f8x.get(), "f8_y": self.f8y.get(),
            "f9_x": self.f9x.get(), "f9_y": self.f9y.get(),
            "f10_x": self.f10x.get(), "f10_y": self.f10y.get(),
            "color1": self.color1.get(), "color2": self.color2.get(),
            "color3": self.color3.get(),
            "count": self.count_var.get(),
        }

    def _save_config(self):
        save_config(self.get_config())

    # ── 로그 ──────────────────────────────────────────────────────
    def log(self, msg):
        def _append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _append)

    def _on_close(self):
        self._save_config()
        keyboard.unhook_all()
        self.root.destroy()


# ─── 진입점 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = TicketingApp(root)
    root.mainloop()
