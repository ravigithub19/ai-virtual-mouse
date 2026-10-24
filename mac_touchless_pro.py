"""
MacBook-Tier Touchless Mouse System (Apple Vision Pro & macOS Trackpad Experience)
=================================================================================
V2 UPGRADE - MAGNETIC TARGET LOCK (ANTI-SLIP CLICKING):
- Pre-Pinch Magnetic Lock: The millisecond you start closing your thumb to click,
  the cursor locks onto the target position. ZERO drift or slipping on impact!
- Immediate Tactile Click: Triggers click the instant fingers touch, with double-click support.
- Hold for Drag & Drop: Keep pinched for > 0.30s to drag items/windows, open fingers to drop.
- Scale-Adaptive Thresholds: Normalizes pinch distance against hand size.
- 1€ (One Euro) Filter: Eliminates hand tremor with zero lag at high speed.
- Two-Finger MacBook Scroll: Natural inertial page scrolling.
"""

import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import math
import time

# Disable pyautogui safety delays for instantaneous response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

# ---------------------------------------------------------
# 1. One Euro Filter for Butter-Smooth, Jitter-Free Motion
# ---------------------------------------------------------
class OneEuroFilter:
    def __init__(self, t0, x0, dx0=0.0, min_cutoff=1.0, beta=0.02, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)  # Lower = smoother at rest
        self.beta = float(beta)              # Higher = faster response at speed
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

        # Estimate derivative of the input
        a_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self._exp_smoothing(a_d, dx, self.dx_prev)

        # Dynamic cutoff frequency based on movement speed
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._smoothing_factor(t_e, cutoff)
        x_hat = self._exp_smoothing(a, x, self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat


from camera_utils import open_camera, get_default_camera_index


def get_usb_camera_cap(cam_w=640, cam_h=480):
    """
    Detects physical USB cameras on the system and prioritizes external USB webcams.
    Returns (cap, cam_name, cam_idx).
    """
    idx = get_default_camera_index()
    return open_camera(idx, cam_w, cam_h)



# ---------------------------------------------------------
# 2. Main Touchless Controller
# ---------------------------------------------------------
def main():
    CAM_W, CAM_H = 640, 480
    cap, cam_name, cam_idx = get_usb_camera_cap(CAM_W, CAM_H)

    if not cap.isOpened():
        print(f"Erro: Nao foi possivel acessar a camera USB '{cam_name}' (Indice {cam_idx}).")
        return

    # Screen dimensions
    SCREEN_W, SCREEN_H = pyautogui.size()

    # Active interaction box (margins inside camera frame)
    # Allows reaching screen corners without awkward arm stretching
    MARGIN_X = 110
    MARGIN_Y = 90

    # MediaPipe Hands (Compatible with Python 3.8 - 3.13 Tasks & Solutions API)
    from tracker_utils import UniversalHandsDetector, draw_hand_skeleton
    hands = UniversalHandsDetector(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    # Filters for X and Y coordinates
    t_now = time.time()
    filter_x = OneEuroFilter(t_now, SCREEN_W / 2, min_cutoff=0.9, beta=0.022)
    filter_y = OneEuroFilter(t_now, SCREEN_H / 2, min_cutoff=0.9, beta=0.022)

    # State Machine Variables (Magnetic Lock & Anti-Slip)
    is_locked = False
    locked_screen_pos = (SCREEN_W / 2, SCREEN_H / 2)
    locked_cam_pos = (CAM_W // 2, CAM_H // 2)
    has_clicked_in_lock = False
    is_dragging = False
    lock_start_time = 0.0
    last_click_time = 0.0

    DRAG_HOLD_DELAY = 0.32     # Seconds held before transitioning to Drag & Drop
    DOUBLE_CLICK_GAP = 0.40    # Gap between clicks for double-click

    # Right Click state
    is_right_pinching = False
    right_pinch_start = 0.0

    # Scroll state
    is_scrolling = False
    prev_scroll_y = None

    # UI Feedback
    current_action_label = "Pointer Tracking"
    label_color = (255, 255, 255)
    fps_time = time.time()
    fps = 30.0

    print("\n" + "="*60)
    print(" MACBOOK TOUCHLESS PRO V2 (TRAVA MAGNETICA ANTI-DESVIO)")
    print("="*60)
    print(" - Mover Cursor: Aponte com o dedo indicador naturalmente")
    print(" - Trava Magnetica: Ao comecar a fechar a pinca, o cursor")
    print("   CONGELA no botao para nunca errar o clique!")
    print(" - Clique: Junte o polegar e indicador (pinca firme)")
    print(" - Clique Duplo: Dois toques rapidos")
    print(" - Arrastar e Soltar (Drag & Drop): Aperte a pinca e segure")
    print(" - Clique Direito: Pinca de Polegar + Dedo Medio")
    print(" - Rolagem (Scroll): Levante Indicador + Medio juntos")
    print(" - Sair: Pressione 'q' na janela da camera")
    print("="*60 + "\n")

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        if frame.shape[1] != CAM_W or frame.shape[0] != CAM_H:
            frame = cv2.resize(frame, (CAM_W, CAM_H), interpolation=cv2.INTER_LINEAR)

        # Mirror image for intuitive control
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        t_current = time.time()

        # Calculate FPS
        dt_fps = t_current - fps_time
        if dt_fps > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt_fps)
        fps_time = t_current

        results = hands.process(rgb_frame)

        # Draw Active Tracking Zone guide
        cv2.rectangle(frame, (MARGIN_X, MARGIN_Y), (CAM_W - MARGIN_X, CAM_H - MARGIN_Y),
                      (60, 60, 60), 1)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            landmarks = hand_landmarks.landmark

            def get_px(idx):
                return int(landmarks[idx].x * CAM_W), int(landmarks[idx].y * CAM_H)

            wrist_px = get_px(0)
            thumb_px = get_px(4)        # Thumb Tip
            index_px = get_px(8)        # Index Tip
            middle_px = get_px(12)      # Middle Tip
            ring_px = get_px(16)        # Ring Tip
            pinky_px = get_px(20)       # Pinky Tip

            index_pip = get_px(6)       # Index Knuckle PIP
            middle_pip = get_px(10)     # Middle Knuckle PIP
            ring_pip = get_px(14)       # Ring Knuckle PIP
            pinky_pip = get_px(18)      # Pinky Knuckle PIP

            # Finger extension checks
            index_up = index_px[1] < index_pip[1]
            middle_up = middle_px[1] < middle_pip[1]
            ring_up = ring_px[1] < ring_pip[1]
            pinky_up = pinky_px[1] < pinky_pip[1]

            # Hand scale normalization (Wrist to Middle Knuckle)
            hand_scale = max(60, math.hypot(wrist_px[0] - middle_pip[0], wrist_px[1] - middle_pip[1]))

            # Distances
            dist_thumb_index = math.hypot(thumb_px[0] - index_px[0], thumb_px[1] - index_px[1])
            dist_thumb_middle = math.hypot(thumb_px[0] - middle_px[0], thumb_px[1] - middle_px[1])

            # Adaptive dynamic thresholds based on hand distance to camera
            # scale ~ 120 -> pre_lock ~ 54, click ~ 34, release ~ 58
            scale_ratio = hand_scale / 120.0
            PRE_LOCK_DIST = int(52 * scale_ratio)       # Freeze cursor early so hand motion doesn't slip!
            PINCH_CLICK_DIST = int(34 * scale_ratio)    # Contact point for click
            RELEASE_DIST = int(58 * scale_ratio)        # Unfreeze distance

            # -------------------------------------------------------------
            # GESTURE 1: MacBook Two-Finger Scroll
            # -------------------------------------------------------------
            two_finger_mode = index_up and middle_up and not ring_up and not pinky_up and dist_thumb_index > (55 * scale_ratio)

            if two_finger_mode:
                is_scrolling = True
                avg_y = (index_px[1] + middle_px[1]) / 2.0

                if prev_scroll_y is not None:
                    dy = avg_y - prev_scroll_y
                    if abs(dy) > 1.5:
                        scroll_amount = -int(dy * 15)
                        pyautogui.scroll(scroll_amount)

                prev_scroll_y = avg_y
                current_action_label = "MacBook Two-Finger Scroll"
                label_color = (0, 215, 255)

                cv2.line(frame, index_px, middle_px, (0, 215, 255), 3)

            else:
                is_scrolling = False
                prev_scroll_y = None

                # ---------------------------------------------------------
                # GESTURE 2: Pointer Tracking (Stabilized Anchor)
                # ---------------------------------------------------------
                # Use a blended coordinate (75% tip, 25% knuckle) for higher mechanical stability
                stable_x = 0.75 * index_px[0] + 0.25 * index_pip[0]
                stable_y = 0.75 * index_px[1] + 0.25 * index_pip[1]

                raw_x = np.interp(stable_x, [MARGIN_X, CAM_W - MARGIN_X], [0, SCREEN_W])
                raw_y = np.interp(stable_y, [MARGIN_Y, CAM_H - MARGIN_Y], [0, SCREEN_H])

                smooth_x = filter_x.filter(t_current, raw_x)
                smooth_y = filter_y.filter(t_current, raw_y)
                smooth_x = max(0, min(SCREEN_W - 1, smooth_x))
                smooth_y = max(0, min(SCREEN_H - 1, smooth_y))

                # ---------------------------------------------------------
                # GESTURE 3: Magnetic Target Lock & Anti-Slip Click
                # ---------------------------------------------------------
                # 1. Engage Target Lock when fingers start approaching
                if not is_locked and not is_right_pinching:
                    if dist_thumb_index < PRE_LOCK_DIST:
                        is_locked = True
                        locked_screen_pos = (smooth_x, smooth_y)
                        locked_cam_pos = index_px
                        lock_start_time = t_current
                        has_clicked_in_lock = False

                if is_locked:
                    lock_duration = t_current - lock_start_time

                    # A. While in lock, FREEZE the cursor on the target!
                    if not is_dragging:
                        pyautogui.moveTo(locked_screen_pos[0], locked_screen_pos[1])
                        current_action_label = "[TARGET LOCKED] Ready to Click"
                        label_color = (0, 255, 255)

                    # B. Contact reached -> Trigger Click!
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

                    # C. Check for Drag & Drop (Holding pinch past delay)
                    if has_clicked_in_lock and not is_dragging:
                        if lock_duration > DRAG_HOLD_DELAY and dist_thumb_index < PINCH_CLICK_DIST + 8:
                            is_dragging = True
                            pyautogui.mouseDown()
                            current_action_label = "Dragging Window / Item"
                            label_color = (255, 120, 0)

                    # D. If dragging: allow cursor to move with hand while holding mouseDown
                    if is_dragging:
                        pyautogui.moveTo(smooth_x, smooth_y)
                        current_action_label = "Dragging Window / Item"
                        label_color = (255, 120, 0)

                    # E. Check for Release / Lock Exit
                    if dist_thumb_index > RELEASE_DIST:
                        if is_dragging:
                            pyautogui.mouseUp()
                            is_dragging = False
                            current_action_label = "Dropped"
                        is_locked = False
                        has_clicked_in_lock = False

                else:
                    # Normal Cursor Tracking when not locked
                    pyautogui.moveTo(smooth_x, smooth_y)
                    current_action_label = "Pointer Tracking"
                    label_color = (200, 200, 200)

                # ---------------------------------------------------------
                # GESTURE 4: Right Click (Thumb + Middle Pinch)
                # ---------------------------------------------------------
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

                # ---------------------------------------------------------
                # Visual Reticle & Magnetic Lock Crosshair
                # ---------------------------------------------------------
                if is_locked:
                    # Draw Magnetic Lock Crosshair on target
                    cx, cy = locked_cam_pos
                    cv2.circle(frame, (cx, cy), 18, (0, 255, 255), 2)
                    cv2.line(frame, (cx - 24, cy), (cx + 24, cy), (0, 255, 255), 1)
                    cv2.line(frame, (cx, cy - 24), (cx, cy + 24), (0, 255, 255), 1)

                # Dynamic Halo that contracts as thumb closes in
                pinch_progress = max(0.0, min(1.0, (dist_thumb_index - PINCH_CLICK_DIST) / max(1, (PRE_LOCK_DIST - PINCH_CLICK_DIST))))
                ring_radius = int(8 + pinch_progress * 18)
                ring_color = (0, 255, 0) if dist_thumb_index < PINCH_CLICK_DIST else ((0, 255, 255) if is_locked else (255, 200, 0))

                mid_x = int((thumb_px[0] + index_px[0]) / 2)
                mid_y = int((thumb_px[1] + index_px[1]) / 2)

                cv2.line(frame, thumb_px, index_px, (160, 160, 160), 1)
                cv2.circle(frame, index_px, 6, (0, 255, 255), -1)
                cv2.circle(frame, thumb_px, 5, (255, 120, 0), -1)
                cv2.circle(frame, (mid_x, mid_y), ring_radius, ring_color, 2)

            # Draw subtle skeleton
            draw_hand_skeleton(frame, hand_landmarks, CAM_W, CAM_H)

        # ---------------------------------------------------------
        # Apple-Style Translucent Top HUD
        # ---------------------------------------------------------
        hud_h = 55
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (CAM_W, hud_h), (18, 18, 18), -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        # Status text
        cv2.putText(frame, "TOUCHLESS PRO V2", (18, 35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 1)
        cv2.putText(frame, current_action_label, (230, 35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.58, label_color, 1)
        cv2.putText(frame, f"{int(fps)} FPS", (CAM_W - 95, 35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (160, 160, 160), 1)

        cv2.imshow("MacBook Touchless Pro - Press 'q' to exit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
