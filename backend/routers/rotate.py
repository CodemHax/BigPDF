import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.pdf_service import rotate_pdf

router = APIRouter(prefix="/api", tags=["rotate"])


@router.post("/rotate")
async def rotate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rotation: int = Form(90),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    if rotation not in (90, 180, 270):
        raise HTTPException(status_code=400, detail="Rotation must be 90, 180, or 270.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(rotate_pdf, dec_path, file_id, rotation=rotation)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_rotated.pdf",
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Rotation failed: {str(e)}")
