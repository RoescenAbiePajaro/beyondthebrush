import cv2
import numpy as np


class ZoomManager:
    def __init__(self, min_zoom=0.5, max_zoom=3.0, initial_zoom=1.0):
        self.zoom_factor = initial_zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.is_zooming = False
        self.zoom_reference_distance = 0
        self.zoom_step = 0.1
        self.last_zoom_center = (0, 0)

    def handle_pinch_gesture(self, fingers, landmarks):
        """Handle zoom based on pinch gesture between thumb and index finger"""
        if fingers[0] and fingers[1] and not any(fingers[2:]):  # Only thumb and index finger up
            thumb_tip = landmarks[4][1:]
            index_tip = landmarks[8][1:]

            current_distance = np.sqrt((thumb_tip[0] - index_tip[0]) ** 2 +
                                       (thumb_tip[1] - index_tip[1]) ** 2)

            if not self.is_zooming:
                self.zoom_reference_distance = current_distance
                self.is_zooming = True
                self.last_zoom_center = ((thumb_tip[0] + index_tip[0]) // 2,
                                         (thumb_tip[1] + index_tip[1]) // 2)
            else:
                zoom_change = current_distance / self.zoom_reference_distance
                self.zoom_factor *= zoom_change
                self.zoom_factor = np.clip(self.zoom_factor, self.min_zoom, self.max_zoom)
                self.zoom_reference_distance = current_distance
                return True, self.last_zoom_center
        else:
            self.is_zooming = False

        return False, self.last_zoom_center

    def apply_zoom(self, image, center=None):
        """Apply zoom transformation to an image"""
        if self.zoom_factor == 1.0:
            return image.copy()

        h, w = image.shape[:2]
        if center is None:
            center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(center, 0, self.zoom_factor)
        return cv2.warpAffine(image, M, (w, h))

    def reset_zoom(self):
        """Reset zoom to default (1.0)"""
        self.zoom_factor = 1.0

    def zoom_in(self, step=None):
        """Programmatic zoom in"""
        step = step or self.zoom_step
        self.zoom_factor = min(self.zoom_factor + step, self.max_zoom)

    def zoom_out(self, step=None):
        """Programmatic zoom out"""
        step = step or self.zoom_step
        self.zoom_factor = max(self.zoom_factor - step, self.min_zoom)

    def get_zoom_level(self):
        """Get current zoom level"""
        return self.zoom_factor