"""
Universal Hand Tracker Module (Python 3.8 - 3.13+)
Provides high-performance hand landmark detection using MediaPipe Tasks API
with automatic fallback to legacy MediaPipe Solutions API if available.
"""

import os
import cv2
import numpy as np
import mediapipe as mp
import urllib.request
import math
from typing import List, Optional, Tuple


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),        # Indicador
    (5, 9), (9, 10), (10, 11), (11, 12),    # Médio
    (9, 13), (13, 14), (14, 15), (15, 16), # Anelar
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17) # Mínimo e palma
]


class NormalizedLandmark:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x: float, y: float, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class SingleHandLandmarks:
    def __init__(self, landmark_list: List[NormalizedLandmark]):
        self.landmark = landmark_list

    def __getitem__(self, idx: int) -> NormalizedLandmark:
        return self.landmark[idx]

    def __len__(self) -> int:
        return len(self.landmark)


class HandDetectionResults:
    def __init__(self, multi_hand_landmarks: Optional[List[SingleHandLandmarks]] = None):
        self.multi_hand_landmarks = multi_hand_landmarks or []


class UniversalHandsDetector:
    """
    Unified Hand Landmarker compatible with both MediaPipe Tasks (Python 3.13+)
    and legacy MediaPipe Solutions (Python 3.8 - 3.12).
    """
    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.65,
        min_tracking_confidence: float = 0.65,
        model_path: str = "hand_landmarker.task"
    ):
        self.max_hands = max_num_hands
        self.use_legacy = False
        self.legacy_detector = None
        self.tasks_detector = None

        # Check for legacy MediaPipe solutions API
        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            try:
                self.legacy_detector = mp.solutions.hands.Hands(
                    max_num_hands=max_num_hands,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence
                )
                self.use_legacy = True
                return
            except Exception:
                pass

        # Use Tasks API
        if not os.path.exists(model_path):
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, model_path)

        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.tasks_detector = vision.HandLandmarker.create_from_options(options)

    def process(self, rgb_frame: np.ndarray) -> HandDetectionResults:
        """
        Detects hand landmarks in an RGB frame.
        Returns a result object with .multi_hand_landmarks attribute.
        """
        if self.use_legacy and self.legacy_detector:
            return self.legacy_detector.process(rgb_frame)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection = self.tasks_detector.detect(mp_image)

        if not detection.hand_landmarks:
            return HandDetectionResults([])

        hands_list = []
        for raw_hand in detection.hand_landmarks:
            lms = [NormalizedLandmark(lm.x, lm.y, getattr(lm, 'z', 0.0)) for lm in raw_hand]
            hands_list.append(SingleHandLandmarks(lms))

        return HandDetectionResults(hands_list)


def draw_hand_skeleton(frame: np.ndarray, hand_landmarks: SingleHandLandmarks, width: int = 640, height: int = 480):
    """Draws clean connecting lines and landmark dots on an image."""
    lms = hand_landmarks.landmark
    for p1_idx, p2_idx in HAND_CONNECTIONS:
        pt1 = (int(lms[p1_idx].x * width), int(lms[p1_idx].y * height))
        pt2 = (int(lms[p2_idx].x * width), int(lms[p2_idx].y * height))
        cv2.line(frame, pt1, pt2, (100, 100, 100), 1)

    for lm in lms:
        cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 2, (60, 60, 60), -1)


def check_black_wristband(frame: np.ndarray, landmarks, cam_w: int, cam_h: int) -> Tuple[bool, Tuple[int, int], int, float]:
    """
    Checks if a black wristband/bracelet is present near the wrist.
    Returns:
        is_authorized (bool): True if black bracelet is detected.
        center_pt (tuple): (x, y) coordinates of the wristband zone.
        radius (int): radius of the detection circle.
        black_ratio (float): percentage of dark pixels detected.
    """
    wrist_x = int(landmarks[0].x * cam_w)
    wrist_y = int(landmarks[0].y * cam_h)
    middle_mcp_x = int(landmarks[9].x * cam_w)
    middle_mcp_y = int(landmarks[9].y * cam_h)

    hand_scale = max(40.0, math.hypot(wrist_x - middle_mcp_x, wrist_y - middle_mcp_y))

    # Vector from middle knuckle towards wrist (along forearm direction)
    dir_x = wrist_x - middle_mcp_x
    dir_y = wrist_y - middle_mcp_y
    norm = math.hypot(dir_x, dir_y)
    if norm > 1e-3:
        ux, uy = dir_x / norm, dir_y / norm
    else:
        ux, uy = 0.0, 1.0

    # Inspection zone centered slightly down the wrist/forearm
    zone_x = int(wrist_x + ux * (0.16 * hand_scale))
    zone_y = int(wrist_y + uy * (0.16 * hand_scale))
    radius = int(max(16, 0.30 * hand_scale))

    x1 = max(0, zone_x - radius)
    x2 = min(cam_w, zone_x + radius)
    y1 = max(0, zone_y - radius)
    y2 = min(cam_h, zone_y + radius)

    if (x2 - x1) < 8 or (y2 - y1) < 8:
        return False, (wrist_x, wrist_y), radius, 0.0

    roi_bgr = frame[y1:y2, x1:x2]
    roi_hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    yy, xx = np.ogrid[:y2 - y1, :x2 - x1]
    center_roi_x = zone_x - x1
    center_roi_y = zone_y - y1
    circle_mask = ((xx - center_roi_x) ** 2 + (yy - center_roi_y) ** 2) <= (radius ** 2)

    total_circle_pixels = int(np.sum(circle_mask))
    if total_circle_pixels < 20:
        return False, (zone_x, zone_y), radius, 0.0

    # Sample palm brightness for adaptive ambient lighting comparison
    palm_x = int((wrist_x + middle_mcp_x) / 2)
    palm_y = int((wrist_y + middle_mcp_y) / 2)
    px1 = max(0, palm_x - 8)
    px2 = min(cam_w, palm_x + 8)
    py1 = max(0, palm_y - 8)
    py2 = min(cam_h, palm_y + 8)

    if (px2 - px1) > 4 and (py2 - py1) > 4:
        palm_hsv = cv2.cvtColor(frame[py1:py2, px1:px2], cv2.COLOR_BGR2HSV)
        palm_val = float(np.mean(palm_hsv[:, :, 2]))
    else:
        palm_val = 140.0

    # Dynamic threshold: black wristband is significantly darker than skin
    black_thresh_v = min(85.0, max(45.0, palm_val * 0.58))

    val_channel = roi_hsv[:, :, 2]
    dark_pixels = (val_channel < black_thresh_v) & circle_mask
    black_count = int(np.sum(dark_pixels))
    black_ratio = black_count / float(total_circle_pixels)

    # Authorized if at least 10% of pixels in wrist zone are dark and count >= 20
    is_authorized = (black_ratio >= 0.10 and black_count >= 20)

    return is_authorized, (zone_x, zone_y), radius, black_ratio


def draw_wristband_badge(frame: np.ndarray, center_pt: Tuple[int, int], radius: int, is_authorized: bool, black_ratio: float, angle_deg: Optional[float] = None):
    """Draws a security authorization badge at the wrist."""
    cx, cy = center_pt
    color = (0, 255, 120) if is_authorized else (0, 40, 255)

    cv2.circle(frame, (cx, cy), radius, color, 2)
    if angle_deg is not None:
        for i in range(4):
            theta = math.radians(angle_deg * 2 + i * 90)
            tx = int(cx + (radius + 5) * math.cos(theta))
            ty = int(cy + (radius + 5) * math.sin(theta))
            cv2.line(frame, (cx, cy), (tx, ty), color, 1)

    if is_authorized:
        inner_r = int(radius * 0.6) if angle_deg is not None else int(radius * 0.5)
        cv2.circle(frame, (cx, cy), inner_r, (0, 255, 200), 1)
        tag = f"LIBERADA [OK {int(black_ratio * 100)}%]" if angle_deg is not None else f"LIBERADA ({int(black_ratio * 100)}%)"
        tag_offset = 55 if angle_deg is not None else 45
        cv2.putText(frame, tag, (cx - tag_offset, cy + radius + 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 255, 120), 1)
    else:
        cv2.line(frame, (cx - 6, cy - 6), (cx + 6, cy + 6), (0, 0, 255), 2)
        cv2.line(frame, (cx + 6, cy - 6), (cx - 6, cy + 6), (0, 0, 255), 2)
        tag = "BLOQUEADA: SEM PULSEIRA"
        cv2.putText(frame, tag, (cx - 75, cy + radius + 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 50, 255), 1)

