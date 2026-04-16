import io
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from PIL import Image

from services.file_service import get_output_path, get_output_dir


def merge_pdfs(file_paths: List[Path], output_id: str) -> Path:
    writer = PdfWriter()
    for file_path in file_paths:
        try:
            reader = PdfReader(str(file_path))
            for page in reader.pages:
                writer.add_page(page)
        except Exception as e:
            raise ValueError(f"Failed to read PDF '{file_path.name}': {str(e)}")

    output_path = get_output_path(output_id, "merged.pdf")
    try:
        with open(str(output_path), "wb") as f:
            writer.write(f)
    except Exception as e:
        raise ValueError(f"Failed to write merged PDF: {str(e)}")
    return output_path


def split_pdf(file_path: Path, output_id: str, ranges: Optional[List[str]] = None) -> Path:
    reader = PdfReader(str(file_path))
    total_pages = len(reader.pages)

    if not ranges:
        ranges = [str(i) for i in range(1, total_pages + 1)]

    selected_pages = set()
    for r in ranges:
        pages = _parse_range(r, total_pages)
        selected_pages.update(pages)

    if not selected_pages:
        raise ValueError("No valid pages selected.")

    sorted_pages = sorted(selected_pages)
    writer = PdfWriter()
    for page_num in sorted_pages:
        writer.add_page(reader.pages[page_num - 1])

    output_path = get_output_path(output_id, "split.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def compress_pdf(file_path: Path, output_id: str, quality: str = "medium") -> Path:
    output_path = get_output_path(output_id, "compressed.pdf")
    source_size = file_path.stat().st_size

    with tempfile.TemporaryDirectory(dir=output_path.parent) as temp_dir:
        temp_dir_path = Path(temp_dir)
        candidates = []

        repacked_path = temp_dir_path / "repacked.pdf"
        _compress_pdf_with_pikepdf(file_path, repacked_path, quality)
        candidates.append(repacked_path)

        image_rewrite_path = temp_dir_path / "image-rewrite.pdf"
        if _compress_pdf_images(file_path, image_rewrite_path, quality):
            candidates.append(image_rewrite_path)

        valid_candidates = [
            path for path in candidates
            if path.exists() and path.stat().st_size > 0
        ]
        if not valid_candidates:
            raise ValueError("No valid compressed PDF could be created.")

        best_path = min(valid_candidates, key=lambda path: path.stat().st_size)
        if best_path.stat().st_size < source_size:
            shutil.copyfile(best_path, output_path)
        else:
            shutil.copyfile(file_path, output_path)

    return output_path


def _compress_pdf_with_pikepdf(file_path: Path, output_path: Path, quality: str) -> None:
    import pikepdf

    quality_settings = {
        "low": {
            "object_stream_mode": pikepdf.ObjectStreamMode.generate,
            "compress_streams": True,
            "recompress_flate": True,
        },
        "medium": {
            "object_stream_mode": pikepdf.ObjectStreamMode.generate,
            "compress_streams": True,
            "recompress_flate": True,
        },
        "high": {
            "object_stream_mode": pikepdf.ObjectStreamMode.generate,
            "compress_streams": True,
            "recompress_flate": True,
        },
    }

    settings = quality_settings.get(quality, quality_settings["medium"])

    with pikepdf.open(str(file_path)) as pdf:
        pdf.remove_unreferenced_resources()
        
        if quality == "low":
            for page in pdf.pages:
                try:
                    if "/Contents" in page:
                        page.Contents.compress_content_streams()
                except Exception:
                    pass
        
        pdf.save(str(output_path), **settings)


def _compress_pdf_images(file_path: Path, output_path: Path, quality: str) -> bool:
    try:
        import fitz
    except ImportError:
        return False

    image_profiles = {
        "high": {"dpi_threshold": 260, "dpi_target": 220, "quality": 84},
        "medium": {"dpi_threshold": 180, "dpi_target": 144, "quality": 68},
        "low": {"dpi_threshold": 150, "dpi_target": 110, "quality": 45},
    }
    profile = image_profiles.get(quality, image_profiles["medium"])

    document = None
    try:
        document = fitz.open(str(file_path))
        document.rewrite_images(
            dpi_threshold=profile["dpi_threshold"],
            dpi_target=profile["dpi_target"],
            quality=profile["quality"],
            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True,
            set_to_gray=False,
        )
        document.save(
            str(output_path),
            garbage=4,
            clean=False,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            use_objstms=1,
            compression_effort=9,
        )
    except Exception:
        _close_pdf_document(document)
        return False

    _close_pdf_document(document)
    return output_path.exists() and output_path.stat().st_size > 0


def _close_pdf_document(document) -> None:
    if document is not None:
        try:
            document.close()
        except Exception:
            pass


def rotate_pdf(file_path: Path, output_id: str, rotation: int = 90) -> Path:
    reader = PdfReader(str(file_path))
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(rotation)
        writer.add_page(page)

    output_path = get_output_path(output_id, "rotated.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def protect_pdf(file_path: Path, output_id: str, password: str) -> Path:
    import pikepdf

    output_path = get_output_path(output_id, "protected.pdf")
    with pikepdf.open(str(file_path)) as pdf:
        pdf.save(
            str(output_path),
            encryption=pikepdf.Encryption(
                owner=password,
                user=password,
                R=6,
            ),
        )
    return output_path


def unlock_pdf(file_path: Path, output_id: str, password: str) -> Path:
    import pikepdf

    output_path = get_output_path(output_id, "unlocked.pdf")
    try:
        with pikepdf.open(str(file_path), password=password) as pdf:
            pdf.save(str(output_path))
    except pikepdf.PasswordError:
        raise ValueError("Incorrect password.")
    return output_path


def watermark_pdf(
    file_path: Path,
    output_id: str,
    text: str = "CONFIDENTIAL",
    opacity: float = 0.3,
    font_size: int = 50,
    rotation: int = 45,
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
) -> Path:
    reader = PdfReader(str(file_path))
    writer = PdfWriter()

    for page in reader.pages:
        box = page.cropbox if page.cropbox else page.mediabox
        left = float(box.left)
        bottom = float(box.bottom)
        width = float(box.width)
        height = float(box.height)
        right = float(box.right)
        top = float(box.top)

        rotation_angle = int(page.get("/Rotate", 0) or 0)

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(right, top))
        c.saveState()
        c.setFillColor(Color(color[0], color[1], color[2], alpha=opacity))
        c.setFont("Helvetica-Bold", font_size)

        center_x = left + (width / 2)
        center_y = bottom + (height / 2)
        c.translate(center_x, center_y)

        final_rotation = rotation - rotation_angle
        c.rotate(final_rotation)

        c.drawCentredString(0, 0, text)
        c.restoreState()
        c.save()

        packet.seek(0)
        watermark_reader = PdfReader(packet)
        watermark_page = watermark_reader.pages[0]

        watermark_page.mediabox = page.mediabox
        if page.cropbox:
            watermark_page.cropbox = page.cropbox

        page.merge_page(watermark_page)
        writer.add_page(page)

    output_path = get_output_path(output_id, "watermarked.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def add_page_numbers(
    file_path: Path,
    output_id: str,
    position: str = "bottom-center",
    start_number: int = 1,
    font_size: int = 12,
) -> Path:
    reader = PdfReader(str(file_path))
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        page_num = start_number + idx

        positions = {
            "bottom-center": (page_width / 2, 30),
            "bottom-left": (40, 30),
            "bottom-right": (page_width - 40, 30),
            "top-center": (page_width / 2, page_height - 30),
            "top-left": (40, page_height - 30),
            "top-right": (page_width - 40, page_height - 30),
        }

        x, y = positions.get(position, positions["bottom-center"])

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))
        c.setFont("Helvetica", font_size)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawCentredString(x, y, str(page_num))
        c.save()

        packet.seek(0)
        number_page = PdfReader(packet).pages[0]
        page.merge_page(number_page)
        writer.add_page(page)

    output_path = get_output_path(output_id, "numbered.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def organize_pages(file_path: Path, output_id: str, page_order: List[int]) -> Path:
    reader = PdfReader(str(file_path))
    writer = PdfWriter()

    for page_num in page_order:
        if 1 <= page_num <= len(reader.pages):
            writer.add_page(reader.pages[page_num - 1])

    output_path = get_output_path(output_id, "organized.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def _parse_range(range_str: str, total_pages: int) -> List[int]:
    pages = []
    range_str = range_str.strip()
    if "-" in range_str:
        parts = range_str.split("-")
        start = max(1, int(parts[0]))
        end = min(total_pages, int(parts[1]))
        pages = list(range(start, end + 1))
    else:
        page = int(range_str)
        if 1 <= page <= total_pages:
            pages = [page]
    return pages


def extract_text(file_path: Path, output_id: str) -> Path:
    reader = PdfReader(str(file_path))
    output_path = get_output_path(output_id, "extracted.txt")

    lines = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        lines.append(f"--- Page {i + 1} ---")
        lines.append(text.strip())
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def filter_pdf(file_path: Path, output_id: str, filter_type: str = "grayscale") -> Path:
    try:
        import fitz
        from PIL import Image, ImageOps, ImageEnhance
    except ImportError:
        raise ValueError("PyMuPDF or Pillow not available")
    
    output_path = get_output_path(output_id, f"filtered_{filter_type}.pdf")
    document = fitz.open(str(file_path))
    out_document = fitz.open()
    
    try:
        for page_num in range(len(document)):
            page = document[page_num]
            pixmap = page.get_pixmap(alpha=False, matrix=fitz.Matrix(2, 2))
            
            mode = "RGB" if pixmap.n < 4 else "RGBA"
            pil_img = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
            
            if filter_type == "grayscale":
                pil_img = ImageOps.grayscale(pil_img)
            elif filter_type == "invert":
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                pil_img = ImageOps.invert(pil_img)
            elif filter_type == "brighter":
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(1.4)
            elif filter_type == "darker":
                enhancer = ImageEnhance.Brightness(pil_img)
                pil_img = enhancer.enhance(0.6)
            
            img_path = str(file_path).replace(".pdf", f"_temp_{page_num}.png")
            pil_img.save(img_path, format="PNG")
            
            out_page = out_document.new_page(width=page.rect.width, height=page.rect.height)
            
            out_page.insert_image(page.rect, filename=img_path)
            
            Path(img_path).unlink()
        
        out_document.save(str(output_path), deflate=True)
    finally:
        document.close()
        out_document.close()
    
    return output_path


def flatten_pdf(file_path: Path, output_id: str) -> Path:
    import fitz
    
    output_dir = get_output_dir(output_id)
    output_path = output_dir / "output.pdf"
    document = None
    
    try:
        document = fitz.open(str(file_path))
        
        for page_num in range(len(document)):
            page = document[page_num]
            page.clean_contents()
        
        document.save(str(output_path), deflate=True)
    finally:
        if document:
            document.close()
    
    return output_path
