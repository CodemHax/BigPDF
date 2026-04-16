import asyncio
import json
import base64
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from PIL import Image
import fitz

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.annotate_service import annotate_pdf, get_preset_annotations

router = APIRouter(prefix="/api", tags=["annotate"])


@router.post("/annotate")
async def annotate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    annotation_preset: str = Form(None),
    annotation_image: str = Form(None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        
        if annotation_image:
            output_path = await asyncio.to_thread(
                overlay_annotation_image, dec_path, annotation_image
            )
        elif annotation_preset and annotation_preset in ("highlight", "review", "note"):
            annot_list = get_preset_annotations(annotation_preset)
            output_path = await asyncio.to_thread(annotate_pdf, dec_path, file_id, annot_list)
        else:
            raise HTTPException(status_code=400, detail="No annotation data provided.")
        
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_annotated.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Annotation failed: {str(e)}")


def overlay_annotation_image(pdf_path: str, annotation_image_data: str):
    try:
        if annotation_image_data.startswith("data:image"):
            annotation_image_data = annotation_image_data.split(",", 1)[1]
        
        image_bytes = base64.b64decode(annotation_image_data)
        annotation_img = Image.open(BytesIO(image_bytes))
        
        pdf_doc = fitz.open(pdf_path)
        page = pdf_doc[0]
        
        mat = fitz.Matrix(1, 1)
        pix = page.get_pixmap(matrix=mat)
        
        pdf_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        overlay_img = annotation_img.convert("RGBA")
        if overlay_img.size != pdf_img.size:
            overlay_img = overlay_img.resize(pdf_img.size, Image.Resampling.LANCZOS)
        
        pdf_img_rgba = pdf_img.convert("RGBA")
        pdf_img_rgba = Image.alpha_composite(pdf_img_rgba, overlay_img)
        
        temp_img_path = pdf_path.replace(".pdf", "_annotated_temp.png")
        pdf_img_rgba.save(temp_img_path, "PNG")
        
        output_path = pdf_path.replace(".pdf", "_with_annotations.pdf")
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import landscape
        
        page_width = pix.width
        page_height = pix.height
        
        c = rl_canvas.Canvas(output_path, pagesize=(page_width, page_height))
        c.drawImage(temp_img_path, 0, 0, width=page_width, height=page_height)
        c.save()
        
        Path(temp_img_path).unlink()
        pdf_doc.close()
        
        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to overlay annotation image: {str(e)}")
