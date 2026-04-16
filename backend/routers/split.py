import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.pdf_service import split_pdf

router = APIRouter(prefix="/api", tags=["split"])


@router.post("/split")
async def split(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    ranges: Optional[str] = Form(None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)
    range_list = [r.strip() for r in ranges.split(",") if r.strip()] if ranges else None

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(split_pdf, dec_path, file_id, range_list)
        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)
        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(path=str(download_path), media_type="application/pdf", filename=f"{stem}_split.pdf")
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Split failed: {str(e)}")
