# VirtualPainter.py
import cv2
import numpy as np
import os
import time
import HandTrackingModule as htm
from tkinter import *
from PIL import Image, ImageTk  # Needed for handling the icon image

# Create a hidden tkinter window for the icon
root = Tk()
root.withdraw()  # Hide the main tkinter window

# Set the taskbar icon
try:
    img = PhotoImage(file='C:\\Users\\s\\PycharmProjects\\btb\\icon\\icons.png')
    root.iconphoto(False, img)
except Exception as e:
    print(f"Could not set icon: {e}")

# Variables
brushSize = 10  # Reduced brush size for smoother drawing
eraserSize = 50
fps = 60
time_per_frame = 2.0 / fps

folderPath = 'header'
myList = sorted(os.listdir(folderPath))  # Sort the list to maintain order
overlayList = [cv2.imread(f"{folderPath}/{imPath}") for imPath in myList]

folderPath = 'guide'
myList = sorted(os.listdir(folderPath))  # Sort the list to maintain order
overlayLists = [cv2.imread(f"{folderPath}/{imPath}") for imPath in myList]

# Set the first image as the header
header = overlayList[0]
guide = overlayLists[0]

# Default drawing color
drawColor = (255, 0, 255)

# Set up the camera
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)  # Height

# Assigning Detector
detector = htm.handDetector(detectionCon=0.85)

# Previous points
xp, yp = 0, 0

# Create Image Canvas
imgCanvas = np.zeros((720, 1280, 3), np.uint8)

# Undo/Redo Stack
undoStack = []
redoStack = []


# Function to show transient notification
def show_transient_notification(message, duration=1000):
    notification = Toplevel(root)
    notification.wm_overrideredirect(True)  # Remove window decorations
    notification.wm_geometry("+%d+%d" % (root.winfo_screenwidth() // 2 - 100, root.winfo_screenheight() // 2 - 50))

    Label(notification, text=message, font=('Helvetica', 12), bg='lightyellow', padx=20, pady=10).pack()

    # Make the window disappear after duration milliseconds
    notification.after(duration, notification.destroy)


# Function to save the canvas
def save_canvas():
    save_path = os.path.join(os.path.expanduser("~"), "Pictures", "saved_painting.png")
    cv2.imwrite(save_path, imgCanvas)
    print(f"Canvas Saved at {save_path}")
    show_transient_notification(f"Saved to:\n{save_path}")


# Function to interpolate points
def interpolate_points(x1, y1, x2, y2, num_points=10):
    points = []
    for i in range(num_points):
        x = int(x1 + (x2 - x1) * (i / num_points))
        y = int(y1 + (y2 - y1) * (i / num_points))
        points.append((x, y))
    return points


# Main Loop
while True:
    start_time = time.time()

    # 1. Import Image
    success, img = cap.read()
    img = cv2.flip(img, 1)

    # 2. Find Hand Landmarks
    img = detector.findHands(img, draw=False)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        # Tip of index and middle fingers
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        # 3. Check which fingers are up
        fingers = detector.fingersUp()

        # 4. Selection Mode - Two Fingers Up
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0  # Reset points

            # Detecting selection based on X coordinate
            if y1 < 125:  # Ensure the selection is within the header area
                if 0 < x1 < 128:  # Save
                    header = overlayList[1]
                    save_canvas()

                elif 128 < x1 < 256:  # Pink
                    header = overlayList[2]
                    drawColor = (255, 0, 255)  # Pink
                    show_transient_notification("Pink brush selected")

                elif 256 < x1 < 384:  # Blue
                    header = overlayList[3]
                    drawColor = (255, 0, 0)  # Blue
                    show_transient_notification("Blue brush selected")

                elif 384 < x1 < 512:  # Green
                    header = overlayList[4]
                    drawColor = (0, 255, 0)  # Green
                    show_transient_notification("Green brush selected")

                elif 512 < x1 < 640:  # Yellow
                    header = overlayList[5]
                    drawColor = (0, 255, 255)  # Yellow
                    show_transient_notification("Yellow brush selected")

                elif 640 < x1 < 768:  # Eraser
                    header = overlayList[6]
                    drawColor = (0, 0, 0)  # Eraser
                    show_transient_notification("Eraser selected")

                elif 768 < x1 < 896:  # Undo
                    header = overlayList[7]
                    if len(undoStack) > 0:
                        redoStack.append(imgCanvas.copy())
                        imgCanvas = undoStack.pop()
                        show_transient_notification("Undo")
                    else:
                        show_transient_notification("Nothing to undo")

                elif 896 < x1 < 1024:  # Redo
                    header = overlayList[8]
                    if len(redoStack) > 0:
                        undoStack.append(imgCanvas.copy())
                        imgCanvas = redoStack.pop()
                        show_transient_notification("Redo")
                    else:
                        show_transient_notification("Nothing to redo")

                elif 1024 < x1 < 1152:  # Guide
                    header = overlayList[9]
                    show_transient_notification("Guide selected")

            # Show selection rectangle
            cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)

        # 5. Drawing Mode - Index Finger Up
        if fingers[1] and not fingers[2]:
            cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)

            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            # Interpolate points for smoother drawing
            points = interpolate_points(xp, yp, x1, y1)
            for point in points:
                if drawColor == (0, 0, 0):  # Eraser Mode
                    cv2.line(img, (xp, yp), point, drawColor, eraserSize)
                    cv2.line(imgCanvas, (xp, yp), point, drawColor, eraserSize)
                else:
                    cv2.line(img, (xp, yp), point, drawColor, brushSize)
                    cv2.line(imgCanvas, (xp, yp), point, drawColor, brushSize)
                xp, yp = point

            # Push the current state to the undo stack after drawing
            undoStack.append(imgCanvas.copy())
            redoStack.clear()  # Clear redo stack after a new action

        else:
            # No fingers up - reset points
            xp, yp = 0, 0



    # 7. Convert Canvas to Grayscale and Invert
    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, imgCanvas)

    # 8. Set Header Image
    img[0:125, 0:1280] = header

    # 9. Display the images
    cv2.imshow("Beyond The Brush", img)
    cv2.imshow("Beyond The Brush Canvas", imgCanvas)

    # Maintain 60 FPS
    elapsed_time = time.time() - start_time
    if elapsed_time < time_per_frame:
        time.sleep(time_per_frame - elapsed_time)

    # Process Tkinter events
    root.update()

    # Exit condition
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()