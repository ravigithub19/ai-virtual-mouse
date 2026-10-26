"""
Camera Management and Auto-Detection Utilities for AI Virtual Mouse.
Detects USB webcams, integrated webcams, and virtual cameras.
Prioritizes physical external USB webcams.
"""

import cv2
from typing import List, Dict, Any, Tuple, Optional


VIRTUAL_KEYWORDS = [
    'virtual', 'obs', 'ivcam', 'droidcam', 'iriun',
    'manycam', 'vcam', 'epoccam', 'splitcam', 'ndi', 'unity'
]

INTEGRATED_KEYWORDS = [
    'integrated', 'internal', 'built-in', 'builtin',
    'laptop', 'facetime', 'front camera', 'rear camera', 'câmera frontal'
]


def get_camera_devices() -> List[Dict[str, Any]]:
    """
    Detects all video capture devices on the system.
    Identifies external USB webcams vs integrated laptop cameras vs virtual cameras.
    Returns list of device dictionaries sorted by priority (USB webcams first).
    """
    device_names: List[str] = []

    # 1. Try pygrabber for accurate Windows DirectShow device names
    try:
        from pygrabber.dshow_graph import FilterGraph
        graph = FilterGraph()
        device_names = graph.get_input_devices()
    except Exception:
        device_names = []

    # 2. Fallback: probe OpenCV indices if pygrabber failed or found no devices
    if not device_names:
        for idx in range(6):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    device_names.append(f"Câmera de Vídeo {idx}")
                cap.release()
            else:
                break

    devices_info: List[Dict[str, Any]] = []

    for idx, name in enumerate(device_names):
        nl = name.lower()
        is_virt = any(k in nl for k in VIRTUAL_KEYWORDS)
        is_integ = any(k in nl for k in INTEGRATED_KEYWORDS)
        is_usb_ext = (not is_virt) and (not is_integ)

        if is_usb_ext:
            score = 100
            label = f"{name} (USB Externa)"
        elif is_integ:
            score = 50
            label = f"{name} (Integrada)"
        elif is_virt:
            score = 10
            label = f"{name} (Virtual)"
        else:
            score = 40
            label = f"{name}"

        devices_info.append({
            "index": idx,
            "name": name,
            "label": label,
            "score": score,
            "is_usb_external": is_usb_ext,
            "is_integrated": is_integ,
            "is_virtual": is_virt
        })

    # Sort so that highest score (external USB webcam) is first
    devices_info.sort(key=lambda d: d["score"], reverse=True)
    return devices_info


def get_default_camera_index() -> int:
    """
    Returns the camera index of the best physical USB webcam available.
    Falls back to 0 if no preferred camera is found.
    """
    cams = get_camera_devices()
    if cams:
        return cams[0]["index"]
    return 0


def get_default_camera_name() -> str:
    """
    Returns the friendly name of the preferred USB webcam.
    """
    cams = get_camera_devices()
    if cams:
        return cams[0]["name"]
    return "Câmera Padrão"


def open_camera(cam_index: int, cam_w: int = 640, cam_h: int = 480) -> Tuple[Optional[cv2.VideoCapture], str, int]:
    """
    Opens the camera at the given index using DirectShow on Windows.
    Sets preferred resolution and validates capture.
    Returns (cap, cam_name, cam_index).
    """
    cams = get_camera_devices()
    cam_name = f"Camera {cam_index}"
    for c in cams:
        if c["index"] == cam_index:
            cam_name = c["name"]
            break

    # DirectShow is optimal for USB webcams on Windows
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(cam_index)

    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)
        # Test read
        ret, _ = cap.read()
        if not ret:
            # If reading failed with CAP_DSHOW, try default backend
            cap.release()
            cap = cv2.VideoCapture(cam_index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

    return cap, cam_name, cam_index
