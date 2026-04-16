import io
from pathlib import Path
from typing import List, Dict, Any

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color

from services.file_service import get_output_path


def annotate_pdf(file_path: Path, output_id: str, annotations: List[Dict[str, Any]]) -> Path:
    reader = PdfReader(str(file_path))
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages):
        page_annotations = [a for a in annotations if a.get("page") == page_num]
        
        if page_annotations:
            page = _add_annotations_to_page(page, page_annotations)
        
        writer.add_page(page)

    output_path = get_output_path(output_id, "annotated.pdf")
    with open(str(output_path), "wb") as f:
        writer.write(f)
    
    return output_path


def _add_annotations_to_page(page, annotations: List[Dict[str, Any]]):
    page_width = float(page.mediabox.width)
    page_height = float(page.mediabox.height)
    
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    for annot in annotations:
        annot_type = annot.get("type", "text")
        
        if annot_type == "text":
            _draw_text_annotation(c, annot, page_width, page_height)
        elif annot_type == "highlight":
            _draw_highlight_annotation(c, annot, page_width, page_height)
        elif annot_type == "box":
            _draw_box_annotation(c, annot, page_width, page_height)
        elif annot_type == "line":
            _draw_line_annotation(c, annot, page_width, page_height)
    
    c.save()
    packet.seek(0)
    
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]
    overlay_page.mediabox = page.mediabox
    
    page.merge_page(overlay_page)
    return page


def _draw_text_annotation(c, annot: Dict[str, Any], page_width: float, page_height: float):
    x = float(annot.get("x", 0))
    y = float(annot.get("y", 0))
    text = annot.get("text", "")
    font_size = int(annot.get("fontSize", 12))
    color = annot.get("color", "#000000")
    
    y_adjusted = page_height - y
    
    c.setFont("Helvetica", font_size)
    c.setFillColor(_hex_to_rgb(color))
    c.drawString(x, y_adjusted, text)


def _draw_highlight_annotation(c, annot: Dict[str, Any], page_width: float, page_height: float):
    x = float(annot.get("x", 0))
    y = float(annot.get("y", 0))
    width = float(annot.get("width", 100))
    height = float(annot.get("height", 20))
    color = annot.get("color", "#FFFF00")
    opacity = float(annot.get("opacity", 0.3))
    
    y_adjusted = page_height - y - height
    
    c.setFillColor(_hex_to_rgb(color), alpha=opacity)
    c.rect(x, y_adjusted, width, height, fill=True, stroke=False)


def _draw_box_annotation(c, annot: Dict[str, Any], page_width: float, page_height: float):
    x = float(annot.get("x", 0))
    y = float(annot.get("y", 0))
    width = float(annot.get("width", 100))
    height = float(annot.get("height", 100))
    color = annot.get("color", "#000000")
    stroke_width = float(annot.get("strokeWidth", 2))
    
    y_adjusted = page_height - y - height
    
    c.setStrokeColor(_hex_to_rgb(color))
    c.setLineWidth(stroke_width)
    c.rect(x, y_adjusted, width, height, fill=False, stroke=True)


def _draw_line_annotation(c, annot: Dict[str, Any], page_width: float, page_height: float):
    x1 = float(annot.get("x1", 0))
    y1 = float(annot.get("y1", 0))
    x2 = float(annot.get("x2", 0))
    y2 = float(annot.get("y2", 0))
    color = annot.get("color", "#000000")
    stroke_width = float(annot.get("strokeWidth", 2))
    
    y1_adjusted = page_height - y1
    y2_adjusted = page_height - y2
    
    c.setStrokeColor(_hex_to_rgb(color))
    c.setLineWidth(stroke_width)
    c.line(x1, y1_adjusted, x2, y2_adjusted)


def _hex_to_rgb(hex_color: str) -> Color:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return Color(r, g, b)
    return Color(0, 0, 0)


def get_preset_annotations(preset: str) -> List[Dict[str, Any]]:
    if preset == "highlight":
        return [
            {
                "page": 0,
                "type": "highlight",
                "x": 50,
                "y": 100,
                "width": 200,
                "height": 30,
                "color": "#FFFF00",
                "opacity": 0.3,
            },
            {
                "page": 0,
                "type": "text",
                "x": 50,
                "y": 150,
                "text": "Highlighted for review",
                "fontSize": 10,
                "color": "#000000",
            },
        ]
    elif preset == "review":
        return [
            {
                "page": 0,
                "type": "box",
                "x": 50,
                "y": 100,
                "width": 200,
                "height": 100,
                "color": "#0066CC",
                "strokeWidth": 2,
            },
            {
                "page": 0,
                "type": "text",
                "x": 60,
                "y": 110,
                "text": "REVIEW",
                "fontSize": 12,
                "color": "#0066CC",
            },
        ]
    elif preset == "note":
        return [
            {
                "page": 0,
                "type": "text",
                "x": 50,
                "y": 100,
                "text": "Note: Please review this document carefully",
                "fontSize": 11,
                "color": "#CC0000",
            },
            {
                "page": 0,
                "type": "highlight",
                "x": 50,
                "y": 95,
                "width": 300,
                "height": 25,
                "color": "#FFCCCC",
                "opacity": 0.2,
            },
        ]
    return []
