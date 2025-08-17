from __future__ import annotations
import os
from flask import Blueprint, current_app, request, jsonify, render_template

from ..utils.file_utils import allowed_file, save_upload, derive_output_path
from ..services.ascii_engine import image_to_ascii, video_to_ascii_frames
from ..services.terminal_player import player, CLEAR, HOME

bp = Blueprint("api", __name__)

@bp.post("/upload/image")
def upload_image():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No image uploaded"}), 400

    if not allowed_file(file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
        return jsonify({"error": "Unsupported image format"}), 400

    path = save_upload(file, current_app.config["UPLOAD_FOLDER"])

    target_width = int(request.form.get("width", current_app.config["DEFAULT_TARGET_WIDTH"]))
    charset = request.form.get("charset", current_app.config["DEFAULT_ASCII_CHARSET"]) or "@%#*+=-:. "
    invert = request.form.get("invert", "false").lower() == "true"
    color = request.form.get("color", "false").lower() == "true"
    to_terminal = request.form.get("terminal", "false").lower() == "true"

    import cv2
    img = cv2.imread(path)
    ascii_art = image_to_ascii(img, target_width=target_width, charset=charset, invert=invert, color=color)

    out_path = derive_output_path(path, current_app.config["OUTPUT_FOLDER"], suffix="_ascii.txt")
    with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(ascii_art)

    if to_terminal:
        import sys
        sys.stdout.write(HOME + CLEAR + ascii_art + "\n")
        sys.stdout.flush()

    return render_template("success.html", kind="image", upload_path=path, output_path=out_path)

@bp.post("/upload/video")
def upload_video():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No video uploaded"}), 400

    if not allowed_file(file.filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"]):
        return jsonify({"error": "Unsupported video format"}), 400

    path = save_upload(file, current_app.config["UPLOAD_FOLDER"])

    target_width = int(request.form.get("width", current_app.config["DEFAULT_TARGET_WIDTH"]))
    charset = request.form.get("charset", current_app.config["DEFAULT_ASCII_CHARSET"]) or "@%#*+=-:. "
    invert = request.form.get("invert", "false").lower() == "true"
    color = request.form.get("color", "false").lower() == "true"
    play_terminal = request.form.get("terminal", "true").lower() == "true"

    if play_terminal:
        frames = video_to_ascii_frames(
            video_path=path,
            target_width=target_width,
            target_height=None,
            charset=charset,
            invert=invert,
            color=color,
        )
        try:
            player.start_in_thread(frames)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 409

    note_path = derive_output_path(path, current_app.config["OUTPUT_FOLDER"], suffix="_howto.txt")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(
            "You uploaded: %s\n"
            "Playback started in server terminal (if enabled).\n"
            "To replay via Python shell, import the engine and player.\n" % path
        )

    return render_template("success.html", kind="video", upload_path=path, output_path=note_path)

@bp.post("/control/stop")
def stop_playback():
    player.stop()
    return jsonify({"status": "stopped"})
