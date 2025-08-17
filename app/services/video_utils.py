import cv2

def get_video_fps(path: str) -> float:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return 24.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    cap.release()
    return float(fps)
