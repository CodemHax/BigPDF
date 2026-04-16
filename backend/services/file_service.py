import os
import uuid
import time
import shutil
import asyncio
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

CLEANUP_MAX_AGE_SECONDS = 30 * 60
MAX_FILE_SIZE = 100 * 1024 * 1024


def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_file_id() -> str:
    return str(uuid.uuid4())


def get_upload_path(file_id: str, filename: str) -> Path:
    file_dir = UPLOAD_DIR / file_id
    file_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in filename if c.isalnum() or c in ".-_ ")
    return file_dir / safe_name


def get_output_path(file_id: str, filename: str) -> Path:
    file_dir = OUTPUT_DIR / file_id
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir / filename


def get_output_dir(file_id: str) -> Path:
    file_dir = OUTPUT_DIR / file_id
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir


def _get_key_path(file_id: str) -> Path:
    """Get the key file path for a given file_id (one key per file_id)"""
    key_path = UPLOAD_DIR / file_id / ".fernet.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    return key_path


def _get_output_key_path(file_id: str) -> Path:
    """Get the key file path for output directory"""
    key_path = OUTPUT_DIR / file_id / ".fernet.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    return key_path


def _get_or_create_key(file_id: str, is_output: bool = False) -> bytes:
    """Get existing key or create a new one for the file_id"""
    key_path = _get_output_key_path(file_id) if is_output else _get_key_path(file_id)
    
    if key_path.exists():
        with open(key_path, "rb") as f:
            return f.read()
    
    # Create new key
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)
    return key


def _encrypt_file(file_path: Path, file_id: str) -> None:
    """Encrypt a file using the key associated with file_id"""
    # Determine if this is an upload or output file
    is_output = str(file_path).startswith(str(OUTPUT_DIR))
    key = _get_or_create_key(file_id, is_output=is_output)
    fernet = Fernet(key)

    with open(file_path, "rb") as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(file_path, "wb") as f:
        f.write(encrypted)


def _decrypt_file(file_path: Path, file_id: str) -> bytes:
    """Decrypt a file using the key associated with file_id"""
    # Determine if this is an upload or output file
    is_output = str(file_path).startswith(str(OUTPUT_DIR))
    key_path = _get_output_key_path(file_id) if is_output else _get_key_path(file_id)

    if not key_path.exists():
        # File is not encrypted, return as-is
        with open(file_path, "rb") as f:
            return f.read()

    with open(key_path, "rb") as f:
        key = f.read()

    fernet = Fernet(key)

    with open(file_path, "rb") as f:
        encrypted = f.read()

    return fernet.decrypt(encrypted)


def decrypt_to_temp(file_path: Path, file_id: str) -> Path:
    decrypted_data = _decrypt_file(file_path, file_id)
    temp_path = file_path.parent / f"_dec_{file_path.name}"

    with open(temp_path, "wb") as f:
        f.write(decrypted_data)

    return temp_path


def encrypt_output(file_path: Path, file_id: str) -> None:
    _encrypt_file(file_path, file_id)


def decrypt_for_download(file_path: Path, file_id: str) -> Path:
    return decrypt_to_temp(file_path, file_id)


def cleanup_temp_files(file_id: str):
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        dir_path = directory / file_id
        if dir_path.exists():
            for f in dir_path.iterdir():
                if f.name.startswith("_dec_"):
                    try:
                        f.unlink()
                    except Exception:
                        pass


async def save_upload(file_content: bytes, file_id: str, filename: str) -> Path:
    path = get_upload_path(file_id, filename)
    with open(path, "wb") as f:
        f.write(file_content)
    _encrypt_file(path, file_id)
    return path


def cleanup_old_files():
    now = time.time()
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
        for item in directory.iterdir():
            if item.is_dir():
                try:
                    age = now - item.stat().st_mtime
                    if age > CLEANUP_MAX_AGE_SECONDS:
                        shutil.rmtree(item)
                except Exception:
                    pass


async def periodic_cleanup():
    while True:
        cleanup_old_files()
        await asyncio.sleep(300)


def cleanup_file_id(file_id: str):
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        path = directory / file_id
        if path.exists():
            shutil.rmtree(path)
