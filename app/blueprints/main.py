from flask import Blueprint, current_app, render_template

bp = Blueprint("main", __name__)

@bp.get("/")
def index():
    cfg = dict(
        default_width=current_app.config["DEFAULT_TARGET_WIDTH"],
        default_charset=current_app.config["DEFAULT_ASCII_CHARSET"],
        default_invert=current_app.config["DEFAULT_INVERT"],
        default_color=current_app.config["DEFAULT_COLOR"],
    )
    return render_template("index.html", **cfg)
