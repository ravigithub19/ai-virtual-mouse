"""
AI Virtual Mouse Studio - SENAI (Edição Moderna & Alcance de Tela Inteira)
Construído com CustomTkinter para uma experiência visual contemporânea, limpa e responsiva.
Permite controle fluido e sem restrições por toda a tela do computador (1920x1080).
"""

import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np
import time
import math
import random
from typing import Dict, Any, Optional

from virtual_mouse_engine import VirtualMouseEngine
from camera_utils import get_camera_devices, get_default_camera_index


# Set global CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernSenaiMouseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window settings
        self.title("SENAI — Mouse Virtual por Visão Computacional")
        self.geometry("1240x780")
        self.minsize(1080, 680)

        # SENAI Modern Palette
        self.c_senai_red = "#e30613"
        self.c_senai_red_hover = "#ff2231"
        self.c_bg = "#090d16"
        self.c_card = "#121724"
        self.c_card_border = "#20283c"
        self.c_card_hover = "#192133"
        self.c_text_white = "#ffffff"
        self.c_text_muted = "#94a3b8"
        self.c_success = "#10b981"
        self.c_cyan = "#06b6d4"

        self.configure(fg_color=self.c_bg)

        # Camera Discovery & Default Selection (Prioritizes external USB webcam)
        self.camera_list = get_camera_devices()
        self.camera_map = {cam["label"]: cam["index"] for cam in self.camera_list}
        self.selected_camera_index = get_default_camera_index()

        # Engine Setup (Control System Mouse TRUE by default for Full Screen coverage)
        self.engine = VirtualMouseEngine()
        self.engine.control_system_mouse = True
        self.engine.margin_x = 85
        self.engine.margin_y = 65
        self.engine.on_frame_ready = self._on_frame_ready
        self.engine.on_telemetry_ready = self._on_telemetry_ready
        self.engine.on_action_event = self._on_engine_action

        # State Variables
        self.is_camera_active = False
        self.last_frame: Optional[np.ndarray] = None
        self.current_telemetry: Dict[str, Any] = {}
        self.photo_image = None
        self.is_mini_mode = False

        # Full-Screen Range Coverage Test State (4 Corners + Center)
        self.coverage_nodes = {
            "top_left": {"name": "Sup. Esquerdo", "pos": (40, 40), "hit": False},
            "top_right": {"name": "Sup. Direito", "pos": (740, 40), "hit": False},
            "bottom_left": {"name": "Inf. Esquerdo", "pos": (40, 360), "hit": False},
            "bottom_right": {"name": "Inf. Direito", "pos": (740, 360), "hit": False},
            "center": {"name": "Centro da Tela", "pos": (390, 200), "hit": False},
        }
        self.random_target_pos = (390, 160)
        self.random_target_hits = 0

        # Drag and Drop Lab State
        self.drag_items = [
            {"id": "p1", "name": "Módulo Robótico", "color": self.c_senai_red, "x": 50, "y": 70, "w": 160, "h": 50, "zone": "origem"},
            {"id": "p2", "name": "Sensor Óptico", "color": "#0284c7", "x": 50, "y": 140, "w": 160, "h": 50, "zone": "origem"},
        ]
        self.dragged_item_idx: Optional[int] = None
        self.drag_offset = (0, 0)

        # Drawing state
        self.draw_color = self.c_senai_red
        self.draw_brush_size = 4
        self.last_draw_pt = None

        # Build UI
        self._build_top_dock()
        self._build_main_layout()

        # Shutdown and auto-start
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._update_loop()
        self.after(300, self._toggle_camera)

    # -------------------------------------------------------------
    # TOP DOCK / HEADER
    # -------------------------------------------------------------
    def _build_top_dock(self):
        """Clean, modern floating dock at the top of the interface."""
        self.header_card = ctk.CTkFrame(
            self, fg_color=self.c_card, corner_radius=16,
            border_width=1, border_color=self.c_card_border, height=72
        )
        self.header_card.pack(fill=tk.X, padx=18, pady=(14, 10))
        self.header_card.pack_propagate(False)

        # Left Section: SENAI Brand & Title
        left_box = ctk.CTkFrame(self.header_card, fg_color="transparent")
        left_box.pack(side=tk.LEFT, padx=16, pady=10)

        # Logo SENAI (Official image loaded with CTkImage)
        logo_path = os.path.join(os.path.dirname(__file__), "senai_logo.png")
        if os.path.exists(logo_path):
            try:
                raw_logo = Image.open(logo_path)
                w, h = raw_logo.size
                nh = 38
                nw = int(w * (nh / h))
                ctk_logo = ctk.CTkImage(light_image=raw_logo, dark_image=raw_logo, size=(nw, nh))
                logo_lbl = ctk.CTkLabel(left_box, image=ctk_logo, text="")
                logo_lbl.pack(side=tk.LEFT, padx=(0, 14))
            except Exception:
                pass

        # Vertical Divider
        ctk.CTkFrame(left_box, width=2, height=36, fg_color=self.c_card_border).pack(side=tk.LEFT, padx=(0, 14))

        # Title & Subtitle
        text_col = ctk.CTkFrame(left_box, fg_color="transparent")
        text_col.pack(side=tk.LEFT)

        ctk.CTkLabel(
            text_col, text="MOUSE VIRTUAL IA",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.c_text_white
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_col, text="CONTROLE TOTAL POR VISÃO COMPUTACIONAL • TELA INTEIRA",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.c_senai_red
        ).pack(anchor="w")

        # Right Section: Controls & Status
        right_box = ctk.CTkFrame(self.header_card, fg_color="transparent")
        right_box.pack(side=tk.RIGHT, padx=16, pady=10)

        # Real Mouse Full Screen Switch (Active by default!)
        self.full_screen_switch = ctk.CTkSwitch(
            right_box, text="Controlar Mouse do Windows (Tela Inteira)",
            command=self._on_switch_full_screen,
            progress_color=self.c_senai_red,
            button_color=self.c_text_white,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_text_white
        )
        self.full_screen_switch.select()
        self.full_screen_switch.pack(side=tk.LEFT, padx=(0, 20))

        # Mini-Widget Floating Mode Toggle
        self.btn_mini = ctk.CTkButton(
            right_box, text="🗖 Modo Flutuante",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#1e2638", hover_color="#2b364e",
            text_color=self.c_text_white, corner_radius=10, width=130, height=38,
            command=self._toggle_mini_mode
        )
        self.btn_mini.pack(side=tk.LEFT, padx=(0, 12))

        # Main Power Button
        self.btn_power = ctk.CTkButton(
            right_box, text="▶ LIGAR CÂMERA",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=self.c_senai_red, hover_color=self.c_senai_red_hover,
            text_color="#ffffff", corner_radius=10, width=145, height=38,
            command=self._toggle_camera
        )
        self.btn_power.pack(side=tk.LEFT)

    # -------------------------------------------------------------
    # MAIN BODY LAYOUT (TWO MODERN CARDS)
    # -------------------------------------------------------------
    def _build_main_layout(self):
        """Constructs modern two-column workspace."""
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        # -------------------------------------------------------------
        # LEFT CARD: Camera & Action Telemetry
        # -------------------------------------------------------------
        self.left_card = ctk.CTkFrame(
            self.body_frame, fg_color=self.c_card, corner_radius=18,
            border_width=1, border_color=self.c_card_border, width=440
        )
        self.left_card.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 12))
        self.left_card.pack_propagate(False)

        # Card Title + FPS
        left_header = ctk.CTkFrame(self.left_card, fg_color="transparent")
        left_header.pack(fill=tk.X, padx=18, pady=(14, 8))

        ctk.CTkLabel(
            left_header, text="VISÃO DA CÂMERA",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.c_text_white
        ).pack(side=tk.LEFT)

        self.fps_badge = ctk.CTkLabel(
            left_header, text="0 FPS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_text_muted, fg_color="#182030",
            corner_radius=8, padx=8, pady=2
        )
        self.fps_badge.pack(side=tk.RIGHT)

        # Camera Device Selector Dropdown (Defaults to USB Webcam)
        cam_selector_frame = ctk.CTkFrame(self.left_card, fg_color="#0e131d", corner_radius=10, height=36)
        cam_selector_frame.pack(fill=tk.X, padx=18, pady=(0, 6))
        cam_selector_frame.pack_propagate(False)

        ctk.CTkLabel(
            cam_selector_frame, text="📷 Câmera:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_text_muted
        ).pack(side=tk.LEFT, padx=(10, 6))

        menu_values = [cam["label"] for cam in self.camera_list] if self.camera_list else ["Câmera 0"]
        default_val = self.camera_list[0]["label"] if self.camera_list else "Câmera 0"

        self.cam_dropdown = ctk.CTkOptionMenu(
            cam_selector_frame,
            values=menu_values,
            command=self._on_camera_selected,
            fg_color="#182030",
            button_color="#222d42",
            button_hover_color=self.c_senai_red,
            dropdown_fg_color="#121724",
            dropdown_hover_color="#1c2436",
            dropdown_text_color="#ffffff",
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=10),
            corner_radius=8,
            height=26
        )
        self.cam_dropdown.set(default_val)
        self.cam_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=5)

        # Camera Display Canvas
        self.cam_canvas = tk.Canvas(
            self.left_card, bg="#000000", width=400, height=300,
            highlightthickness=1, highlightbackground=self.c_card_border
        )
        self.cam_canvas.pack(padx=18, pady=4)

        self.cam_placeholder = self.cam_canvas.create_text(
            200, 150, text="Iniciando câmera...\nSua mão controlará toda a tela.",
            fill="#64748b", font=("Segoe UI", 11, "bold"), justify=tk.CENTER
        )

        # Action Feedback Pill (Clean, glowing status banner)
        self.action_pill = ctk.CTkFrame(
            self.left_card, fg_color="#182133", corner_radius=12,
            border_width=1, border_color="#27354f", height=44
        )
        self.action_pill.pack(fill=tk.X, padx=18, pady=10)
        self.action_pill.pack_propagate(False)

        self.action_icon = ctk.CTkLabel(
            self.action_pill, text="⚪", font=ctk.CTkFont(size=14),
            text_color=self.c_text_muted
        )
        self.action_icon.pack(side=tk.LEFT, padx=(12, 6))

        self.action_label = ctk.CTkLabel(
            self.action_pill, text="Aguardando detecção da mão...",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_text_white
        )
        self.action_label.pack(side=tk.LEFT, padx=4)

        # Clean Instructions Card (4 gestures in modern mini-cards)
        guide_card = ctk.CTkFrame(
            self.left_card, fg_color="#0e131d", corner_radius=14,
            border_width=1, border_color=self.c_card_border
        )
        guide_card.pack(fill=tk.BOTH, expand=True, padx=18, pady=(4, 14))

        ctk.CTkLabel(
            guide_card, text="COMO CONTROLAR A TELA INTEIRA",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.c_senai_red
        ).pack(anchor="w", padx=12, pady=(10, 6))

        gestures = [
            ("☝️", "Apontar Indicador", "Move o mouse livremente por todos os cantos"),
            ("🤏", "Pinça Firme", "Clica no item apontado com trava anti-desvio"),
            ("⚡", "Dois Toques", "Duplo clique instantâneo"),
            ("📦", "Segurar Pinça", "Arrasta janelas, ícones e arquivos"),
            ("✌️", "Dois Dedos", "Rola páginas para cima ou para baixo")
        ]

        for icon, title, desc in gestures:
            row = ctk.CTkFrame(guide_card, fg_color="transparent")
            row.pack(fill=tk.X, padx=12, pady=2)

            ctk.CTkLabel(
                row, text=f"{icon}  {title}:",
                font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                text_color=self.c_text_white
            ).pack(side=tk.LEFT)

            ctk.CTkLabel(
                row, text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=self.c_text_muted
            ).pack(side=tk.RIGHT)

        # -------------------------------------------------------------
        # RIGHT CARD: Full-Screen Range Interactive Lab
        # -------------------------------------------------------------
        self.right_card = ctk.CTkFrame(
            self.body_frame, fg_color=self.c_card, corner_radius=18,
            border_width=1, border_color=self.c_card_border
        )
        self.right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Segmented Tab Selector (Modern pill tabs)
        tab_bar = ctk.CTkFrame(self.right_card, fg_color="transparent")
        tab_bar.pack(fill=tk.X, padx=18, pady=(14, 10))

        self.tab_selector = ctk.CTkSegmentedButton(
            tab_bar,
            values=["🎯 Alcance de Tela Inteira (4 Cantos)", "📦 Arraste de Peças", "🎨 Desenho Livre"],
            command=self._on_tab_changed,
            selected_color=self.c_senai_red,
            selected_hover_color=self.c_senai_red_hover,
            unselected_color="#182030",
            unselected_hover_color="#202c44",
            text_color=self.c_text_white,
            corner_radius=12, height=36,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.tab_selector.set("🎯 Alcance de Tela Inteira (4 Cantos)")
        self.tab_selector.pack(side=tk.LEFT)

        # Sub-container for tabs
        self.tab_body = ctk.CTkFrame(self.right_card, fg_color="transparent")
        self.tab_body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))

        # Build each tab view
        self._build_range_tab()
        self._build_drag_tab()
        self._build_draw_tab()

        self._show_tab("🎯 Alcance de Tela Inteira (4 Cantos)")

    # -------------------------------------------------------------
    # TAB 1: Teste de Alcance da Tela Inteira (4 Cantos + Centro)
    # -------------------------------------------------------------
    def _build_range_tab(self):
        self.frame_range = ctk.CTkFrame(self.tab_body, fg_color="transparent")

        # Top info strip
        info_strip = ctk.CTkFrame(self.frame_range, fg_color="#0e131d", corner_radius=12, height=40)
        info_strip.pack(fill=tk.X, pady=(0, 10))
        info_strip.pack_propagate(False)

        self.lbl_coverage = ctk.CTkLabel(
            info_strip, text="Cobertura da Tela: 0 / 5 Alvos Conquistados",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_senai_red
        )
        self.lbl_coverage.pack(side=tk.LEFT, padx=14)

        btn_reset_range = ctk.CTkButton(
            info_strip, text="Reiniciar Alvos", width=100, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#1c2538", hover_color="#293752",
            text_color=self.c_text_white, corner_radius=8,
            command=self._reset_range_targets
        )
        btn_reset_range.pack(side=tk.RIGHT, padx=10)

        # Large Full-Screen Simulation Canvas
        self.range_canvas = tk.Canvas(
            self.frame_range, bg="#0a0e17", highlightthickness=1,
            highlightbackground=self.c_card_border
        )
        self.range_canvas.pack(fill=tk.BOTH, expand=True)

        self.range_canvas.bind("<Configure>", lambda e: self._redraw_range_canvas())
        self.range_canvas.bind("<Button-1>", self._on_range_canvas_click)

    def _redraw_range_canvas(self):
        """Draws the full-screen range coverage test arena."""
        self.range_canvas.delete("all")
        cw = max(400, self.range_canvas.winfo_width())
        ch = max(300, self.range_canvas.winfo_height())

        # Grid lines for screen calibration feeling
        for gx in range(0, cw, 60):
            self.range_canvas.create_line(gx, 0, gx, ch, fill="#121826", width=1)
        for gy in range(0, ch, 60):
            self.range_canvas.create_line(0, gy, cw, gy, fill="#121826", width=1)

        # Update corner positions based on actual canvas size
        pad = 65
        self.coverage_nodes["top_left"]["pos"] = (pad, pad)
        self.coverage_nodes["top_right"]["pos"] = (cw - pad, pad)
        self.coverage_nodes["bottom_left"]["pos"] = (pad, ch - pad)
        self.coverage_nodes["bottom_right"]["pos"] = (cw - pad, ch - pad)
        self.coverage_nodes["center"]["pos"] = (cw // 2, ch // 2)

        # Instruction Text
        self.range_canvas.create_text(
            cw // 2, 22,
            text="TESTE DE ALCANCE: Mova sua mão até os 4 cantos e o centro para provar o alcance de 100% da tela!",
            fill="#94a3b8", font=("Segoe UI", 10, "bold")
        )

        # Draw the 5 coverage nodes
        hit_count = 0
        for key, node in self.coverage_nodes.items():
            nx, ny = node["pos"]
            is_hit = node["hit"]
            r = 30

            if is_hit:
                hit_count += 1
                self.range_canvas.create_oval(nx - r, ny - r, nx + r, ny + r, fill="#065f46", outline=self.c_success, width=2)
                self.range_canvas.create_text(nx, ny, text="✓", fill=self.c_text_white, font=("Segoe UI", 14, "bold"))
            else:
                self.range_canvas.create_oval(nx - r, ny - r, nx + r, ny + r, fill="#182030", outline=self.c_senai_red, width=2)
                self.range_canvas.create_oval(nx - 6, ny - 6, nx + 6, ny + 6, fill=self.c_senai_red, outline="")

            # Node label
            self.range_canvas.create_text(
                nx, ny + r + 14, text=node["name"],
                fill="#cbd5e1" if is_hit else "#64748b", font=("Segoe UI", 8, "bold")
            )

        self.lbl_coverage.configure(text=f"Cobertura da Tela: {hit_count} / 5 Alvos Conquistados ({int(hit_count * 20)}%)")

        # Celebration banner if 100% reached
        if hit_count == 5:
            self.range_canvas.create_rectangle(
                cw // 2 - 200, ch // 2 + 50, cw // 2 + 200, ch // 2 + 95,
                fill=self.c_senai_red, outline="#ffffff", width=2
            )
            self.range_canvas.create_text(
                cw // 2, ch // 2 + 72,
                text="🎉 100% DA TELA ALCANÇADA COM SUCESSO!",
                fill="#ffffff", font=("Segoe UI", 11, "bold")
            )

    def _on_range_canvas_click(self, event):
        cx, cy = event.x, event.y
        for key, node in self.coverage_nodes.items():
            nx, ny = node["pos"]
            if math.hypot(cx - nx, cy - ny) <= 35:
                node["hit"] = True
                self._redraw_range_canvas()
                break

    def _reset_range_targets(self):
        for node in self.coverage_nodes.values():
            node["hit"] = False
        self._redraw_range_canvas()

    # -------------------------------------------------------------
    # TAB 2: Arraste de Peças
    # -------------------------------------------------------------
    def _build_drag_tab(self):
        self.frame_drag = ctk.CTkFrame(self.tab_body, fg_color="transparent")

        self.drag_canvas = tk.Canvas(
            self.frame_drag, bg="#0a0e17", highlightthickness=1,
            highlightbackground=self.c_card_border
        )
        self.drag_canvas.pack(fill=tk.BOTH, expand=True)

        self.drag_canvas.bind("<Configure>", lambda e: self._redraw_drag_canvas())
        self.drag_canvas.bind("<ButtonPress-1>", self._on_drag_press)
        self.drag_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.drag_canvas.bind("<ButtonRelease-1>", self._on_drag_release)

    def _redraw_drag_canvas(self):
        self.drag_canvas.delete("all")
        cw = max(400, self.drag_canvas.winfo_width())
        ch = max(300, self.drag_canvas.winfo_height())

        # Area 1: Origem
        z1_w = int(cw * 0.44)
        self.drag_canvas.create_rectangle(20, 20, z1_w, ch - 20, fill="#101624", outline="#232f48", width=1, dash=(4, 4))
        self.drag_canvas.create_text(32, 34, text="ÁREA DE ORIGEM", anchor="nw", fill="#64748b", font=("Segoe UI", 9, "bold"))

        # Area 2: Destino (SENAI Red Theme)
        z2_x = int(cw * 0.56)
        self.drag_canvas.create_rectangle(z2_x, 20, cw - 20, ch - 20, fill="#1c1216", outline=self.c_senai_red, width=1, dash=(4, 4))
        self.drag_canvas.create_text(z2_x + 14, 34, text="ÁREA DE DESTINO (SENAI)", anchor="nw", fill=self.c_senai_red, font=("Segoe UI", 9, "bold"))

        # Items
        for i, item in enumerate(self.drag_items):
            x, y, w, h = item["x"], item["y"], item["w"], item["h"]
            is_active = (self.dragged_item_idx == i)
            border_c = "#ffffff" if is_active else "#334155"

            self.drag_canvas.create_rectangle(x, y, x + w, y + h, fill=item["color"], outline=border_c, width=2)
            self.drag_canvas.create_text(x + w // 2, y + h // 2, text=item["name"], fill="#ffffff", font=("Segoe UI", 9, "bold"))

    def _on_drag_press(self, event):
        x, y = event.x, event.y
        for i, item in enumerate(self.drag_items):
            if item["x"] <= x <= item["x"] + item["w"] and item["y"] <= y <= item["y"] + item["h"]:
                self.dragged_item_idx = i
                self.drag_offset = (x - item["x"], y - item["y"])
                self._redraw_drag_canvas()
                break

    def _on_drag_motion(self, event):
        if self.dragged_item_idx is not None:
            item = self.drag_items[self.dragged_item_idx]
            item["x"] = event.x - self.drag_offset[0]
            item["y"] = event.y - self.drag_offset[1]
            self._redraw_drag_canvas()

    def _on_drag_release(self, event):
        if self.dragged_item_idx is not None:
            item = self.drag_items[self.dragged_item_idx]
            cw = self.drag_canvas.winfo_width()
            item["zone"] = "destino" if item["x"] >= int(cw * 0.56) - 30 else "origem"
            self.dragged_item_idx = None
            self._redraw_drag_canvas()

    # -------------------------------------------------------------
    # TAB 3: Desenho Livre
    # -------------------------------------------------------------
    def _build_draw_tab(self):
        self.frame_draw = ctk.CTkFrame(self.tab_body, fg_color="transparent")

        top_strip = ctk.CTkFrame(self.frame_draw, fg_color="#0e131d", corner_radius=12, height=40)
        top_strip.pack(fill=tk.X, pady=(0, 10))
        top_strip.pack_propagate(False)

        ctk.CTkLabel(
            top_strip, text="Cor:", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_text_muted
        ).pack(side=tk.LEFT, padx=(12, 4))

        for color_hex, name in [(self.c_senai_red, "Vermelho"), (self.c_cyan, "Ciano"), ("#ffffff", "Branco")]:
            ctk.CTkButton(
                top_strip, text="", width=24, height=24, corner_radius=6,
                fg_color=color_hex, hover_color=color_hex,
                command=lambda c=color_hex: setattr(self, "draw_color", c)
            ).pack(side=tk.LEFT, padx=3)

        ctk.CTkButton(
            top_strip, text="Limpar Tela", width=90, height=26, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#1c2538", hover_color="#293752", text_color=self.c_text_white,
            command=lambda: self.draw_canvas.delete("all")
        ).pack(side=tk.RIGHT, padx=10)

        self.draw_canvas = tk.Canvas(
            self.frame_draw, bg="#0a0e17", highlightthickness=1,
            highlightbackground=self.c_card_border
        )
        self.draw_canvas.pack(fill=tk.BOTH, expand=True)

        self.draw_canvas.bind("<B1-Motion>", self._on_mouse_draw)
        self.draw_canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "last_draw_pt", None))

    def _on_mouse_draw(self, event):
        x, y = event.x, event.y
        if self.last_draw_pt:
            self.draw_canvas.create_line(
                self.last_draw_pt[0], self.last_draw_pt[1], x, y,
                fill=self.draw_color, width=self.draw_brush_size, capstyle=tk.ROUND, smooth=True
            )
        self.last_draw_pt = (x, y)

    def _on_tab_changed(self, choice):
        self._show_tab(choice)

    def _show_tab(self, choice):
        self.frame_range.pack_forget()
        self.frame_drag.pack_forget()
        self.frame_draw.pack_forget()

        if "Alcance" in choice:
            self.frame_range.pack(fill=tk.BOTH, expand=True)
            self._redraw_range_canvas()
        elif "Arraste" in choice:
            self.frame_drag.pack(fill=tk.BOTH, expand=True)
            self._redraw_drag_canvas()
        elif "Desenho" in choice:
            self.frame_draw.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------
    # FLOATING MINI-MODE (Use the mouse across entire Windows freely)
    # -------------------------------------------------------------
    def _toggle_mini_mode(self):
        """Toggles between full studio and a floating compact widget."""
        if not self.is_mini_mode:
            self.is_mini_mode = True
            self.body_frame.pack_forget()
            self.geometry("480x110+40+40")
            self.attributes("-topmost", True)
            self.btn_mini.configure(text="🗖 Restaurar Estúdio")
        else:
            self.is_mini_mode = False
            self.geometry("1240x780")
            self.attributes("-topmost", False)
            self.body_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 14))
            self.btn_mini.configure(text="🗖 Modo Flutuante")

    # -------------------------------------------------------------
    # ENGINE & TELEMETRY SYNC
    # -------------------------------------------------------------
    def _on_switch_full_screen(self):
        val = self.full_screen_switch.get()
        self.engine.update_params(control_system_mouse=bool(val))

    def _on_frame_ready(self, frame: np.ndarray):
        self.last_frame = frame

    def _on_telemetry_ready(self, telemetry: Dict[str, Any]):
        self.current_telemetry = telemetry

    def _on_engine_action(self, event_name: str, payload: Dict[str, Any]):
        pass  # Real cursor moves natively across full screen!

    def _update_loop(self):
        """Refreshes video frame and dynamic status pill."""
        if self.last_frame is not None and not self.is_mini_mode:
            try:
                frame_rgb = cv2.cvtColor(self.last_frame, cv2.COLOR_BGR2RGB)
                fh, fw = frame_rgb.shape[:2]
                tw, th = 400, 300
                scale = min(tw / fw, th / fh)
                nw, nh = int(fw * scale), int(fh * scale)

                resized = cv2.resize(frame_rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
                img = Image.fromarray(resized)
                self.photo_image = ImageTk.PhotoImage(image=img)
                self.cam_canvas.delete("all")
                self.cam_canvas.create_image(200, 150, image=self.photo_image, anchor=tk.CENTER)
            except Exception:
                pass

        # Update telemetry status pill
        if self.current_telemetry:
            t = self.current_telemetry
            fps = t.get("fps", 0.0)
            self.fps_badge.configure(text=f"{int(fps)} FPS")

            hand_detected = t.get("hand_detected", False)
            is_locked = t.get("is_locked", False)
            is_dragging = t.get("is_dragging", False)
            is_scrolling = t.get("is_scrolling", False)
            action = t.get("action", "")

            if not hand_detected:
                self.action_icon.configure(text="⚪", text_color=self.c_text_muted)
                self.action_label.configure(text="Aguardando mão à frente da câmera...", text_color=self.c_text_muted)
                self.action_pill.configure(border_color="#20283c")
            elif is_dragging:
                self.action_icon.configure(text="📦", text_color="#f59e0b")
                self.action_label.configure(text="Arrastando Objeto / Janela", text_color="#f59e0b")
                self.action_pill.configure(border_color="#f59e0b")
            elif is_locked:
                self.action_icon.configure(text="🎯", text_color=self.c_senai_red)
                self.action_label.configure(text="Trava Magnética — Pronto para Clicar!", text_color=self.c_senai_red)
                self.action_pill.configure(border_color=self.c_senai_red)
            elif "Clique" in action:
                self.action_icon.configure(text="🔴", text_color=self.c_senai_red)
                self.action_label.configure(text="Clique Realizado!", text_color=self.c_text_white)
                self.action_pill.configure(border_color=self.c_senai_red)
            elif is_scrolling:
                self.action_icon.configure(text="📜", text_color=self.c_cyan)
                self.action_label.configure(text="Rolagem de Página com 2 Dedos", text_color=self.c_cyan)
                self.action_pill.configure(border_color=self.c_cyan)
            else:
                self.action_icon.configure(text="🟢", text_color=self.c_success)
                self.action_label.configure(text="Mão Rastreada — Movendo por Toda a Tela", text_color=self.c_text_white)
                self.action_pill.configure(border_color=self.c_success)

        self.after(33, self._update_loop)

    def _toggle_camera(self):
        if not self.is_camera_active:
            success = self.engine.start(cam_index=self.selected_camera_index)
            if success:
                self.is_camera_active = True
                self.btn_power.configure(text="⏹ PARAR CÂMERA", fg_color="#334155", hover_color="#475569")
            else:
                self.cam_canvas.delete("all")
                self.cam_canvas.create_text(
                    200, 150,
                    text="Erro ao abrir a câmera selecionada.\nVerifique se o cabo USB está conectado.",
                    fill="#ef4444", font=("Segoe UI", 11, "bold"), justify=tk.CENTER
                )
        else:
            self.engine.stop()
            self.is_camera_active = False
            self.btn_power.configure(text="▶ LIGAR CÂMERA", fg_color=self.c_senai_red, hover_color=self.c_senai_red_hover)
            if not self.is_mini_mode:
                self.cam_canvas.delete("all")
                self.cam_canvas.create_text(200, 150, text="Câmera pausada.", fill="#64748b", font=("Segoe UI", 11, "bold"))

    def _on_camera_selected(self, choice: str):
        target_idx = self.camera_map.get(choice, 0)
        if target_idx == self.selected_camera_index and self.is_camera_active:
            return

        self.selected_camera_index = target_idx
        if self.is_camera_active:
            self.engine.stop()
            time.sleep(0.15)
            success = self.engine.start(cam_index=self.selected_camera_index)
            if not success:
                self.is_camera_active = False
                self.btn_power.configure(text="▶ LIGAR CÂMERA", fg_color=self.c_senai_red, hover_color=self.c_senai_red_hover)
                self.cam_canvas.delete("all")
                self.cam_canvas.create_text(
                    200, 150,
                    text=f"Erro ao inicializar {choice}.\nTente selecionar outro dispositivo.",
                    fill="#ef4444", font=("Segoe UI", 11, "bold"), justify=tk.CENTER
                )

    def _on_close(self):
        if self.is_camera_active:
            self.engine.stop()
        self.destroy()


def run_app():
    app = ModernSenaiMouseApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
