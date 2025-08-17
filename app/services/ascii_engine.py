from __future__ import annotations
import shutil
import sys
import time
from typing import Iterable, Tuple, Optional

import cv2
import numpy as np


CHAR_ASPECT = 2.0  

def get_terminal_size() -> tuple[int, int]:
    """
    Return terminal (columns, lines). Fallback if unknown.
    """
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines

def _normalize_frame(gray: np.ndarray, invert: bool) -> np.ndarray:
    """
    Optionally invert a grayscale image.
    """
    if invert:
        return 255 - gray
    return gray

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
    - target_width: number of characters per line
    - target_height: if None, computed to preserve aspect ratio (with CHAR_ASPECT)
    - charset: string from dense->sparse
    - invert: invert luminance
    - color: if True, returns ANSI-escaped colored characters (24-bit)
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
        lines = ["".join(chars[row]) for row in idx]
        return "\n".join(lines)


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
    target_height: Optional[int] = None,
    charset: str = "@%#*+=-:. ",
    invert: bool = False,
    color: bool = False,
) -> Iterable[Tuple[str, float]]:
    """
    Lazy generator: opens a video file and yields tuples (ascii_frame: str, seconds_per_frame: float)
    This does NOT print frames — it just generates them lazily so a player can pace them.

    Usage:
        for ascii_frame, spf in video_to_ascii_frames(...):
            print(ascii_frame)
            time.sleep(spf)
    """
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
    """
    Convenience function to open a video and play it in the terminal at the video's FPS.
    - clear_each: whether to clear terminal between frames (recommended).
    - max_frame_skip: if processing can't keep up, allow skipping up to this many frames to catch up.
      Set to 0 to never skip (may lag).
    Notes:
      - This function prints directly to stdout and blocks until playback ends.
      - Use the generator `video_to_ascii_frames` + an external player thread if you prefer non-blocking behavior.
    """
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

            frame_proc_start = time.perf_counter()
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


                behind_seconds = -remaining
                frames_behind = int(behind_seconds // spf)
                if frames_behind > 0 and max_frame_skip > 0:
                    skip = min(frames_behind, max_frame_skip)

                    for _ in range(skip):
                        ok, _ = cap.read()
                        if not ok:
                            break
                        frame_index += 1


                    continue



            frame_proc_end = time.perf_counter()
            proc_time = frame_proc_end - frame_proc_start
            if proc_time < 0.001:

                time.sleep(0.0005)

    finally:
        cap.release()
        sys.stdout.write("\n" + _SHOW_CURSOR)
        sys.stdout.flush()
