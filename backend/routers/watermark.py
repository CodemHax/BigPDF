import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.pdf_service import watermark_pdf

router = APIRouter(prefix="/api", tags=["watermark"])

@router.post("/watermark")
async def watermark(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    text: str = Form(...),
    opacity: float = Form(0.3),
    font_size: int = Form(50),
    rotation: int = Form(45),
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
        output_path = await asyncio.to_thread(
            watermark_pdf, dec_path, file_id,
            text=text, opacity=opacity, font_size=font_size, rotation=rotation,
        )
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_watermarked.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Watermark failed: {str(e)}")
