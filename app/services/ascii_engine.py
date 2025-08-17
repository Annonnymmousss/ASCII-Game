from __future__ import annotations
import shutil
import sys
import time
from typing import Iterable, Tuple, Optional

import cv2
import numpy as np


CHAR_ASPECT = 2.0  # aspect correction factor for characters


def get_terminal_size() -> tuple[int, int]:
    """Return terminal (columns, lines). Fallback if unknown."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def _normalize_frame(gray: np.ndarray, invert: bool) -> np.ndarray:
    """Optionally invert a grayscale image."""
    return 255 - gray if invert else gray


def _boost_colors(rgb: np.ndarray, factor: float = 1.8) -> np.ndarray:
    """
    Boost saturation and contrast of RGB image to make colors pop.
    """
    # Convert to float for scaling
    rgb = rgb.astype(np.float32)

    # Center around 128, scale, and clamp
    rgb = (rgb - 128) * factor + 128
    rgb = np.clip(rgb, 0, 255)

    return rgb.astype(np.uint8)


def image_to_ascii(
    img_bgr: np.ndarray,
    target_width: int = 120,
    target_height: Optional[int] = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
) -> str:
    """
    Convert a BGR image (numpy array) to an ASCII multi-line string.
    Now with EXTREME color shading and true black chars.
    """
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
        return "\n".join("".join(chars[row]) for row in idx)

    # EXTREME COLORS
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    rgb = _boost_colors(rgb, factor=2.2)  # crank saturation

    out_lines = []
    for y in range(idx.shape[0]):
        row_chars = []
        for x in range(idx.shape[1]):
            r, g, b = rgb[y, x]
            ch = chars[idx[y, x]]

            # Extreme black detection
            if r < 40 and g < 40 and b < 40:
                row_chars.append(f"\x1b[38;2;0;0;0m{ch}\x1b[0m")
                continue

            # Amplify brightness for more vividness
            r = min(255, int(r * 1.5))
            g = min(255, int(g * 1.5))
            b = min(255, int(b * 1.5))

            row_chars.append(f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m")
        out_lines.append("".join(row_chars))
    return "\n".join(out_lines)


def video_to_ascii_frames(
    video_path: str,
    target_width: int = 120,
    target_height: Optional[int] = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
) -> Iterable[Tuple[str, float]]:
    """Lazy generator: yields (ascii_frame, seconds_per_frame)."""
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


# Terminal escape codes
_CLEAR = "\x1b[2J"
_HOME = "\x1b[H"
_HIDE_CURSOR = "\x1b[?25l"
_SHOW_CURSOR = "\x1b[?25h"


def play_video_in_terminal(
    video_path: str,
    target_width: int = 120,
    target_height: Optional[int] = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
    clear_each: bool = True,
    max_frame_skip: int = 5,
):
    """Play a video as ASCII directly in the terminal with extreme colors."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    spf = 1.0 / float(fps)

    try:
        sys.stdout.write(_HIDE_CURSOR)
        sys.stdout.flush()

        start_time = time.perf_counter()
        frame_index = 0

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

            if clear_each:
                sys.stdout.write(_HOME + _CLEAR)
            else:
                sys.stdout.write(_HOME)
            sys.stdout.write(ascii_frame)
            sys.stdout.flush()

            frame_index += 1
            next_due = start_time + frame_index * spf
            now = time.perf_counter()
            remaining = next_due - now

            if remaining > 0:
                time.sleep(remaining)
            else:
                behind = -remaining
                frames_behind = int(behind // spf)
                if frames_behind > 0 and max_frame_skip > 0:
                    skip = min(frames_behind, max_frame_skip)
                    for _ in range(skip):
                        ok, _ = cap.read()
                        if not ok:
                            break
                        frame_index += 1
                    continue
    finally:
        cap.release()
        sys.stdout.write("\n" + _SHOW_CURSOR)
        sys.stdout.flush()
