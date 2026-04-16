import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List

from services.file_service import (
    generate_file_id, save_upload, MAX_FILE_SIZE,
    decrypt_to_temp, encrypt_output, decrypt_for_download, cleanup_temp_files,
)
from services.pdf_service import merge_pdfs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["merge"])


@router.post("/merge")
async def merge(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files are required.")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 PDF files can be merged at a time.")

    file_id = generate_file_id()
    logger.info(f"Starting merge operation for file_id: {file_id}")
    encrypted_paths = []
    original_names = []

    try:
        for f in files:
            if not f.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"File '{f.filename}' is not a PDF.")
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail=f"File '{f.filename}' exceeds 100MB limit.")
            original_names.append(f.filename)
            path = await save_upload(content, file_id, f.filename)
            encrypted_paths.append(path)
            logger.info(f"Saved encrypted file: {path}")

        logger.info(f"Starting PDF merge with {len(encrypted_paths)} files")
        decrypted_paths = [decrypt_to_temp(p, file_id) for p in encrypted_paths]
        logger.info(f"Decrypted {len(decrypted_paths)} files to temp")
        
        output_path = await asyncio.to_thread(merge_pdfs, decrypted_paths, file_id)
        logger.info(f"PDF merge completed, output saved to: {output_path}")
        
        encrypt_output(output_path, file_id)
        logger.info(f"Output file encrypted")
        
        download_path = decrypt_for_download(output_path, file_id)
        logger.info(f"Created download file: {download_path}")
        
        stem = Path(original_names[0]).stem
        background_tasks.add_task(cleanup_temp_files, file_id)
        logger.info(f"Merge successful for file_id: {file_id}")
        return FileResponse(path=str(download_path), media_type="application/pdf", filename=f"{stem}_merged.pdf")
    except HTTPException:
        cleanup_temp_files(file_id)
        raise
    except Exception as e:
        logger.error(f"Merge failed for file_id {file_id}: {str(e)}", exc_info=True)
        cleanup_temp_files(file_id)
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")
