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
