# =============================================================
# RYVA Project — vision/camera.py
# Purpose : Camera capture + frame preprocessing
# Author  : RYVA Team
# Usage   : python vision/camera.py
# =============================================================

import cv2
import time


class RYVACamera:
    """
    Handles camera capture and frame preprocessing for the RYVA system.
    - Opens webcam or video source
    - Applies CLAHE histogram equalization for low-light cabin conditions
    - Provides clean BGR and RGB frames for downstream modules
    """

    def __init__(self, source=0, width=640, height=480):
        """
        Args:
            source : Camera index (0 = default webcam) or video file path
            width  : Frame width in pixels
            height : Frame height in pixels
        """
        self.source = source
        self.width = width
        self.height = height
        self.cap = None

        # CLAHE for histogram equalization (handles dark cabin lighting)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # FPS tracking
        self.prev_time = time.time()
        self.fps = 0

    # ----------------------------------------------------------
    # 1. Open Camera
    # ----------------------------------------------------------
    def open(self):
        """Opens the camera. Returns True if successful."""
        self.cap = cv2.VideoCapture(self.source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print("[ERROR] Could not open camera source:", self.source)
            return False

        print(f"[INFO] Camera opened — {self.width}x{self.height}")
        return True

    # ----------------------------------------------------------
    # 2. Read Raw Frame
    # ----------------------------------------------------------
    def get_frame(self):
        """
        Reads one raw frame from the camera.
        Returns:
            frame (BGR numpy array) or None if read fails
        """
        if self.cap is None or not self.cap.isOpened():
            print("[ERROR] Camera is not open. Call open() first.")
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("[WARNING] Failed to read frame.")
            return None

        return frame

    # ----------------------------------------------------------
    # 3. Preprocess Frame
    # ----------------------------------------------------------
    def preprocess(self, frame):
        """
        Preprocesses a raw frame for AI modules:
          1. Resize to target resolution
          2. CLAHE equalization on L channel (LAB color space)
             — improves visibility in dark/uneven cabin lighting
          3. Returns both BGR (for YOLO) and RGB (for MediaPipe)

        Args:
            frame : Raw BGR frame from get_frame()

        Returns:
            bgr_frame : Preprocessed BGR frame  → feed to YOLOv8
            rgb_frame : Preprocessed RGB frame  → feed to MediaPipe
        """
        # Step 1 — Resize
        frame = cv2.resize(frame, (self.width, self.height))

        # Step 2 — CLAHE on L channel (preserves color while fixing brightness)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        lab = cv2.merge((l, a, b))
        bgr_frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Step 3 — RGB copy for MediaPipe
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)

        return bgr_frame, rgb_frame

    # ----------------------------------------------------------
    # 4. FPS Calculator
    # ----------------------------------------------------------
    def get_fps(self):
        """Calculates and returns current FPS."""
        curr_time = time.time()
        self.fps = 1 / (curr_time - self.prev_time + 1e-6)
        self.prev_time = curr_time
        return round(self.fps, 1)

    # ----------------------------------------------------------
    # 5. Draw Debug Overlay
    # ----------------------------------------------------------
    def draw_overlay(self, frame, extra_text=""):
        """
        Draws FPS and status info on frame for debugging.
        Args:
            frame      : BGR frame to draw on
            extra_text : Optional status string (e.g. "PPE: OK")
        Returns:
            frame with overlay drawn
        """
        fps = self.get_fps()
        cv2.putText(frame, f"FPS: {fps}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if extra_text:
            cv2.putText(frame, extra_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        cv2.putText(frame, "RYVA Vision Module", (10, self.height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        return frame

    # ----------------------------------------------------------
    # 6. Release Camera
    # ----------------------------------------------------------
    def release(self):
        """Releases camera and closes all OpenCV windows."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released.")


# ==============================================================
# QUICK TEST — Run this file directly to verify camera works
# python vision/camera.py
# Press 'q' to quit
# ==============================================================

if __name__ == "__main__":

    cam = RYVACamera(source=0, width=640, height=480)

    if not cam.open():
        print("[ERROR] Exiting — camera could not be opened.")
        exit()

    print("[INFO] Camera test running. Press 'q' to quit.")

    while True:
        # 1. Get raw frame
        frame = cam.get_frame()
        if frame is None:
            break

        # 2. Preprocess
        bgr_frame, rgb_frame = cam.preprocess(frame)

        # 3. Draw debug overlay
        bgr_frame = cam.draw_overlay(bgr_frame, extra_text="Status: OK")

        # 4. Show window
        cv2.imshow("RYVA — Camera Test", bgr_frame)

        # 5. Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Quit signal received.")
            break


    cam.release()
    cam.release()

