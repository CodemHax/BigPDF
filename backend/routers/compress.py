import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.pdf_service import compress_pdf

router = APIRouter(prefix="/api", tags=["compress"])


@router.post("/compress")
async def compress(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: str = Form("medium"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    if quality not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="Quality must be 'low', 'medium', or 'high'.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 100MB limit.")

    file_id = generate_file_id()
    enc_path = await save_upload(content, file_id, file.filename)

    try:
        dec_path = decrypt_to_temp(enc_path, file_id)
        output_path = await asyncio.to_thread(compress_pdf, dec_path, file_id, quality)
        original_size = len(content)
        compressed_size = output_path.stat().st_size

        encrypt_output(output_path, file_id)
        download_path = decrypt_for_download(output_path, file_id)

        reduction = max(0, round((1 - compressed_size / original_size) * 100, 1))
        stem = Path(file.filename).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        return FileResponse(
            path=str(download_path),
            media_type="application/pdf",
            filename=f"{stem}_compressed.pdf",
            headers={
                "X-Original-Size": str(original_size),
                "X-Compressed-Size": str(compressed_size),
                "X-Reduction-Percent": str(reduction),
            },
        )
    except Exception as e:
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Compression failed: {str(e)}")
