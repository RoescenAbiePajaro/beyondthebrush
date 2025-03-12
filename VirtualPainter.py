import cv2
import numpy as np
import time
import os
import handtrackingmodule as ht

folderPath = "header"
mylist = os.listdir(folderPath)
print(mylist)
overlayList = []

for imPath in mylist:
    image = cv2.imread(f'{folderPath}/{imPath}')
    image = cv2.resize(image, (1280, 120))  # Resize header width to match video feed
    overlayList.append(image)

print(len(overlayList))
header = overlayList[0]

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

detector = ht.handDetector(detectionCon=0.75)

while True:

    # 1. Import Image
    success, img = cap.read()
    img = cv2.flip(img, 1)

    # 2.Find Hand landmarks
    img = detector.findHands(img)

    if not success:
        continue  # Skip frame if there's an issue

# Setting header_image
    img[0:120, 0:1280] = header  # Apply the resized header at the top

    cv2.imshow("Beyond The Brush", img)
    cv2.waitKey(1)
