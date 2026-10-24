import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
from camera_utils import get_default_camera_index, open_camera

######################
wCam, hCam = 640, 480
frameR = 100     # Frame Reduction
smoothening = 7  # Smoothing factor
######################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

# Connect to USB webcam automatically
cam_idx = get_default_camera_index()
cap, cam_name, cam_idx = open_camera(cam_idx, wCam, hCam)
print(f"[AI Virtual Mouse] Usando webcam USB: '{cam_name}' (Dispositivo {cam_idx})")

detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()

while True:
    # Step1: Find the landmarks
    success, img = cap.read()
    if not success or img is None:
        continue

    # Standardize frame size
    if img.shape[1] != wCam or img.shape[0] != hCam:
        img = cv2.resize(img, (wCam, hCam))

    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    # Step2: Get the tip of the index and middle finger
    if len(lmList) != 0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        # Step3: Check which fingers are up
        fingers = detector.fingersUp()
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                      (255, 0, 255), 2)

        # Step4: Only Index Finger: Moving Mode
        if fingers[1] == 1 and fingers[2] == 0:
            # Step5: Convert the coordinates
            x3 = np.interp(x1, (frameR, wCam-frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam-frameR), (0, hScr))

            # Step6: Smooth Values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            # Step7: Move Mouse
            target_x = max(0, min(int(wScr - clocX), int(wScr - 1)))
            target_y = max(0, min(int(clocY), int(hScr - 1)))
            autopy.mouse.move(target_x, target_y)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # Step8: Both Index and middle are up: Clicking Mode
        if fingers[1] == 1 and fingers[2] == 1:
            # Step9: Find distance between fingers
            length, img, lineInfo = detector.findDistance(8, 12, img)

            # Step10: Click mouse if distance short
            if length < 40:
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()

    # Step11: Frame rate
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 30
    pTime = cTime
    cv2.putText(img, f"FPS: {int(fps)}", (28, 58), cv2.FONT_HERSHEY_PLAIN, 2, (255, 8, 8), 2)

    # Step12: Display
    cv2.imshow("AI Virtual Mouse - Press q to exit", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
