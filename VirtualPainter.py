import cv2
import numpy as np
import os
import time
import HandTrackingModule as htm
from tkinter import *
from PIL import Image, ImageTk

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
brushSize = 10
eraserSize = 100
fps = 60
time_per_frame = 5.0 / fps

# Load header images
folderPath = 'header'
myList = sorted(os.listdir(folderPath))
overlayList = [cv2.imread(f"{folderPath}/{imPath}") for imPath in myList]

# Load guide images (resized to 1280x595)
folderPath = 'guide'
myList = sorted(os.listdir(folderPath))
guideList = []
for imPath in myList:
    img = cv2.imread(f"{folderPath}/{imPath}")
    if img is not None:
        # Resize guide images to fit below header (1280x595)
        img = cv2.resize(img, (1280, 595))
        guideList.append(img)

# Default images
header = overlayList[0]
current_guide_index = 0  # Track current guide index
current_guide = None  # Initially no guide shown
show_guide = False  # Track guide visibility state

# Swipe detection variables
swipe_threshold = 50  # Minimum horizontal movement to consider a swipe
swipe_start_x = None  # To track where swipe started
swipe_active = False  # To track if swipe is in progress

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
    notification.wm_overrideredirect(True)
    notification.wm_geometry("+%d+%d" % (root.winfo_screenwidth() // 2 - 100, root.winfo_screenheight() // 2 - 50))
    Label(notification, text=message, font=('Helvetica', 12), bg='lightyellow', padx=20, pady=10).pack()
    notification.after(duration, notification.destroy)


# Function to save the canvas
def save_canvas():
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(os.path.expanduser("~"), "Pictures", f"saved_painting_{timestamp}.png")
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


# Improved notification function
def show_transient_notification(message, duration=1000, is_error=False):
    notification = Toplevel(root)
    notification.wm_overrideredirect(True)

    # Calculate position to be centered on screen (not just drawing area)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Notification will be 250px wide and auto-height
    notif_width = 250
    notification.wm_geometry(f"+{(screen_width - notif_width) // 2}+{(screen_height - 100) // 2}")

    # Style based on message type
    bg_color = 'lightyellow'
    if is_error:
        bg_color = '#ffdddd'  # light red for errors
    elif "selected" in message.lower():
        bg_color = '#ddffdd'  # light green for selections

    # Create frame for better centering control
    frame = Frame(notification, bg=bg_color, padx=10, pady=10)
    frame.pack(expand=True, fill=BOTH)

    # Create notification label with improved centering
    label = Label(
        frame,
        text=message,
        font=('Helvetica', 12, 'bold'),
        bg=bg_color,
        fg='#333333',
        padx=10,
        pady=10,
        wraplength=notif_width - 40,  # Account for padding
        justify=CENTER,
        anchor=CENTER  # This ensures text is centered within the label
    )
    label.pack(expand=True, fill=BOTH)

    # Add a subtle border
    notification.config(bd=1, relief='solid')

    # Auto-destroy after duration
    notification.after(duration, notification.destroy)


# Main Loop
while True:
    start_time = time.time()

    # 1. Import Image
    success, img = cap.read()
    img = cv2.flip(img, 1)

    # 2. Find Hand Landmarks
    img = detector.findHands(img, draw=False)
    lmList = detector.findPosition(img, draw=False)
    # Draw black outline (thicker)
    cv2.putText(img, "Selection Mode - Two Fingers Up", (50, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)  # Black with thickness 4

    # Draw main white text (thinner)
    cv2.putText(img, "Selection Mode - Two Fingers Up", (50, 150),
    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # White with thickness 2

    if len(lmList) != 0:
        # Tip of index and middle fingers
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        # 3. Check which fingers are up
        fingers = detector.fingersUp()

        # 4. Selection Mode - Two Fingers Up
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0  # Reset points
            swipe_start_x = None  # Reset swipe tracking when in selection mode



            # Detecting selection based on X coordinate
            if y1 < 125:  # Ensure the selection is within the header area
                if 0 < x1 < 128:  # Save
                    header = overlayList[1]
                    save_canvas()
                    show_guide = False

                elif 128 < x1 < 256:  # Pink
                    header = overlayList[2]
                    drawColor = (255, 0, 255)  # Pink
                    show_transient_notification("Pink brush selected")
                    show_guide = False

                elif 256 < x1 < 384:  # Blue
                    header = overlayList[3]
                    drawColor = (255, 0, 0)  # Blue
                    show_transient_notification("Blue brush selected")
                    show_guide = False

                elif 384 < x1 < 512:  # Green
                    header = overlayList[4]
                    drawColor = (0, 255, 0)  # Green
                    show_transient_notification("Green brush selected")
                    show_guide = False

                elif 512 < x1 < 640:  # Yellow
                    header = overlayList[5]
                    drawColor = (0, 255, 255)  # Yellow
                    show_transient_notification("Yellow brush selected")
                    show_guide = False

                elif 640 < x1 < 768:  # Eraser
                    header = overlayList[6]
                    drawColor = (0, 0, 0)  # Eraser
                    show_transient_notification("Eraser selected")
                    show_guide = False

                elif 768 < x1 < 896:  # Undo
                    header = overlayList[7]
                    if len(undoStack) > 0:
                        redoStack.append(imgCanvas.copy())
                        imgCanvas = undoStack.pop()
                        show_transient_notification("Undo")
                    else:
                        show_transient_notification("Nothing to undo")
                    show_guide = False

                elif 896 < x1 < 1024:  # Redo
                    header = overlayList[8]
                    if len(redoStack) > 0:
                        undoStack.append(imgCanvas.copy())
                        imgCanvas = redoStack.pop()
                        show_transient_notification("Redo")
                    else:
                        show_transient_notification("Nothing to redo")
                    show_guide = False

                elif 1024 < x1 < 1152:  # Guide
                    header = overlayList[9]
                    show_transient_notification("Guide selected")
                    # Toggle guide display
                    show_guide = True  # Always show guide when selected
                    current_guide_index = 0  # Reset to first guide
                    current_guide = guideList[current_guide_index]  # Show first guide image

                elif 1155 < x1 < 1280:
                    header = overlayList[10]
                    show_transient_notification("Please Select A Brush and Eraser Size")


            # Show selection rectangle
            cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)

        # 5. Guide Navigation Mode - Single Index Finger (only when guide is shown)
        elif fingers[1] and not fingers[2] and show_guide:
            if swipe_start_x is None:
                # Start tracking swipe
                swipe_start_x = x1
                swipe_active = True
            else:
                # Calculate horizontal movement
                delta_x = x1 - swipe_start_x

                # Check if swipe threshold is reached
                if abs(delta_x) > swipe_threshold and swipe_active:
                    if delta_x > 0:
                        # Swipe right - previous guide
                        current_guide_index = max(0, current_guide_index - 1)
                        show_transient_notification(f"Guide {current_guide_index + 1}/{len(guideList)}")
                    else:
                        # Swipe left - next guide
                        current_guide_index = min(len(guideList) - 1, current_guide_index + 1)
                        show_transient_notification(f"Guide {current_guide_index + 1}/{len(guideList)}")

                    # Update current guide
                    current_guide = guideList[current_guide_index]
                    swipe_active = False  # Prevent multiple triggers

            # Show index finger position (visual feedback)
            cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)

        # 6. Drawing Mode - Index Finger Up (only if guide is not shown)
        elif fingers[1] and not fingers[2] and not show_guide:
            swipe_start_x = None  # Reset swipe tracking when drawing
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
            # No fingers up - reset points and swipe tracking
            xp, yp = 0, 0
            swipe_start_x = None
            swipe_active = False
    else:
        # No hands detected - reset swipe tracking
        swipe_start_x = None
        swipe_active = False

    # 7. Convert Canvas to Grayscale and Invert
    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, imgCanvas)

    # 8. Set Header Image
    img[0:125, 0:1280] = header

    # 9. Display Guide Image if active
    if show_guide and current_guide is not None:
        # Create a composite image that preserves the drawing canvas
        guide_area = img[125:720, 0:1280].copy()
        # Blend the guide with the current camera feed (50% opacity)
        blended_guide = cv2.addWeighted(current_guide, 0.3, guide_area, 0.3, 0)
        # Put the blended guide back
        img[125:720, 0:1280] = blended_guide

        # Display guide navigation instructions
        cv2.putText(img, "", (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Guide {current_guide_index + 1}/{len(guideList)}", (1100, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # 10. Display the image
    cv2.imshow("Beyond The Brush", img)

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