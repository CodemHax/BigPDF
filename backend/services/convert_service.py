import os
import ipaddress
import socket
import subprocess
import zipfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from PIL import Image

from services.file_service import get_output_path, get_output_dir

LIBREOFFICE_SUPPORTED = {
    ".doc", ".docx", ".odt", ".rtf", ".txt",
    ".xls", ".xlsx", ".ods", ".csv",
    ".ppt", ".pptx", ".odp",
    ".html", ".htm", ".xml", ".epub",
}

_libreoffice_path_cache = None
_node_path_cache = None


def normalize_image_format(fmt: str) -> str:
    normalized = fmt.strip().lower()
    if normalized == "jpeg":
        return "jpg"
    if normalized in ("png", "jpg"):
        return normalized
    raise ValueError("Format must be 'png' or 'jpg'.")


def _pillow_save_format(fmt: str) -> str:
    return "JPEG" if fmt == "jpg" else "PNG"


def _find_libreoffice() -> str:
    global _libreoffice_path_cache
    if _libreoffice_path_cache:
        return _libreoffice_path_cache

    candidates = [
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/local/bin/libreoffice",
        "/usr/local/bin/soffice",
        "/snap/bin/libreoffice",
        "libreoffice",
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]

    for path in candidates:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                _libreoffice_path_cache = path
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
            continue

    raise RuntimeError(
        "LibreOffice not found. Install it with: sudo apt install libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress"
    )


def _find_node() -> str:
    global _node_path_cache
    if _node_path_cache:
        return _node_path_cache

    candidates = [
        os.getenv("NODE_BINARY", ""),
        "node",
        "node.exe",
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]

    for path in candidates:
        if not path:
            continue
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                _node_path_cache = path
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
            continue

    raise RuntimeError("Node.js not found. Install Node.js to use HTML to PDF conversion with Puppeteer.")


def _convert_with_libreoffice(file_path: Path, output_id: str, output_format: str = "pdf") -> Path:
    lo_path = _find_libreoffice()
    output_dir = get_output_dir(output_id)

    subprocess.run(
        [
            lo_path,
            "--headless",
            "--norestore",
            "--convert-to",
            output_format,
            "--outdir",
            str(output_dir),
            str(file_path),
        ],
        capture_output=True,
        timeout=180,
        check=True,
    )

    output_name = file_path.stem + f".{output_format}"
    output_file = output_dir / output_name

    if not output_file.exists():
        raise RuntimeError(f"LibreOffice conversion failed: output file '{output_name}' not found.")

    final_path = get_output_path(output_id, f"converted.{output_format}")
    if output_file != final_path:
        os.rename(str(output_file), str(final_path))

    return final_path


def pdf_to_images(file_path: Path, output_id: str, fmt: str = "png", dpi: int = 200) -> Path:
    from pdf2image import convert_from_path

    fmt = normalize_image_format(fmt)
    save_format = _pillow_save_format(fmt)
    output_dir = get_output_dir(output_id)
    images = convert_from_path(str(file_path), dpi=dpi, fmt=fmt)

    image_paths = []
    for idx, img in enumerate(images):
        img_name = f"page_{idx + 1}.{fmt}"
        img_path = output_dir / img_name
        if save_format == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(str(img_path), save_format)
        image_paths.append(img_path)

    if len(image_paths) == 1:
        return image_paths[0]

    zip_path = get_output_path(output_id, "pdf_images.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img_path in image_paths:
            zf.write(img_path, img_path.name)

    return zip_path


def images_to_pdf(file_paths: List[Path], output_id: str, page_size: str = "a4") -> Path:
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as canvas_module

    page_sizes = {
        "a4": A4,
        "letter": LETTER,
    }
    ps = page_sizes.get(page_size.lower(), A4)
    output_path = get_output_path(output_id, "images_combined.pdf")

    c = canvas_module.Canvas(str(output_path), pagesize=ps)
    page_width, page_height = ps

    for img_path in file_paths:
        with Image.open(str(img_path)) as img:
            image = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img.copy()

        img_width, img_height = image.size

        scale = min(page_width / img_width, page_height / img_height)
        scaled_width = img_width * scale
        scaled_height = img_height * scale

        x = (page_width - scaled_width) / 2
        y = (page_height - scaled_height) / 2

        c.drawImage(ImageReader(image), x, y, scaled_width, scaled_height, mask="auto")
        c.showPage()

    c.save()
    return output_path


def word_to_pdf(file_path: Path, output_id: str) -> Path:
    return _convert_with_libreoffice(file_path, output_id, "pdf")


def powerpoint_to_pdf(file_path: Path, output_id: str) -> Path:
    return _convert_with_libreoffice(file_path, output_id, "pdf")


def excel_to_pdf(file_path: Path, output_id: str) -> Path:
    return _convert_with_libreoffice(file_path, output_id, "pdf")


def _render_with_puppeteer(source_type: str, source: str, output_id: str) -> Path:
    node_path = _find_node()
    script_path = Path(__file__).parent.parent / "scripts" / "html_to_pdf_puppeteer.js"
    if not script_path.exists():
        raise RuntimeError("Puppeteer HTML to PDF renderer script is missing.")

    output_path = get_output_path(output_id, "converted.pdf")
    result = subprocess.run(
        [node_path, str(script_path), f"--{source_type}", source, str(output_path)],
        cwd=str(script_path.parent.parent),
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Puppeteer conversion failed.").strip()
        raise RuntimeError(message)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Puppeteer conversion failed: output PDF was not created.")

    return output_path


def _normalize_public_url(url: str) -> str:
    value = url.strip()
    if len(value) > 2048:
        raise ValueError("URL is too long.")

    parsed = urlparse(value)
    if not parsed.scheme:
        parsed = urlparse(f"https://{value}")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://.")
    if not parsed.hostname:
        raise ValueError("Enter a valid URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs with usernames or passwords are not allowed.")

    host = parsed.hostname.strip().lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("Localhost URLs are not allowed.")

    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Enter a valid URL port.")

    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError("Could not resolve the URL host.")

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private, local, or reserved network URLs are not allowed.")

    normalized_host = host.encode("idna").decode("ascii")
    netloc = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
    if port:
        netloc = f"{netloc}:{port}"
    return urlunparse((parsed.scheme, netloc, parsed.path or "/", parsed.params, parsed.query, ""))


def html_to_pdf(file_path: Path, output_id: str) -> Path:
    ext = file_path.suffix.lower()
    if ext not in (".html", ".htm"):
        raise ValueError("Unsupported HTML file. Upload a .html or .htm file.")

    return _render_with_puppeteer("file", str(file_path), output_id)


def url_to_pdf(url: str, output_id: str) -> Path:
    return _render_with_puppeteer("url", _normalize_public_url(url), output_id)


def any_to_pdf(file_path: Path, output_id: str) -> Path:
    ext = file_path.suffix.lower()
    if ext not in LIBREOFFICE_SUPPORTED:
        raise ValueError(
            f"Unsupported format '{ext}'. Supported: {', '.join(sorted(LIBREOFFICE_SUPPORTED))}"
        )
    return _convert_with_libreoffice(file_path, output_id, "pdf")
