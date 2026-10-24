"""
IRONMAN & MACBOOK TOUCHLESS PRO (JARVIS INTERFACE)
=================================================
Combines:
1. ANDREW'S LAB SYSTEM PRODUCTIVITY GESTURES:
   - Swipe Left (Open Palm): Switch to Next Virtual Desktop (Win + Ctrl + Right)
   - Swipe Right (Open Palm): Switch to Previous Virtual Desktop (Win + Ctrl + Left)
   - Swipe Up (Open Palm): Task View / Mission Control (Win + Tab)
   - Swipe Down (Open Palm): Show Desktop / Minimize All (Win + D)
   - Two-Finger MacBook Scroll: Natural inertial page scrolling
   - Apple Pinch with Magnetic Target Lock: Jitter-free, 100% accurate clicking
   - Pinch & Hold: Drag and drop windows/icons
   - Thumb + Middle Pinch: Right click context menu

2. VERSAO NAO FINALIZADA (HOMEM DE FERRO / SCI-FI HUD):
   - Holographic Arc Reactor HUD on the palm with rotating angular ticks
   - Sci-Fi Energy Conduits connecting palm core to all 5 fingertips
   - Dual-Hand Holographic Zoom: Pinch with both hands and expand/contract
     to zoom in/out with Tony Stark holographic laser beam!
   - Twin Repulsor Shield: Open both palms to camera for repulsor defense mode
   - Cybernetic telemetry HUD overlay (FPS, Coords, System Status)
"""

import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import math
import time
from collections import deque

# Disable safety delays for instantaneous response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

# ---------------------------------------------------------
# 1. One Euro Filter for Jitter-Free Motion
# ---------------------------------------------------------
class OneEuroFilter:
    def __init__(self, t0, x0, dx0=0.0, min_cutoff=0.9, beta=0.022, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def _smoothing_factor(self, t_e, cutoff):
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def _exp_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev

    def filter(self, t, x):
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


# ---------------------------------------------------------
# 2. Sci-Fi HUD Rendering Helpers (Iron Man Aesthetics)
# ---------------------------------------------------------
def draw_arc_reactor(frame, center, radius, angle_deg, color=(0, 255, 255), is_repulsor=False):
    """Draws a rotating Iron Man Arc Reactor hologram on the palm."""
    cx, cy = center
    if radius < 15:
        radius = 15

    # Core inner glow
    core_rad = int(radius * 0.35)
    cv2.circle(frame, (cx, cy), core_rad, (255, 255, 255), -1)
    cv2.circle(frame, (cx, cy), core_rad + 2, color, 2)

    # Concentric tech rings
    cv2.circle(frame, (cx, cy), radius, color, 1)
    cv2.circle(frame, (cx, cy), int(radius * 0.7), color, 1)

    # 8 Rotating tick marks
    num_ticks = 8
    for i in range(num_ticks):
        theta = math.radians(angle_deg + i * (360 / num_ticks))
        r1 = radius - 5
        r2 = radius + 6
        x1 = int(cx + r1 * math.cos(theta))
        y1 = int(cy + r1 * math.sin(theta))
        x2 = int(cx + r2 * math.cos(theta))
        y2 = int(cy + r2 * math.sin(theta))
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)

    # If repulsor mode active: draw outer energy shockwaves
    if is_repulsor:
        pulse_r = int(radius * 1.5 + 8 * math.sin(time.time() * 10))
        cv2.circle(frame, (cx, cy), pulse_r, (0, 165, 255), 2)
        cv2.circle(frame, (cx, cy), pulse_r + 10, (0, 100, 255), 1)


def draw_energy_conduits(frame, center, fingertips, color=(0, 220, 255)):
    """Draws glowing energy conduits from palm center to each fingertip."""
    cx, cy = center
    for tip in fingertips:
        cv2.line(frame, (cx, cy), tip, color, 1)
        cv2.circle(frame, tip, 4, (255, 255, 255), -1)
        cv2.circle(frame, tip, 6, color, 1)


from camera_utils import open_camera, get_default_camera_index


def get_usb_camera_cap(cam_w=640, cam_h=480):
    """
    Detects physical USB cameras on the system and prioritizes external USB webcams.
    Returns (cap, cam_name, cam_idx).
    """
    idx = get_default_camera_index()
    return open_camera(idx, cam_w, cam_h)



# ---------------------------------------------------------
# 3. Main Touchless Controller
# ---------------------------------------------------------

from tracker_utils import UniversalHandsDetector


def main():
    CAM_W, CAM_H = 640, 480
    cap, cam_name, cam_idx = get_usb_camera_cap(CAM_W, CAM_H)

    if not cap.isOpened():
        print(f"Erro: Nao foi possivel acessar a camera USB '{cam_name}' (Indice {cam_idx}).")
        return

    SCREEN_W, SCREEN_H = pyautogui.size()

    # Active tracking boundary
    MARGIN_X = 110
    MARGIN_Y = 85

    # MediaPipe Hands (Compatible with Python 3.8 - 3.13 Tasks & Solutions API)
    hands = UniversalHandsDetector(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    t_now = time.time()
    filter_x = OneEuroFilter(t_now, SCREEN_W / 2, min_cutoff=0.9, beta=0.022)
    filter_y = OneEuroFilter(t_now, SCREEN_H / 2, min_cutoff=0.9, beta=0.022)

    # State Machine Variables
    is_locked = False
    locked_screen_pos = (SCREEN_W / 2, SCREEN_H / 2)
    locked_cam_pos = (CAM_W // 2, CAM_H // 2)
    has_clicked_in_lock = False
    is_dragging = False
    lock_start_time = 0.0
    last_click_time = 0.0

    DRAG_HOLD_DELAY = 0.32
    DOUBLE_CLICK_GAP = 0.40

    # Right Click state
    is_right_pinching = False
    right_pinch_start = 0.0

    # Scroll state
    is_scrolling = False
    prev_scroll_y = None

    # System Productivity Swipe Engine (Andrew's Lab)
    palm_history = deque(maxlen=7)  # Records recent (time, x, y) for velocity
    last_system_swipe_time = 0.0
    SYSTEM_SWIPE_COOLDOWN = 0.85     # Prevents accidental rapid-fire triggers
    SWIPE_DIST_THRESHOLD = 55        # Pixels of displacement required for swipe

    # Dual-Hand Zoom State (Tony Stark Hologram)
    prev_dual_pinch_dist = None
    last_zoom_time = 0.0

    # UI Feedback
    current_action_label = "SYSTEM READY"
    label_color = (0, 255, 255)
    fps_time = time.time()
    fps = 30.0

    print("\n" + "="*65)
    print(" IRONMAN TOUCHLESS PRO - JARVIS INTERFACE ACTIVE")
    print(f" Camera Conectada: {cam_name} (USB DirectShow Indice {cam_idx})")
    print("="*65)
    print(" [SISTEMA MACBOOK / ANDREW'S LAB]")
    print("  - Cursor: Aponte com o indicador (Filtro One Euro)")
    print("  - Clique com Trava Magnetica: Pinca Polegar + Indicador")
    print("  - Arrastar (Drag): Segure a pinca por > 0.3s")
    print("  - Scroll MacBook: Dois dedos levantados (Indicador + Medio)")
    print("  - Swipe Esquerda (Mao Aberta): Proxima Area de Trabalho")
    print("  - Swipe Direita (Mao Aberta): Area de Trabalho Anterior")
    print("  - Swipe Cima (Mao Aberta): Visao de Tarefas (Win+Tab)")
    print("  - Swipe Baixo (Mao Aberta): Mostrar Desktop (Win+D)")
    print(" [SISTEMA HOMEM DE FERRO / TONY STARK]")
    print("  - HUD Holografico com Reator Arc na palma em tempo real")
    print("  - Zoom Holografico: Faca pinca com AS DUAS MAOS e afaste/junte")
    print("  - Escudo Repulsor: Abra as duas palmas viradas para a tela")
    print("  - Sair: Pressione 'q' na janela de video")
    print("="*65 + "\n")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        if frame.shape[1] != CAM_W or frame.shape[0] != CAM_H:
            frame = cv2.resize(frame, (CAM_W, CAM_H), interpolation=cv2.INTER_LINEAR)

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        t_current = time.time()

        # Calculate FPS
        dt_fps = t_current - fps_time
        if dt_fps > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt_fps)
        fps_time = t_current

        results = hands.process(rgb_frame)

        # Draw Active Tracking Zone Guide
        cv2.rectangle(frame, (MARGIN_X, MARGIN_Y), (CAM_W - MARGIN_X, CAM_H - MARGIN_Y),
                      (45, 45, 45), 1)

        num_hands = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
        hud_angle = (t_current * 100) % 360  # Continuous rotation for HUD rings

        # ---------------------------------------------------------
        # MODE A: DUAL-HAND INTERACTION (Tony Stark Hologram Mode)
        # ---------------------------------------------------------
        if num_hands >= 2:
            hand1 = results.multi_hand_landmarks[0].landmark
            hand2 = results.multi_hand_landmarks[1].landmark

            def get_hand_pts(lms):
                wrist = (int(lms[0].x * CAM_W), int(lms[0].y * CAM_H))
                thumb = (int(lms[4].x * CAM_W), int(lms[4].y * CAM_H))
                index = (int(lms[8].x * CAM_W), int(lms[8].y * CAM_H))
                palm = (int((wrist[0] + lms[9].x * CAM_W) / 2), int((wrist[1] + lms[9].y * CAM_H) / 2))
                return wrist, thumb, index, palm

            w1, th1, idx1, palm1 = get_hand_pts(hand1)
            w2, th2, idx2, palm2 = get_hand_pts(hand2)

            # Check if both hands are pinching (Thumb to Index)
            pinch1_dist = math.hypot(th1[0] - idx1[0], th1[1] - idx1[1])
            pinch2_dist = math.hypot(th2[0] - idx2[0], th2[1] - idx2[1])
            both_pinching = pinch1_dist < 42 and pinch2_dist < 42

            # Check if both hands are open repulsor palms
            fingers_up_count1 = sum(hand1[tip].y < hand1[pip].y for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)])
            fingers_up_count2 = sum(hand2[tip].y < hand2[pip].y for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)])
            both_repulsors = fingers_up_count1 >= 4 and fingers_up_count2 >= 4

            if both_pinching:
                # GESTURE: HOLOGRAPHIC DUAL-HAND ZOOM
                dual_dist = math.hypot(idx1[0] - idx2[0], idx1[1] - idx2[1])
                mid_zoom = ((idx1[0] + idx2[0]) // 2, (idx1[1] + idx2[1]) // 2)

                # Laser beam connecting pinches
                cv2.line(frame, idx1, idx2, (0, 255, 255), 2)
                cv2.circle(frame, idx1, 8, (0, 255, 0), -1)
                cv2.circle(frame, idx2, 8, (0, 255, 0), -1)
                cv2.circle(frame, mid_zoom, 14, (0, 255, 255), 2)

                if prev_dual_pinch_dist is not None:
                    delta_dist = dual_dist - prev_dual_pinch_dist
                    if (t_current - last_zoom_time) > 0.08:
                        if delta_dist > 10:
                            # Expanding hands -> ZOOM IN
                            pyautogui.hotkey('ctrl', '+')
                            last_zoom_time = t_current
                            current_action_label = "HOLOGRAPHIC ZOOM (+)"
                            label_color = (0, 255, 0)
                        elif delta_dist < -10:
                            # Contracting hands -> ZOOM OUT
                            pyautogui.hotkey('ctrl', '-')
                            last_zoom_time = t_current
                            current_action_label = "HOLOGRAPHIC ZOOM (-)"
                            label_color = (0, 150, 255)

                prev_dual_pinch_dist = dual_dist
                cv2.putText(frame, f"SCALE: {int(dual_dist)}px", (mid_zoom[0] - 50, mid_zoom[1] - 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            elif both_repulsors:
                # GESTURE: TWIN REPULSOR SHIELD
                draw_arc_reactor(frame, palm1, 38, hud_angle, (0, 255, 255), is_repulsor=True)
                draw_arc_reactor(frame, palm2, 38, -hud_angle, (0, 255, 255), is_repulsor=True)
                current_action_label = "REPULSOR SHIELD ACTIVE"
                label_color = (0, 165, 255)
                prev_dual_pinch_dist = None

            else:
                # Render standard Iron Man reactors for both hands
                draw_arc_reactor(frame, palm1, 28, hud_angle, (0, 220, 255))
                draw_arc_reactor(frame, palm2, 28, -hud_angle, (0, 220, 255))
                prev_dual_pinch_dist = None
                current_action_label = "DUAL HAND TELEMETRY"
                label_color = (200, 200, 200)

        # ---------------------------------------------------------
        # MODE B: SINGLE-HAND PRECISION & SYSTEM PRODUCTIVITY
        # ---------------------------------------------------------
        elif num_hands == 1:
            prev_dual_pinch_dist = None
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = hand_landmarks.landmark

            def get_px(idx):
                return int(landmarks[idx].x * CAM_W), int(landmarks[idx].y * CAM_H)

            wrist_px = get_px(0)
            thumb_px = get_px(4)
            index_px = get_px(8)
            middle_px = get_px(12)
            ring_px = get_px(16)
            pinky_px = get_px(20)

            index_pip = get_px(6)
            middle_pip = get_px(10)
            ring_pip = get_px(14)
            pinky_pip = get_px(18)

            # Palm center calculation
            palm_center = (
                int((wrist_px[0] + landmarks[9].x * CAM_W) / 2),
                int((wrist_px[1] + landmarks[9].y * CAM_H) / 2)
            )

            # Fingertips list for energy conduits
            all_tips = [thumb_px, index_px, middle_px, ring_px, pinky_px]

            # Extension checks
            index_up = index_px[1] < index_pip[1]
            middle_up = middle_px[1] < middle_pip[1]
            ring_up = ring_px[1] < ring_pip[1]
            pinky_up = pinky_px[1] < pinky_pip[1]

            # Count open fingers (excluding thumb)
            open_fingers_count = sum([index_up, middle_up, ring_up, pinky_up])
            all_fingers_open = open_fingers_count == 4

            # Hand scale normalization
            hand_scale = max(60, math.hypot(wrist_px[0] - middle_pip[0], wrist_px[1] - middle_pip[1]))
            scale_ratio = hand_scale / 120.0

            dist_thumb_index = math.hypot(thumb_px[0] - index_px[0], thumb_px[1] - index_px[1])
            dist_thumb_middle = math.hypot(thumb_px[0] - middle_px[0], thumb_px[1] - middle_px[1])

            PRE_LOCK_DIST = int(52 * scale_ratio)
            PINCH_CLICK_DIST = int(34 * scale_ratio)
            RELEASE_DIST = int(58 * scale_ratio)

            # RENDER: Iron Man Holographic Arc Reactor & Conduits
            reactor_radius = int(28 * scale_ratio)
            draw_arc_reactor(frame, palm_center, reactor_radius, hud_angle, (0, 240, 255), is_repulsor=all_fingers_open)
            draw_energy_conduits(frame, palm_center, all_tips, (0, 200, 255))

            # -------------------------------------------------------------
            # FEATURE 1: SYSTEM PRODUCTIVITY SWIPES (Andrew's Lab)
            # Full Open Palm Swipes (Desktop Switch / Mission Control / Desktop)
            # -------------------------------------------------------------
            if all_fingers_open and dist_thumb_index > (55 * scale_ratio):
                palm_history.append((t_current, palm_center[0], palm_center[1]))

                if len(palm_history) >= 4 and (t_current - last_system_swipe_time) > SYSTEM_SWIPE_COOLDOWN:
                    t_old, old_x, old_y = palm_history[0]
                    t_now_p, cur_x, cur_y = palm_history[-1]
                    dx = cur_x - old_x
                    dy = cur_y - old_y
                    dt = t_now_p - t_old

                    if dt > 0.04 and dt < 0.40:
                        # Horizontal Swipes (Switch Virtual Desktops)
                        if abs(dx) > SWIPE_DIST_THRESHOLD and abs(dx) > abs(dy) * 1.4:
                            if dx > 0:
                                # Swipe Right -> Previous Desktop
                                pyautogui.hotkey('win', 'ctrl', 'left')
                                current_action_label = "DESKTOP < PREVIOUS"
                                label_color = (0, 255, 120)
                                last_system_swipe_time = t_current
                                palm_history.clear()
                            else:
                                # Swipe Left -> Next Desktop
                                pyautogui.hotkey('win', 'ctrl', 'right')
                                current_action_label = "DESKTOP > NEXT"
                                label_color = (0, 255, 120)
                                last_system_swipe_time = t_current
                                palm_history.clear()

                        # Vertical Swipes (Mission Control / Desktop)
                        elif abs(dy) > SWIPE_DIST_THRESHOLD and abs(dy) > abs(dx) * 1.4:
                            if dy < 0:
                                # Swipe Up -> Mission Control (Task View)
                                pyautogui.hotkey('win', 'tab')
                                current_action_label = "MISSION CONTROL (Win+Tab)"
                                label_color = (255, 200, 0)
                                last_system_swipe_time = t_current
                                palm_history.clear()
                            else:
                                # Swipe Down -> Show Desktop
                                pyautogui.hotkey('win', 'd')
                                current_action_label = "SHOW DESKTOP (Win+D)"
                                label_color = (255, 120, 0)
                                last_system_swipe_time = t_current
                                palm_history.clear()

                if (t_current - last_system_swipe_time) < 0.6:
                    pass  # Keep displaying the swipe label
                else:
                    current_action_label = "OPEN PALM: SWIPE READY"
                    label_color = (0, 255, 255)

                is_scrolling = False
                prev_scroll_y = None

            # -------------------------------------------------------------
            # FEATURE 2: MacBook Two-Finger Scroll
            # -------------------------------------------------------------
            elif index_up and middle_up and not ring_up and not pinky_up and dist_thumb_index > (50 * scale_ratio):
                palm_history.clear()
                is_scrolling = True
                avg_y = (index_px[1] + middle_px[1]) / 2.0

                if prev_scroll_y is not None:
                    dy = avg_y - prev_scroll_y
                    if abs(dy) > 1.5:
                        scroll_amount = -int(dy * 15)
                        pyautogui.scroll(scroll_amount)

                prev_scroll_y = avg_y
                current_action_label = "MacBook Scroll Active"
                label_color = (0, 215, 255)
                cv2.line(frame, index_px, middle_px, (0, 215, 255), 3)

            # -------------------------------------------------------------
            # FEATURE 3: Pointer Tracking + Magnetic Lock Click
            # -------------------------------------------------------------
            else:
                palm_history.clear()
                is_scrolling = False
                prev_scroll_y = None

                # Blended stabilized anchor
                stable_x = 0.75 * index_px[0] + 0.25 * index_pip[0]
                stable_y = 0.75 * index_px[1] + 0.25 * index_pip[1]

                raw_x = np.interp(stable_x, [MARGIN_X, CAM_W - MARGIN_X], [0, SCREEN_W])
                raw_y = np.interp(stable_y, [MARGIN_Y, CAM_H - MARGIN_Y], [0, SCREEN_H])

                smooth_x = filter_x.filter(t_current, raw_x)
                smooth_y = filter_y.filter(t_current, raw_y)
                smooth_x = max(0, min(SCREEN_W - 1, smooth_x))
                smooth_y = max(0, min(SCREEN_H - 1, smooth_y))

                # Magnetic Lock Trigger
                if not is_locked and not is_right_pinching:
                    if dist_thumb_index < PRE_LOCK_DIST:
                        is_locked = True
                        locked_screen_pos = (smooth_x, smooth_y)
                        locked_cam_pos = index_px
                        lock_start_time = t_current
                        has_clicked_in_lock = False

                if is_locked:
                    lock_duration = t_current - lock_start_time

                    if not is_dragging:
                        pyautogui.moveTo(locked_screen_pos[0], locked_screen_pos[1])
                        current_action_label = "[TARGET LOCKED] Ready to Click"
                        label_color = (0, 255, 255)

                    # Contact -> Trigger Click
                    if dist_thumb_index < PINCH_CLICK_DIST and not has_clicked_in_lock:
                        has_clicked_in_lock = True
                        if (t_current - last_click_time) < DOUBLE_CLICK_GAP:
                            pyautogui.doubleClick()
                            current_action_label = "Double Click!"
                            label_color = (255, 0, 255)
                            last_click_time = 0.0
                        else:
                            pyautogui.click()
                            current_action_label = "Click!"
                            label_color = (0, 255, 0)
                            last_click_time = t_current

                    # Drag & Drop detection
                    if has_clicked_in_lock and not is_dragging:
                        if lock_duration > DRAG_HOLD_DELAY and dist_thumb_index < PINCH_CLICK_DIST + 8:
                            is_dragging = True
                            pyautogui.mouseDown()
                            current_action_label = "Dragging Window / Item"
                            label_color = (255, 120, 0)

                    if is_dragging:
                        pyautogui.moveTo(smooth_x, smooth_y)
                        current_action_label = "Dragging Window / Item"
                        label_color = (255, 120, 0)

                    # Release Lock
                    if dist_thumb_index > RELEASE_DIST:
                        if is_dragging:
                            pyautogui.mouseUp()
                            is_dragging = False
                            current_action_label = "Dropped"
                        is_locked = False
                        has_clicked_in_lock = False

                else:
                    pyautogui.moveTo(smooth_x, smooth_y)
                    current_action_label = "Pointer Tracking"
                    label_color = (200, 200, 200)

                # Right Click (Thumb + Middle)
                if not is_locked and not is_dragging:
                    if not is_right_pinching:
                        if dist_thumb_middle < (32 * scale_ratio) and dist_thumb_index > (45 * scale_ratio):
                            is_right_pinching = True
                            right_pinch_start = t_current
                    else:
                        if dist_thumb_middle > (45 * scale_ratio):
                            is_right_pinching = False
                            if (t_current - right_pinch_start) < 0.45:
                                pyautogui.rightClick()
                                current_action_label = "Right Click"
                                label_color = (0, 100, 255)

                # Target Crosshair Visuals
                if is_locked:
                    cx, cy = locked_cam_pos
                    cv2.circle(frame, (cx, cy), 18, (0, 255, 255), 2)
                    cv2.line(frame, (cx - 24, cy), (cx + 24, cy), (0, 255, 255), 1)
                    cv2.line(frame, (cx, cy - 24), (cx, cy + 24), (0, 255, 255), 1)

                # Proximity Ring
                pinch_progress = max(0.0, min(1.0, (dist_thumb_index - PINCH_CLICK_DIST) / max(1, (PRE_LOCK_DIST - PINCH_CLICK_DIST))))
                ring_radius = int(8 + pinch_progress * 18)
                ring_color = (0, 255, 0) if dist_thumb_index < PINCH_CLICK_DIST else ((0, 255, 255) if is_locked else (255, 200, 0))
                mid_x = int((thumb_px[0] + index_px[0]) / 2)
                mid_y = int((thumb_px[1] + index_px[1]) / 2)
                cv2.circle(frame, (mid_x, mid_y), ring_radius, ring_color, 2)

        else:
            palm_history.clear()
            current_action_label = "STANDBY: SHOW HAND"
            label_color = (130, 130, 130)

        # ---------------------------------------------------------
        # 4. Sci-Fi Cybernetic Top HUD Overlay
        # ---------------------------------------------------------
        hud_h = 58
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (CAM_W, hud_h), (12, 16, 20), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Neon Tech Line
        cv2.line(frame, (0, hud_h), (CAM_W, hud_h), (0, 200, 255), 1)

        # Telemetry & Status
        cv2.putText(frame, f"JARVIS OS [{cam_name}]", (14, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.50, (0, 255, 255), 1)
        cv2.putText(frame, current_action_label, (230, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, label_color, 1)
        cv2.putText(frame, f"{int(fps)} FPS", (CAM_W - 90, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, (160, 160, 160), 1)

        cv2.imshow("Jarvis Ironman Touchless Pro - Press 'q' to exit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
