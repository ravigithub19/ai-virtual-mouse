import cv2
import mediapipe as mp
import time
import math
import numpy as np

# Landmark connections for direct OpenCV drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)
]


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []
        self.raw_hands = []

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
            self.use_legacy = True
            self.mpHands = mp.solutions.hands
            self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.detectionCon, self.trackCon)
            self.mpDraw = mp.solutions.drawing_utils
        else:
            self.use_legacy = False
            from virtual_mouse_engine import UniversalHandTracker
            self.tracker = UniversalHandTracker(model_path="hand_landmarker.task", max_hands=self.maxHands)

    def findHands(self, img, draw=True):
        if self.use_legacy:
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.results = self.hands.process(imgRGB)
            if self.results.multi_hand_landmarks and draw:
                for handLms in self.results.multi_hand_landmarks:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
            return img

        # Universal Tracker (Tasks API / Python 3.13+)
        self.raw_hands = self.tracker.process_frame(img)
        if draw and self.raw_hands:
            h, w, _ = img.shape
            for hand in self.raw_hands:
                for pt1, pt2 in HAND_CONNECTIONS:
                    p1 = (int(hand[pt1][0] * w), int(hand[pt1][1] * h))
                    p2 = (int(hand[pt2][0] * w), int(hand[pt2][1] * h))
                    cv2.line(img, p1, p2, (100, 100, 100), 2)
                for pt in hand:
                    cv2.circle(img, (int(pt[0] * w), int(pt[1] * h)), 4, (255, 0, 255), cv2.FILLED)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []

        if self.use_legacy:
            if hasattr(self, 'results') and self.results.multi_hand_landmarks:
                if handNo < len(self.results.multi_hand_landmarks):
                    myHand = self.results.multi_hand_landmarks[handNo]
                    h, w, c = img.shape
                    for id, lm in enumerate(myHand.landmark):
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        xList.append(cx)
                        yList.append(cy)
                        self.lmList.append([id, cx, cy])
                        if draw:
                            cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                    xmin, xmax = min(xList), max(xList)
                    ymin, ymax = min(yList), max(yList)
                    bbox = xmin, ymin, xmax, ymax

                    if draw:
                        cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)
            return self.lmList, bbox

        # Tasks API
        if self.raw_hands and handNo < len(self.raw_hands):
            myHand = self.raw_hands[handNo]
            h, w, c = img.shape
            for id, pt in enumerate(myHand):
                cx, cy = int(pt[0] * w), int(pt[1] * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            if xList and yList:
                xmin, xmax = min(xList), max(xList)
                ymin, ymax = min(yList), max(yList)
                bbox = xmin, ymin, xmax, ymax
                if draw:
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        if not self.lmList:
            return [0, 0, 0, 0, 0]
        # Thumb
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # Fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    from camera_utils import open_camera, get_default_camera_index
    pTime = 0
    cap, cam_name, cam_idx = open_camera(get_default_camera_index(), 640, 480)
    print(f"HandTrackingModule utilizando: {cam_name} (Índice {cam_idx})")
    detector = handDetector()
    while True:
        success, img = cap.read()
        if not success:
            break
        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if len(lmList) != 0:
            print("Polegar:", lmList[4])
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 30
        pTime = cTime
        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
