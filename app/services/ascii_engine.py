from __future__ import annotations
import shutil
from typing import Iterable, Tuple

import cv2
import numpy as np

# Character aspect ratio compensation: terminal cells are ~2x taller than wide
CHAR_ASPECT = 2.0  # height ≈ 2 * width

def get_terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines

def _normalize_frame(gray: np.ndarray, invert: bool) -> np.ndarray:
    if invert:
        gray = 255 - gray
    return gray

def image_to_ascii(
    img_bgr: np.ndarray,
    target_width: int = 120,
    target_height: int | None = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
) -> str:
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Empty image provided")

    h, w = img_bgr.shape[:2]

    if target_height is None:
        aspect = h / w
        target_height = max(1, int(aspect * target_width / CHAR_ASPECT))

    resized = cv2.resize(img_bgr, (target_width, target_height), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    gray = _normalize_frame(gray, invert)

    chars = np.asarray(list(charset))
    bins = np.linspace(0, 256, num=len(chars) + 1, dtype=np.float32)
    idx = np.digitize(gray.astype(np.float32), bins) - 1
    idx = np.clip(idx, 0, len(chars) - 1)

    if not color:
        lines = ["".join(chars[row]) for row in idx]
        return "\n".join(lines)

    # Truecolor ANSI
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    out_lines = []
    for y in range(idx.shape[0]):
        row_chars = []
        for x in range(idx.shape[1]):
            ch = chars[idx[y, x]]
            r, g, b = rgb[y, x]
            row_chars.append(f"\x1b[38;2;{int(r)};{int(g)};{int(b)}m{ch}\x1b[0m")
        out_lines.append("".join(row_chars))
    return "\n".join(out_lines)

def video_to_ascii_frames(
    video_path: str,
    target_width: int = 120,
    target_height: int | None = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
) -> Iterable[Tuple[str, float]]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    spf = 1.0 / float(fps)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            ascii_frame = image_to_ascii(
                frame,
                target_width=target_width,
                target_height=target_height,
                charset=charset,
                invert=invert,
                color=color,
            )
            yield ascii_frame, spf
    finally:
        cap.release()
