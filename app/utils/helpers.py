from fastapi import UploadFile
from uuid import uuid4
import os
import shutil

def save_img(type: str, img: UploadFile) -> str:
    save_dir = f"static/{type}s"
    os.makedirs(save_dir, exist_ok=True)
    fn = f"{uuid4().hex}_{img.filename}"
    path = os.path.join(save_dir, fn)
    with open(path, "wb") as buf:
        shutil.copyfileobj(img.file, buf)

    return f"/{save_dir}/{fn}"