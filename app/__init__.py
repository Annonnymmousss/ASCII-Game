import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        MAX_CONTENT_LENGTH=512 * 1024 * 1024,  # 512MB
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        OUTPUT_FOLDER=os.path.join(app.instance_path, "outputs"),
        ALLOWED_IMAGE_EXTENSIONS={"png", "jpg", "jpeg", "bmp", "gif"},
        ALLOWED_VIDEO_EXTENSIONS={"mp4", "avi", "mov", "mkv", "webm"},
        DEFAULT_ASCII_CHARSET="@%#*+=-:. ",
        DEFAULT_TARGET_WIDTH=120,
        DEFAULT_INVERT=False,
        DEFAULT_COLOR=False,
    )

    # Ensure instance folders exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    # Register blueprints
    from .blueprints.main import bp as main_bp
    from .blueprints.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
