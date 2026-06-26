# =============================================================
# RYVA Project — vision/face_pipeline.py
# Purpose : Face tracking — EAR, Head Pitch, Gaze Direction
# Author  : RYVA Team
# Usage   : python vision/face_pipeline.py
# Done When: EAR prints 0.28–0.32 eyes open, drops to 0.15
#            when closed. Head pitch increases on forward tilt.
#            Prints at 25fps with no stuttering.
# =============================================================

import cv2
import mediapipe as mp
import numpy as np
import time
import collections

# ==============================================================
# CONSTANTS
# ==============================================================

# Left eye landmark indices (MediaPipe Face Mesh)
LEFT_EYE  = [33, 160, 158, 133, 153, 144]

# Right eye landmark indices
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# 3D model points for head pose (generic face model in mm)
MODEL_3D_POINTS = np.array([
    (0.0,    0.0,    0.0),      # Nose tip         — landmark 1
    (0.0,   -330.0, -65.0),     # Chin             — landmark 152
    (-225.0, 170.0, -135.0),    # Left eye corner  — landmark 33
    (225.0,  170.0, -135.0),    # Right eye corner — landmark 263
    (-150.0,-150.0, -125.0),    # Left mouth corner— landmark 61
    (150.0, -150.0, -125.0),    # Right mouth corner— landmark 291
], dtype=np.float64)

# Corresponding MediaPipe landmark indices for head pose
POSE_LANDMARK_IDS = [1, 152, 33, 263, 61, 291]

# Blink threshold
BLINK_THRESHOLD = 0.25

# 30-second rolling window at 25fps
WINDOW_SIZE = 750

# Target FPS
TARGET_FPS = 25
FRAME_INTERVAL = 1.0 / TARGET_FPS


# ==============================================================
# HELPER FUNCTIONS
# ==============================================================

def get_landmark_coords(landmarks, indices, img_w, img_h):
    """
    Converts normalized MediaPipe landmarks to pixel coordinates.
    Args:
        landmarks : face_mesh landmark list
        indices   : list of landmark indices to extract
        img_w, img_h : frame dimensions
    Returns:
        numpy array of (x, y) pixel coords
    """
    return np.array([
        (landmarks[i].x * img_w, landmarks[i].y * img_h)
        for i in indices
    ], dtype=np.float64)


def compute_EAR(eye_points):
    """
    Computes Eye Aspect Ratio (EAR) for one eye.
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    Args:
        eye_points : numpy array of 6 (x,y) points
    Returns:
        EAR value (float). Normal ~0.28–0.32. Blink < 0.25
    """
    p1, p2, p3, p4, p5, p6 = eye_points

    A = np.linalg.norm(p2 - p6)  # vertical distance 1
    B = np.linalg.norm(p3 - p5)  # vertical distance 2
    C = np.linalg.norm(p1 - p4)  # horizontal distance

    ear = (A + B) / (2.0 * C)
    return round(float(ear), 3)


def compute_head_pose(landmarks, img_w, img_h):
    """
    Computes head pitch (forward/backward tilt) using solvePnP.
    Args:
        landmarks  : MediaPipe face landmark list
        img_w, img_h : frame dimensions
    Returns:
        pitch (float) : forward tilt in degrees
        yaw   (float) : left/right turn in degrees
        roll  (float) : head tilt in degrees
    """
    # Get 2D image points for the 6 landmarks
    image_2d_points = np.array([
        (landmarks[i].x * img_w, landmarks[i].y * img_h)
        for i in POSE_LANDMARK_IDS
    ], dtype=np.float64)

    # Camera internals (estimated)
    focal_length = img_w
    cam_matrix = np.array([
        [focal_length, 0,            img_w / 2],
        [0,            focal_length, img_h / 2],
        [0,            0,            1        ]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rot_vec, trans_vec = cv2.solvePnP(
        MODEL_3D_POINTS,
        image_2d_points,
        cam_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0, 0.0, 0.0

    # Convert rotation vector to rotation matrix
    rot_matrix, _ = cv2.Rodrigues(rot_vec)

    # Extract Euler angles (pitch, yaw, roll) in degrees
    pitch = np.degrees(np.arctan2(rot_matrix[2][1], rot_matrix[2][2]))
    yaw   = np.degrees(np.arctan2(-rot_matrix[2][0],
                        np.sqrt(rot_matrix[2][1]**2 + rot_matrix[2][2]**2)))
    roll  = np.degrees(np.arctan2(rot_matrix[1][0], rot_matrix[0][0]))

    return round(pitch, 2), round(yaw, 2), round(roll, 2)


def compute_gaze(landmarks, img_w, img_h):
    """
    Estimates gaze direction based on iris position relative to eye corners.
    Returns:
        gaze (str): "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
    """
    # Use left iris (landmark 468) and left eye corners (33, 133)
    iris_x  = landmarks[468].x * img_w
    iris_y  = landmarks[468].y * img_h
    left_x  = landmarks[33].x  * img_w
    right_x = landmarks[133].x * img_w
    top_y   = landmarks[159].y * img_h
    bot_y   = landmarks[145].y * img_h

    eye_width  = right_x - left_x
    eye_height = bot_y - top_y

    if eye_width == 0 or eye_height == 0:
        return "CENTER"

    h_ratio = (iris_x - left_x) / eye_width
    v_ratio = (iris_y - top_y)  / eye_height

    if h_ratio < 0.35:
        return "LEFT"
    elif h_ratio > 0.65:
        return "RIGHT"
    elif v_ratio < 0.35:
        return "UP"
    elif v_ratio > 0.65:
        return "DOWN"
    else:
        return "CENTER"


# ==============================================================
# MAIN FACE PIPELINE CLASS
# ==============================================================

class FacePipeline:
    """
    Runs face tracking at 25fps and computes:
      - EAR  (Eye Aspect Ratio) — eye openness
      - Head Pitch              — forward tilt
      - Gaze Direction          — where operator is looking
      - Blink detection         — EAR < 0.25 for 2+ frames
    """

    def __init__(self):
        # MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,   # needed for iris landmarks (468+)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Rolling 30-second window at 25fps
        self.ear_window   = collections.deque(maxlen=WINDOW_SIZE)
        self.pitch_window = collections.deque(maxlen=WINDOW_SIZE)

        # Blink tracking
        self.blink_counter     = 0   # consecutive low-EAR frames
        self.total_blinks      = 0
        self.blink_flag        = False

        # FPS control
        self.last_frame_time = time.time()

    def process_frame(self, frame):
        """
        Processes one frame and returns face metrics.
        Args:
            frame : BGR frame from OpenCV
        Returns:
            dict with keys: ear, pitch, yaw, roll, gaze, blink, total_blinks
            or None if no face detected
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0].landmark

        # --- EAR ---
        left_pts  = get_landmark_coords(landmarks, LEFT_EYE,  w, h)
        right_pts = get_landmark_coords(landmarks, RIGHT_EYE, w, h)
        left_ear  = compute_EAR(left_pts)
        right_ear = compute_EAR(right_pts)
        avg_ear   = round((left_ear + right_ear) / 2.0, 3)

        # --- Blink Detection ---
        if avg_ear < BLINK_THRESHOLD:
            self.blink_counter += 1
        else:
            if self.blink_counter >= 2:    # 2+ consecutive frames = blink
                self.total_blinks += 1
                self.blink_flag = True
            else:
                self.blink_flag = False
            self.blink_counter = 0

        # --- Head Pose ---
        pitch, yaw, roll = compute_head_pose(landmarks, w, h)

        # --- Gaze ---
        gaze = compute_gaze(landmarks, w, h)

        # --- Store in rolling window ---
        self.ear_window.append(avg_ear)
        self.pitch_window.append(pitch)

        return {
            "ear"          : avg_ear,
            "pitch"        : pitch,
            "yaw"          : yaw,
            "roll"         : roll,
            "gaze"         : gaze,
            "blink"        : self.blink_flag,
            "total_blinks" : self.total_blinks
        }

    def draw_metrics(self, frame, metrics):
        """
        Draws EAR, pitch, gaze, blink count on the frame.
        """
        if metrics is None:
            cv2.putText(frame, "No face detected", (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame

        color_ear = (0, 255, 0) if metrics["ear"] >= BLINK_THRESHOLD else (0, 0, 255)

        cv2.putText(frame, f"EAR   : {metrics['ear']}",
                    (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_ear, 2)
        cv2.putText(frame, f"Pitch : {metrics['pitch']} deg",
                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
        cv2.putText(frame, f"Yaw   : {metrics['yaw']} deg",
                    (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
        cv2.putText(frame, f"Gaze  : {metrics['gaze']}",
                    (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 255, 200), 2)
        cv2.putText(frame, f"Blinks: {metrics['total_blinks']}",
                    (10, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 2)

        if metrics["blink"]:
            cv2.putText(frame, "BLINK!", (250, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        cv2.putText(frame, "RYVA Face Pipeline",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        return frame

    def release(self):
        self.face_mesh.close()


# ==============================================================
# QUICK TEST — Run this file directly
# python vision/face_pipeline.py
# Press 'q' to quit
# ==============================================================

if __name__ == "__main__":

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    pipeline = FacePipeline()

    print("[INFO] Face pipeline running at 25fps. Press 'q' to quit.\n")
    print(f"{'EAR':<10} {'Pitch':<12} {'Yaw':<10} {'Gaze':<10} {'Blinks'}")
    print("-" * 55)

    last_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # --- 25 FPS throttle ---
        now = time.time()
        elapsed = now - last_time
        if elapsed < FRAME_INTERVAL:
            continue
        last_time = now

        # --- Process ---
        metrics = pipeline.process_frame(frame)

        # --- Print to terminal ---
        if metrics:
            print(
                f"{metrics['ear']:<10} "
                f"{metrics['pitch']:<12} "
                f"{metrics['yaw']:<10} "
                f"{metrics['gaze']:<10} "
                f"{metrics['total_blinks']}"
            )

        # --- Draw and show ---
        frame = pipeline.draw_metrics(frame, metrics)
        cv2.imshow("RYVA — Face Pipeline", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n[INFO] Quit signal received.")
            break

    cap.release()
    pipeline.release()
    cv2.destroyAllWindows()
