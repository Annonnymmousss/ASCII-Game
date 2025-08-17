import os
from werkzeug.utils import secure_filename

def allowed_file(filename: str, allowed_exts: set[str]) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_exts

def save_upload(file_storage, dest_folder: str) -> str:
    os.makedirs(dest_folder, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    path = os.path.join(dest_folder, filename)
    file_storage.save(path)
    return path

def derive_output_path(upload_path: str, output_folder: str, suffix: str) -> str:
    base = os.path.basename(upload_path)
    name, _ = os.path.splitext(base)
    os.makedirs(output_folder, exist_ok=True)
    return os.path.join(output_folder, f"{name}{suffix}")
