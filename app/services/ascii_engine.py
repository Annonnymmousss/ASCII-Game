from __future__ import annotations
import shutil
import sys
import time
from typing import Iterable, Tuple, Optional

import cv2
import numpy as np

# Character aspect ratio correction
CHAR_ASPECT = 2.0  


def get_terminal_size() -> tuple[int, int]:
    """Return terminal (columns, lines). Fallback if unknown."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def _normalize_frame(gray: np.ndarray, invert: bool) -> np.ndarray:
    """Optionally invert a grayscale image."""
    return 255 - gray if invert else gray


def _enhance_colors(rgb: np.ndarray, contrast: float = 1.4, saturation: float = 1.5, brightness: float = 1.15) -> np.ndarray:
    """
    Enhance contrast, saturation, and brightness while preserving blacks & whites.
    """
    rgb = rgb.astype(np.float32)

    # Contrast (centered at 128 to keep black/white intact)
    rgb = 128 + (rgb - 128) * contrast
    rgb = np.clip(rgb, 0, 255)

    # Brightness scaling
    rgb *= brightness
    rgb = np.clip(rgb, 0, 255)

    # Convert to HSV for saturation control
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] *= saturation  # Boost saturation
    hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)

    enhanced = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return enhanced


def _get_colored_char(r: int, g: int, b: int, ch: str) -> str:
    """
    Return ANSI-colored character with accurate black/white handling and vivid colors.
    """
    # True black stays black
    if r == 0 and g == 0 and b == 0:
        return f"\x1b[38;2;0;0;0m{ch}\x1b[0m"

    # Near-black shades (don’t brighten too much)
    if max(r, g, b) < 20:
        return f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"

    # Near-white shades (don’t oversaturate)
    if min(r, g, b) > 235:
        return f"\x1b[38;2;255;255;255m{ch}\x1b[0m"

    # Normal colors (boosted vividness already applied in _enhance_colors)
    return f"\x1b[38;2;{r};{g};{b}m{ch}\x1b[0m"


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
    Preserves blacks/whites + boosts colors for vivid output.
    """
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Empty image provided")

    h, w = img_bgr.shape[:2]

    # Maintain correct aspect ratio
    if target_height is None:
        aspect = h / w
        target_height = max(1, int(aspect * target_width / CHAR_ASPECT))

    resized = cv2.resize(img_bgr, (target_width, target_height), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    gray = _normalize_frame(gray, invert)

    # Map grayscale to charset
    chars = np.asarray(list(charset))
    bins = np.linspace(0, 256, num=len(chars) + 1, dtype=np.float32)
    idx = np.digitize(gray.astype(np.float32), bins) - 1
    idx = np.clip(idx, 0, len(chars) - 1)

    if not color:
        return "\n".join("".join(chars[row]) for row in idx)

    # Color mode: Enhance for vivid effect
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    rgb = _enhance_colors(rgb, contrast=1.4, saturation=1.5, brightness=1.15)

    out_lines = []
    for y in range(idx.shape[0]):
        row_chars = []
        for x in range(idx.shape[1]):
            r, g, b = rgb[y, x]
            ch = chars[idx[y, x]]
            row_chars.append(_get_colored_char(r, g, b, ch))
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
    """Play a video as ASCII directly in the terminal with vivid & precise colors."""
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
