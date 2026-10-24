"""
AI Virtual Mouse Engine - Multi-Mode Gesture Processor & Telemetry Engine
Supports:
1. Touchless Pro (MacBook / Apple Vision Pro tier with Anti-Slip Magnetic Lock)
2. Classic Mode (Index pointer + Middle pinch click)
3. Iron Man Sci-Fi HUD Mode (Holographic Arc Reactor & Cybernetic Telemetry)
"""

import os
import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import math
import time
import threading
import urllib.request
from typing import Callable, Optional, Dict, Any, List, Tuple

# Disable pyautogui safety delays for instantaneous response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

# Hand Landmark Connections
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),        # Indicador
    (5, 9), (9, 10), (10, 11), (11, 12),    # Médio
    (9, 13), (13, 14), (14, 15), (15, 16), # Anelar
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17) # Mínimo e palma
]


class UniversalHandTracker:
    """
    Unified Hand Tracker supporting both MediaPipe Tasks (Python 3.13+)
    and legacy MediaPipe Solutions (Python 3.8 - 3.12).
    """
    def __init__(self, model_path: str = "hand_landmarker.task", max_hands: int = 1):
        self.use_tasks = False
        self.detector = None
        self.legacy_hands = None
        self.max_hands = max_hands

        # Check if legacy mp.solutions is available
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            try:
                self.mp_hands = mp.solutions.hands
                self.legacy_hands = self.mp_hands.Hands(
                    max_num_hands=max_hands,
                    min_detection_confidence=0.65,
                    min_tracking_confidence=0.65
                )
                self.use_tasks = False
                return
            except Exception:
                pass

        # Fallback to MediaPipe Tasks API
        self.use_tasks = True
        self._init_tasks(model_path)

    def _init_tasks(self, model_path: str):
        if not os.path.exists(model_path):
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            try:
                urllib.request.urlretrieve(url, model_path)
            except Exception as e:
                raise RuntimeError(f"Could not download hand landmark model: {e}")

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr: np.ndarray) -> List[List[Tuple[float, float, float]]]:
        """
        Processes BGR frame and returns list of hand landmarks:
        Each hand is a list of 21 (x, y, z) normalized coordinates.
        """
        if not self.use_tasks and self.legacy_hands:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            res = self.legacy_hands.process(rgb)
            if not res.multi_hand_landmarks:
                return []
            hands_out = []
            for hand_lms in res.multi_hand_landmarks:
                pts = [(lm.x, lm.y, getattr(lm, 'z', 0.0)) for lm in hand_lms.landmark]
                hands_out.append(pts)
            return hands_out

        # Tasks API
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        res = self.detector.detect(mp_image)
        if not res.hand_landmarks:
            return []

        hands_out = []
        for hand in res.hand_landmarks:
            pts = [(lm.x, lm.y, getattr(lm, 'z', 0.0)) for lm in hand]
            hands_out.append(pts)
        return hands_out


class OneEuroFilter:
    """Adaptive 1-Euro Filter for jitter-free tracking without lag."""
    def __init__(self, t0: float, x0: float, dx0: float = 0.0, min_cutoff: float = 0.9, beta: float = 0.022, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def _smoothing_factor(self, t_e: float, cutoff: float) -> float:
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def _exp_smoothing(self, a: float, x: float, x_prev: float) -> float:
        return a * x + (1 - a) * x_prev

    def filter(self, t: float, x: float) -> float:
        t_e = t - self.t_prev
        if t_e <= 0.0001:
            return self.x_prev

        a_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self._exp_smoothing(a_d, dx, self.dx_prev)

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._smoothing_factor(t_e, cutoff)
        x_hat = self._exp_smoothing(a, x, self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

    def reset(self, t0: float, x0: float):
        self.x_prev = float(x0)
        self.dx_prev = 0.0
        self.t_prev = float(t0)


class VirtualMouseEngine:
    """
    Core computer vision and gesture processing engine for AI Virtual Mouse.
    Runs asynchronously, processes video frames and landmark tracking,
    and reports telemetry & gesture events to callbacks.
    """
    MODES = ["Touchless Pro (Trava Magnetica)", "Modo Classico", "Iron Man HUD"]

    def __init__(self):
        # Configuration
        self.cam_index = 0
        self.cam_w = 640
        self.cam_h = 480
        self.margin_x = 90
        self.margin_y = 70
        self.flip_horizontal = True
        self.control_system_mouse = True
        self.current_mode = "Touchless Pro (Trava Magnetica)"
        self.draw_skeleton = True
        self.draw_hud = True

        # Sensitivity and filter parameters
        self.min_cutoff = 0.9
        self.beta = 0.022
        self.click_sensitivity = 1.0  # multiplier for click thresholds

        # Screen dimensions
        try:
            self.screen_w, self.screen_h = pyautogui.size()
        except Exception:
            self.screen_w, self.screen_h = 1920, 1080

        # State machines & filters
        t_init = time.time()
        self.filter_x = OneEuroFilter(t_init, self.screen_w / 2, min_cutoff=self.min_cutoff, beta=self.beta)
        self.filter_y = OneEuroFilter(t_init, self.screen_h / 2, min_cutoff=self.min_cutoff, beta=self.beta)

        # Gestures state tracking
        self.is_locked = False
        self.locked_screen_pos = (self.screen_w / 2, self.screen_h / 2)
        self.locked_norm_pos = (0.5, 0.5)
        self.locked_cam_pos = (self.cam_w // 2, self.cam_h // 2)
        self.has_clicked_in_lock = False
        self.is_dragging = False
        self.lock_start_time = 0.0
        self.last_click_time = 0.0

        self.DRAG_HOLD_DELAY = 0.32
        self.DOUBLE_CLICK_GAP = 0.40

        # Right click state
        self.is_right_pinching = False
        self.right_pinch_start = 0.0

        # Scroll state
        self.is_scrolling = False
        self.prev_scroll_y = None

        # Iron Man animation
        self.arc_angle = 0.0

        # Runtime & Threading
        self.cap: Optional[cv2.VideoCapture] = None
        self.cam_name: str = ""
        self.cam_index: Optional[int] = None
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Callbacks
        self.on_frame_ready: Optional[Callable[[np.ndarray], None]] = None
        self.on_telemetry_ready: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_action_event: Optional[Callable[[str, Dict[str, Any]], None]] = None

        # Universal Tracker
        self.tracker = UniversalHandTracker(model_path="hand_landmarker.task", max_hands=1)

        # Metrics
        self.fps = 0.0
        self.last_fps_time = time.time()

    def start(self, cam_index: Optional[int] = None) -> bool:
        """Starts video capture and background processing."""
        with self.lock:
            if self.is_running:
                return True

            from camera_utils import get_default_camera_index, open_camera

            if cam_index is None:
                self.cam_index = get_default_camera_index()
            else:
                self.cam_index = cam_index

            self.cap, self.cam_name, self.cam_index = open_camera(self.cam_index, self.cam_w, self.cam_h)

            if not self.cap or not self.cap.isOpened():
                return False

            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_loop, daemon=True)
            self.worker_thread.start()
            return True

    def stop(self):
        """Stops video capture and thread."""
        with self.lock:
            self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.5)
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None

    def update_params(self, **kwargs):
        """Dynamically update engine parameters."""
        with self.lock:
            if "min_cutoff" in kwargs or "beta" in kwargs:
                self.min_cutoff = kwargs.get("min_cutoff", self.min_cutoff)
                self.beta = kwargs.get("beta", self.beta)
                self.filter_x.min_cutoff = self.min_cutoff
                self.filter_x.beta = self.beta
                self.filter_y.min_cutoff = self.min_cutoff
                self.filter_y.beta = self.beta
            if "margin_x" in kwargs:
                self.margin_x = int(kwargs["margin_x"])
            if "margin_y" in kwargs:
                self.margin_y = int(kwargs["margin_y"])
            if "click_sensitivity" in kwargs:
                self.click_sensitivity = float(kwargs["click_sensitivity"])
            if "control_system_mouse" in kwargs:
                self.control_system_mouse = bool(kwargs["control_system_mouse"])
            if "current_mode" in kwargs:
                self.current_mode = kwargs["current_mode"]
            if "draw_skeleton" in kwargs:
                self.draw_skeleton = bool(kwargs["draw_skeleton"])
            if "draw_hud" in kwargs:
                self.draw_hud = bool(kwargs["draw_hud"])
            if "flip_horizontal" in kwargs:
                self.flip_horizontal = bool(kwargs["flip_horizontal"])

    def _process_loop(self):
        """Continuous camera grab & gesture processing."""
        while True:
            with self.lock:
                if not self.is_running or not self.cap:
                    break
                ret, frame = self.cap.read()

            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Standardize resolution for predictable performance and margins
            if frame.shape[1] != self.cam_w or frame.shape[0] != self.cam_h:
                frame = cv2.resize(frame, (self.cam_w, self.cam_h), interpolation=cv2.INTER_LINEAR)

            t_current = time.time()
            dt = t_current - self.last_fps_time
            if dt > 0:
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
            self.last_fps_time = t_current

            if self.flip_horizontal:
                frame = cv2.flip(frame, 1)

            annotated_frame = frame.copy()
            hands = self.tracker.process_frame(annotated_frame)
            telemetry = self._process_hand_gestures(annotated_frame, hands, t_current)

            # Send callbacks
            if self.on_frame_ready:
                self.on_frame_ready(annotated_frame)
            if self.on_telemetry_ready:
                self.on_telemetry_ready(telemetry)

        # Cleanup mouse button on exit if dragging
        if self.is_dragging and self.control_system_mouse:
            try:
                pyautogui.mouseUp()
            except Exception:
                pass

    def _process_hand_gestures(self, frame: np.ndarray, hands: List[List[Tuple[float, float, float]]], t_current: float) -> Dict[str, Any]:
        """Core gesture recognition and action dispatch."""
        h, w, _ = frame.shape
        self.arc_angle = (self.arc_angle + 6) % 360

        # Draw Active Zone bounds
        cv2.rectangle(frame, (self.margin_x, self.margin_y),
                      (w - self.margin_x, h - self.margin_y),
                      (60, 60, 60), 1)

        telemetry: Dict[str, Any] = {
            "fps": round(self.fps, 1),
            "hand_detected": False,
            "mode": self.current_mode,
            "action": "Aguardando mao...",
            "fingers": [0, 0, 0, 0, 0],  # Thumb, Index, Middle, Ring, Pinky
            "pinch_dist": 0.0,
            "pinch_norm": 0.0,
            "right_pinch_dist": 0.0,
            "cursor_pos": (0, 0),
            "norm_pos": (0.5, 0.5),
            "is_locked": False,
            "is_dragging": False,
            "is_scrolling": False
        }

        if not hands:
            if self.is_dragging:
                self.is_dragging = False
                if self.control_system_mouse:
                    pyautogui.mouseUp()
                self._dispatch_event("drag_end", {"norm_pos": self.locked_norm_pos})
            self.is_locked = False
            self.is_scrolling = False
            return telemetry

        telemetry["hand_detected"] = True
        landmarks = hands[0]

        def get_px(idx):
            return int(landmarks[idx][0] * w), int(landmarks[idx][1] * h)

        wrist_px = get_px(0)
        thumb_px = get_px(4)
        index_px = get_px(8)
        middle_px = get_px(12)
        ring_px = get_px(16)
        pinky_px = get_px(20)

        thumb_mcp = get_px(2)
        index_pip = get_px(6)
        middle_pip = get_px(10)
        ring_pip = get_px(14)
        pinky_pip = get_px(18)

        # Finger extensions
        thumb_up = math.hypot(thumb_px[0] - pinky_pip[0], thumb_px[1] - pinky_pip[1]) > \
                   math.hypot(thumb_mcp[0] - pinky_pip[0], thumb_mcp[1] - pinky_pip[1]) * 1.15
        index_up = index_px[1] < index_pip[1]
        middle_up = middle_px[1] < middle_pip[1]
        ring_up = ring_px[1] < ring_pip[1]
        pinky_up = pinky_px[1] < pinky_pip[1]

        fingers = [int(thumb_up), int(index_up), int(middle_up), int(ring_up), int(pinky_up)]
        telemetry["fingers"] = fingers

        # Hand scale normalization
        hand_scale = max(60, math.hypot(wrist_px[0] - middle_pip[0], wrist_px[1] - middle_pip[1]))
        scale_ratio = (hand_scale / 120.0) * self.click_sensitivity

        # Distances
        dist_thumb_index = math.hypot(thumb_px[0] - index_px[0], thumb_px[1] - index_px[1])
        dist_thumb_middle = math.hypot(thumb_px[0] - middle_px[0], thumb_px[1] - middle_px[1])
        dist_index_middle = math.hypot(index_px[0] - middle_px[0], index_px[1] - middle_px[1])

        telemetry["pinch_dist"] = round(dist_thumb_index, 1)
        telemetry["right_pinch_dist"] = round(dist_thumb_middle, 1)

        # Dynamic thresholds
        pre_lock_dist = int(52 * scale_ratio)
        pinch_click_dist = int(34 * scale_ratio)
        release_dist = int(58 * scale_ratio)

        telemetry["pinch_norm"] = max(0.0, min(1.0, (dist_thumb_index - pinch_click_dist) / max(1, (pre_lock_dist - pinch_click_dist))))

        # Calculate stable pointer
        stable_x = 0.75 * index_px[0] + 0.25 * index_pip[0]
        stable_y = 0.75 * index_px[1] + 0.25 * index_pip[1]

        norm_x = max(0.0, min(1.0, (stable_x - self.margin_x) / max(1, (w - 2 * self.margin_x))))
        norm_y = max(0.0, min(1.0, (stable_y - self.margin_y) / max(1, (h - 2 * self.margin_y))))

        raw_screen_x = norm_x * self.screen_w
        raw_screen_y = norm_y * self.screen_h

        smooth_screen_x = self.filter_x.filter(t_current, raw_screen_x)
        smooth_screen_y = self.filter_y.filter(t_current, raw_screen_y)
        smooth_screen_x = max(0, min(self.screen_w - 1, smooth_screen_x))
        smooth_screen_y = max(0, min(self.screen_h - 1, smooth_screen_y))

        smooth_norm_x = smooth_screen_x / self.screen_w
        smooth_norm_y = smooth_screen_y / self.screen_h

        telemetry["cursor_pos"] = (int(smooth_screen_x), int(smooth_screen_y))
        telemetry["norm_pos"] = (round(smooth_norm_x, 4), round(smooth_norm_y, 4))

        # Mode execution
        if self.current_mode == "Modo Classico":
            self._handle_classic_mode(frame, telemetry, index_up, middle_up, dist_index_middle,
                                     index_px, middle_px, smooth_screen_x, smooth_screen_y,
                                     smooth_norm_x, smooth_norm_y, t_current)
        else:
            self._handle_touchless_pro_mode(frame, telemetry, index_up, middle_up, ring_up, pinky_up,
                                            thumb_px, index_px, middle_px,
                                            dist_thumb_index, dist_thumb_middle, scale_ratio,
                                            pre_lock_dist, pinch_click_dist, release_dist,
                                            smooth_screen_x, smooth_screen_y, smooth_norm_x, smooth_norm_y,
                                            t_current)

        # Sci-Fi / Iron Man overlays
        if self.current_mode == "Iron Man HUD":
            self._draw_ironman_hud(frame, wrist_px, middle_pip, thumb_px, index_px, middle_px, ring_px, pinky_px)
        elif self.draw_skeleton:
            for pt1, pt2 in HAND_CONNECTIONS:
                cv2.line(frame, get_px(pt1), get_px(pt2), (100, 100, 100), 2)
            for i in range(21):
                color = (0, 255, 255) if i in [4, 8, 12] else (80, 220, 120)
                cv2.circle(frame, get_px(i), 4, color, -1)

        telemetry["is_locked"] = self.is_locked
        telemetry["is_dragging"] = self.is_dragging
        telemetry["is_scrolling"] = self.is_scrolling

        return telemetry

    def _handle_touchless_pro_mode(self, frame: np.ndarray, telemetry: Dict[str, Any],
                                  index_up: bool, middle_up: bool, ring_up: bool, pinky_up: bool,
                                  thumb_px, index_px, middle_px,
                                  dist_thumb_index, dist_thumb_middle, scale_ratio,
                                  pre_lock_dist, pinch_click_dist, release_dist,
                                  smooth_screen_x, smooth_screen_y, smooth_norm_x, smooth_norm_y,
                                  t_current: float):
        """Touchless Pro with Magnetic Lock, Two-Finger Scroll, and Drag-and-Drop."""
        # 1. Two-finger MacBook Scroll
        two_finger_mode = index_up and middle_up and not ring_up and not pinky_up and dist_thumb_index > (50 * scale_ratio)

        if two_finger_mode:
            self.is_scrolling = True
            avg_y = (index_px[1] + middle_px[1]) / 2.0
            telemetry["action"] = "Rolagem (MacBook 2 Dedos)"
            cv2.line(frame, index_px, middle_px, (0, 215, 255), 3)

            if self.prev_scroll_y is not None:
                dy = avg_y - self.prev_scroll_y
                if abs(dy) > 1.5:
                    scroll_amount = -int(dy * 15)
                    if self.control_system_mouse:
                        pyautogui.scroll(scroll_amount)
                    self._dispatch_event("scroll", {"dy": dy, "amount": scroll_amount})

            self.prev_scroll_y = avg_y
            return

        self.is_scrolling = False
        self.prev_scroll_y = None

        # 2. Magnetic Target Lock check
        if not self.is_locked and not self.is_right_pinching:
            if dist_thumb_index < pre_lock_dist:
                self.is_locked = True
                self.locked_screen_pos = (smooth_screen_x, smooth_screen_y)
                self.locked_norm_pos = (smooth_norm_x, smooth_norm_y)
                self.locked_cam_pos = index_px
                self.lock_start_time = t_current
                self.has_clicked_in_lock = False

        if self.is_locked:
            lock_duration = t_current - self.lock_start_time

            # Freeze cursor on target while locked unless dragging
            target_x = self.locked_screen_pos[0] if not self.is_dragging else smooth_screen_x
            target_y = self.locked_screen_pos[1] if not self.is_dragging else smooth_screen_y
            target_norm = self.locked_norm_pos if not self.is_dragging else (smooth_norm_x, smooth_norm_y)

            if self.control_system_mouse:
                pyautogui.moveTo(target_x, target_y)
            self._dispatch_event("pointer_move", {"norm_pos": target_norm, "screen_pos": (target_x, target_y)})

            if not self.is_dragging:
                telemetry["action"] = "Trava Magnetica Ativa (Pre-Clique)"
            else:
                telemetry["action"] = "Arrastando Item / Janela (Drag)"

            # Contact reached -> Trigger Click!
            if dist_thumb_index < pinch_click_dist and not self.has_clicked_in_lock:
                self.has_clicked_in_lock = True
                if (t_current - self.last_click_time) < self.DOUBLE_CLICK_GAP:
                    if self.control_system_mouse:
                        pyautogui.doubleClick()
                    telemetry["action"] = "Duplo Clique!"
                    self._dispatch_event("double_click", {"norm_pos": target_norm, "screen_pos": (target_x, target_y)})
                    self.last_click_time = 0.0
                else:
                    if self.control_system_mouse:
                        pyautogui.click()
                    telemetry["action"] = "Clique Simples!"
                    self._dispatch_event("click", {"norm_pos": target_norm, "screen_pos": (target_x, target_y)})
                    self.last_click_time = t_current

            # Drag transition
            if self.has_clicked_in_lock and not self.is_dragging:
                if lock_duration > self.DRAG_HOLD_DELAY and dist_thumb_index < pinch_click_dist + 10:
                    self.is_dragging = True
                    if self.control_system_mouse:
                        pyautogui.mouseDown()
                    self._dispatch_event("drag_start", {"norm_pos": target_norm, "screen_pos": (target_x, target_y)})

            # Drag motion
            if self.is_dragging:
                self._dispatch_event("drag_move", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})

            # Release
            if dist_thumb_index > release_dist:
                if self.is_dragging:
                    if self.control_system_mouse:
                        pyautogui.mouseUp()
                    self._dispatch_event("drag_end", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})
                    self.is_dragging = False
                    telemetry["action"] = "Soltou (Drop)"
                self.is_locked = False
                self.has_clicked_in_lock = False

            # Draw crosshair at locked cam position
            cx, cy = self.locked_cam_pos
            cv2.circle(frame, (cx, cy), 18, (0, 255, 255), 2)
            cv2.line(frame, (cx - 24, cy), (cx + 24, cy), (0, 255, 255), 1)
            cv2.line(frame, (cx, cy - 24), (cx, cy + 24), (0, 255, 255), 1)

        else:
            # Free tracking
            if self.control_system_mouse:
                pyautogui.moveTo(smooth_screen_x, smooth_screen_y)
            self._dispatch_event("pointer_move", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})
            telemetry["action"] = "Rastreando Apontador"

        # 3. Right Click check (Thumb + Middle pinch)
        if not self.is_locked and not self.is_dragging:
            if not self.is_right_pinching:
                if dist_thumb_middle < (32 * scale_ratio) and dist_thumb_index > (45 * scale_ratio):
                    self.is_right_pinching = True
                    self.right_pinch_start = t_current
            else:
                if dist_thumb_middle > (45 * scale_ratio):
                    self.is_right_pinching = False
                    if (t_current - self.right_pinch_start) < 0.45:
                        if self.control_system_mouse:
                            pyautogui.rightClick()
                        telemetry["action"] = "Clique com Botao Direito"
                        self._dispatch_event("right_click", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})

        # Visual pinch guide line and circle
        mid_x = int((thumb_px[0] + index_px[0]) / 2)
        mid_y = int((thumb_px[1] + index_px[1]) / 2)
        color = (0, 255, 0) if dist_thumb_index < pinch_click_dist else ((0, 255, 255) if self.is_locked else (255, 180, 0))
        cv2.line(frame, thumb_px, index_px, (160, 160, 160), 1)
        cv2.circle(frame, index_px, 6, (0, 255, 255), -1)
        cv2.circle(frame, thumb_px, 5, (255, 120, 0), -1)
        cv2.circle(frame, (mid_x, mid_y), int(8 + telemetry["pinch_norm"] * 16), color, 2)

    def _handle_classic_mode(self, frame: np.ndarray, telemetry: Dict[str, Any],
                             index_up: bool, middle_up: bool, dist_index_middle: float,
                             index_px, middle_px, smooth_screen_x, smooth_screen_y,
                             smooth_norm_x, smooth_norm_y, t_current: float):
        """Classic mode: Index moves, Index+Middle pinch/together clicks."""
        if index_up and not middle_up:
            telemetry["action"] = "Movendo Cursor (Modo Classico)"
            if self.control_system_mouse:
                pyautogui.moveTo(smooth_screen_x, smooth_screen_y)
            self._dispatch_event("pointer_move", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})
            cv2.circle(frame, index_px, 12, (255, 0, 255), cv2.FILLED)

        elif index_up and middle_up:
            cx = (index_px[0] + middle_px[0]) // 2
            cy = (index_px[1] + middle_px[1]) // 2
            cv2.line(frame, index_px, middle_px, (255, 0, 255), 2)
            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

            if dist_index_middle < 40:
                cv2.circle(frame, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                if (t_current - self.last_click_time) > 0.35:
                    if self.control_system_mouse:
                        pyautogui.click()
                    telemetry["action"] = "Clique Classico!"
                    self._dispatch_event("click", {"norm_pos": (smooth_norm_x, smooth_norm_y), "screen_pos": (smooth_screen_x, smooth_screen_y)})
                    self.last_click_time = t_current
            else:
                telemetry["action"] = "Pronto para Clicar (Aproxime os 2 dedos)"

    def _draw_ironman_hud(self, frame: np.ndarray, wrist_px, middle_pip, thumb_px, index_px, middle_px, ring_px, pinky_px):
        """Draws Iron Man holographic Arc Reactor on palm and laser conduits."""
        cx = (wrist_px[0] + middle_pip[0]) // 2
        cy = (wrist_px[1] + middle_pip[1]) // 2
        radius = max(24, int(math.hypot(wrist_px[0] - middle_pip[0], wrist_px[1] - middle_pip[1]) * 0.35))

        color = (0, 255, 255)  # Cyan / Jarvis Gold
        # Arc reactor rings
        cv2.circle(frame, (cx, cy), int(radius * 0.4), (255, 255, 255), -1)
        cv2.circle(frame, (cx, cy), radius, color, 2)
        cv2.circle(frame, (cx, cy), int(radius * 0.75), (0, 200, 255), 1)

        # 8 Rotating tech ticks
        for i in range(8):
            theta = math.radians(self.arc_angle + i * 45)
            r1, r2 = radius - 4, radius + 6
            x1 = int(cx + r1 * math.cos(theta))
            y1 = int(cy + r1 * math.sin(theta))
            x2 = int(cx + r2 * math.cos(theta))
            y2 = int(cy + r2 * math.sin(theta))
            cv2.line(frame, (x1, y1), (x2, y2), color, 2)

        # Glowing energy conduits to all 5 fingertips
        tips = [thumb_px, index_px, middle_px, ring_px, pinky_px]
        for tip in tips:
            cv2.line(frame, (cx, cy), tip, (0, 220, 255), 1)
            cv2.circle(frame, tip, 5, (0, 255, 255), -1)

    def _dispatch_event(self, event_name: str, payload: Dict[str, Any]):
        """Dispatches an action event to callback."""
        if self.on_action_event:
            self.on_action_event(event_name, payload)
